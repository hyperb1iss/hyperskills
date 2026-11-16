"""Exercise the host conversation loop independently of any model provider."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location('skill_eval', ROOT / 'scripts/skill_eval.py')
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class InteractionTests(unittest.TestCase):
    def test_resumed_usage_and_skill_receipts_preserve_session_identity(self):
        for mismatch in (False, True):
            with self.subTest(mismatch=mismatch), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                data = MOD.suite(ROOT / 'evals/clarification.json')
                data['tasks'] = [task for task in data['tasks'] if task['id'] == 'clarification-missing']
                MOD.write(base / 'suite.json', data)
                MOD.plan(base / 'suite.json', base / 'plan.json', repeats=1)
                invoke = MOD.invoke

                def instrument(argv, cwd, env, prefix):
                    result = invoke(argv, cwd, env, prefix)
                    if prefix.name == 'adapter':
                        request = MOD.read(argv[-1])
                        self.assertEqual(env['CLAUDE_CONFIG_DIR'], str(Path(request['home']) / '.claude'))
                        turn = request['turn']
                        MOD.write(request['metrics'], {
                            'cost_usd': 0.2 if turn == 0 else 0.4,
                            'cost_scope': 'session_cumulative',
                            'session_id': 'different' if mismatch and turn else request['session_id'],
                            'tokens': 4 if turn == 0 else 6, 'tokens_scope': 'turn',
                            'skills_loaded': ['implement'] if turn == 0 else [],
                            'skills_preloaded': ['plan'] if turn == 0 else [],
                        })
                        if mismatch and turn:
                            result['exit_code'] = 1
                    return result

                with patch.object(MOD, 'invoke', side_effect=instrument), patch.dict(MOD.os.environ, {'CLAUDE_CONFIG_DIR': '/ambient/claude'}):
                    MOD.run(base / 'plan.json', base / 'run')
                for trial in MOD.read(base / 'plan.json')['trials']:
                    result = MOD.read(base / 'run' / trial['id'] / 'result.json')
                    self.assertEqual(result['cost_usd'], None if mismatch else 0.4)
                    self.assertEqual(result['tokens'], 10)
                    self.assertEqual(result['status'], 'adapter_error' if mismatch else 'valid')
                    self.assertEqual(result['skills_loaded'], ['implement'])
                    self.assertEqual(result['skills_preloaded'], ['plan'])

    def test_real_fixture_loop_and_hidden_response(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            MOD.plan(ROOT / 'evals/clarification.json', base / 'plan.json', repeats=1)
            MOD.run(base / 'plan.json', base / 'run')
            for trial in MOD.read(base / 'plan.json')['trials']:
                directory = base / 'run' / trial['id']
                result = MOD.read(directory / 'result.json')
                self.assertTrue(result['passed'], result)
                initial = MOD.read(directory / 'request.json')
                self.assertNotIn('response', initial)
                self.assertNotIn('interaction', initial)
                self.assertNotIn('replies.json', json.dumps(initial))
                log = MOD.read(directory / 'interactions.json')
                if trial['task'] == 'clarification-missing':
                    self.assertEqual(len(result['attempts']), 2)
                    self.assertEqual(log['turns'][0]['workspace_changes'], [])
                    followup = MOD.read(directory / 'turn-001/request.json')
                    self.assertEqual(initial['session_id'], followup['session_id'])
                    self.assertEqual(initial['home'], followup['home'])
                    self.assertEqual(Path(followup['prompt']).read_text(), 'The team prefers JSON.')
                else:
                    self.assertEqual(log['turns'], [])

    def test_repeated_questions_exhaust_budget_without_becoming_infra_error(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            data = MOD.suite(ROOT / 'evals/clarification.json')
            adapter = base / 'adapter.py'
            adapter.write_text('import json,sys\nfrom pathlib import Path\nr=json.load(open(sys.argv[1]))\nPath(r["workspace"],"clarification.json").write_text(json.dumps({"question":"Again?"}))\n')
            data['tasks'] = data['tasks'][:1]
            data['configurations'][0]['adapter'] = ['python3', str(adapter)]
            MOD.write(base / 'suite.json', data)
            MOD.plan(base / 'suite.json', base / 'plan.json', repeats=1)
            MOD.run(base / 'plan.json', base / 'run')
            for trial in MOD.read(base / 'plan.json')['trials']:
                result = MOD.read(base / 'run' / trial['id'] / 'result.json')
                self.assertEqual(result['status'], 'valid')
                self.assertFalse(result['passed'])
                self.assertEqual(len(result['attempts']), 3)
                self.assertTrue(MOD.read(base / 'run' / trial['id'] / 'interactions.json')['exhausted'])


if __name__ == '__main__':
    unittest.main()
