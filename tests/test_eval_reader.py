"""No model calls: the reader stage runs against a fake CLI, and the cases are checked for integrity."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'evals' / 'cases' / 'prose' / 'reader'
CASE_IDS = sorted(p.name for p in CASES.iterdir() if (p / 'prompt.md').is_file())
SPEC = importlib.util.spec_from_file_location('eval_reader', ROOT / 'scripts' / 'eval_reader.py')
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

MODEL = 'reader-model'
VERSION = 'fake-version'
QUESTIONS = {'version': 1, 'questions': [
    {'id': 'a', 'question': 'Which colour is the queue?', 'options': ['red', 'blue', 'green', 'grey', MOD.NOT_STATED], 'answer': 1},
    {'id': 'b', 'question': 'Who approves?', 'options': ['ops', 'finance', 'legal', 'support', MOD.NOT_STATED], 'answer': 2},
    {'id': 'c', 'question': 'When?', 'options': ['Monday', 'Tuesday', 'Friday', 'Sunday', MOD.NOT_STATED], 'answer': 0},
]}
FAKE = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
LOG = Path({log!r})
RESPONSES = {responses!r}
if '--version' in sys.argv:
    print({version!r})
    sys.exit(0)
prompt = sys.stdin.read()
counter = LOG.with_suffix('.count')
index = int(counter.read_text()) if counter.exists() else 0
counter.write_text(str(index + 1))
with LOG.open('a') as log:
    log.write(json.dumps({{'argv': sys.argv, 'prompt': prompt, 'cwd_entries': os.listdir('.'),
                          'home': os.environ.get('HOME'), 'config': os.environ.get('CLAUDE_CONFIG_DIR')}}) + '\\n')
response = RESPONSES[min(index, len(RESPONSES) - 1)]
print(response if isinstance(response, str) else json.dumps(response))
'''


def event(result, model=MODEL, cost=0.01):
    return {'type': 'result', 'is_error': False, 'result': result, 'modelUsage': {model: {}}, 'total_cost_usd': cost}


class ReaderStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.log = self.root / 'calls.jsonl'
        self.questions = self.root / 'key' / 'questions.json'
        self.questions.parent.mkdir()
        self.questions.write_text(json.dumps(QUESTIONS))
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        self.text = self.workspace / 'edited.md'
        self.text.write_text('The retry queue is blue. Legal approves the purge on Monday.\n')
        (self.workspace / 'notes.md').write_text('NOTES-SENTINEL-41: the queue was renamed twice.\n')

    def fake(self, responses):
        binary = self.root / 'claude'
        binary.write_text(FAKE.format(log=str(self.log), responses=responses, version=VERSION))
        binary.chmod(0o755)
        return str(binary)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def ask(self, binary, repeats, version=VERSION, output='out.json'):
        return MOD.ask(self.text, self.questions, MODEL, version, repeats, binary, self.root / output, jobs=1)

    def test_scores_answers_against_key(self):
        binary = self.fake([event('{"a": 1, "b": 0, "c": 0}'), event('```json\n{"a": 1, "b": 2, "c": 0}\n```', cost=0.02)])
        result = self.ask(binary, 2)
        self.assertEqual((result['valid_repeats'], result['invalid_repeats']), (2, 0))
        self.assertAlmostEqual(result['accuracy'], (2 / 3 + 1) / 2)
        self.assertEqual(result['per_question'], {'a': 1.0, 'b': 0.5, 'c': 1.0})
        self.assertEqual(result['repeats'][0]['correct'], {'a': True, 'b': False, 'c': True})
        self.assertAlmostEqual(result['cost_usd'], 0.03)
        self.assertEqual(result['served_models'], [MODEL])
        self.assertEqual((result['model'], result['cli_version']), (MODEL, VERSION))
        self.assertEqual(json.loads((self.root / 'out.json').read_text())['accuracy'], result['accuracy'])

    def test_unusable_repeats_are_invalid_not_wrong(self):
        binary = self.fake([
            event('{"a": 1, "b": 2, "c": 4}'),
            event('I would pick option 1 for a.'),
            event('{"a": 1}'),
            event('{"a": 1, "b": 2, "c": 9}'),
            event('{"a": 1, "b": 2, "c": 0}', model='another-model'),
            'not json at all',
        ])
        result = self.ask(binary, 6)
        self.assertEqual((result['valid_repeats'], result['invalid_repeats']), (1, 5))
        self.assertAlmostEqual(result['accuracy'], 2 / 3)
        self.assertAlmostEqual(result['not_stated_rate'], 1 / 3)
        self.assertTrue(all(r['error'] for r in result['repeats'][1:]))
        self.assertIsNone(result['cost_usd'])
        self.assertEqual(result['cost_missing_repeats'], 1)

    def test_version_mismatch_refuses_before_any_reader_call(self):
        binary = self.fake([event('{"a": 1, "b": 2, "c": 0}')])
        with self.assertRaisesRegex(ValueError, 'CLI version mismatch'):
            self.ask(binary, 1, version='another-version')
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.root / 'out.json').exists())

    def test_existing_output_is_never_overwritten(self):
        binary = self.fake([event('{"a": 1, "b": 2, "c": 0}')])
        (self.root / 'out.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.ask(binary, 1)
        self.assertEqual(self.calls(), [])

    def test_reader_sees_only_text_and_questions(self):
        binary = self.fake([event('{"a": 1, "b": 2, "c": 0}')])
        self.ask(binary, 1)
        [call] = self.calls()
        prompt, argv = call['prompt'], call['argv']
        self.assertIn('The retry queue is blue.', prompt)
        self.assertIn('Who approves?', prompt)
        self.assertIn('  4. ' + MOD.NOT_STATED, prompt)
        system = argv[argv.index('--system-prompt') + 1]
        for leaked in (str(self.root), 'edited.md', 'notes.md', 'questions.json', 'NOTES-SENTINEL-41', '"answer"'):
            self.assertNotIn(leaked, prompt)
            self.assertNotIn(leaked, system)
        self.assertEqual(argv[argv.index('--tools') + 1], '')
        for flag in ('--safe-mode', '--restricted', '--strict-mcp-config', '--no-session-persistence', '--disable-slash-commands'):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index('--model') + 1], MODEL)
        self.assertEqual(call['cwd_entries'], [])
        self.assertNotEqual(call['home'], os.environ.get('HOME'))
        self.assertTrue(call['config'].startswith(call['home']))
        self.assertFalse(Path(call['home']).exists())

    def test_score_walks_run_directory(self):
        run = self.root / 'run'
        cases = self.root / 'cases'
        (cases / 'demo').mkdir(parents=True)
        shutil.copyfile(self.questions, cases / 'demo' / 'questions.json')
        trials = [
            ('000000', 'prose-reader-demo', 'explicit', 0, 'valid', 'Explicit edit: the queue is blue.'),
            ('000001', 'prose-reader-demo', 'baseline', 0, 'valid', None),
            ('000002', 'prose-reader-demo', 'baseline', 1, 'valid', 'Baseline edit: the queue is blue.'),
            ('000003', 'prose-reader-demo', 'discovery', 0, 'adapter_error', 'Half-written edit.'),
            ('000004', 'screen-silent-drop', 'explicit', 0, 'valid', 'Not a prose-reader task.'),
            ('000005', 'prose-reader-demo', 'explicit', 1, None, None),
        ]
        plan = {'trials': [{'id': t[0], 'task': t[1], 'arm': t[2], 'repeat': t[3], 'configuration': 'cfg'} for t in trials]}
        run.mkdir()
        (run / 'plan.json').write_text(json.dumps(plan))
        for trial_id, task, arm, repeat, status, edited in trials:
            if status is None:
                continue
            workspace = run / trial_id / 'workspace'
            workspace.mkdir(parents=True)
            (run / trial_id / 'result.json').write_text(json.dumps({'status': status, 'passed': edited is not None}))
            if edited:
                (workspace / 'edited.md').write_text(edited)
        binary = self.fake([event('{"a": 1, "b": 2, "c": 0}')])
        report = MOD.score(run, cases, MODEL, VERSION, 2, binary, self.root / 'score.json', jobs=2)
        self.assertEqual(sorted(row['trial'] for row in report['rows']), ['000000', '000002'])
        self.assertTrue(all(row['accuracy'] == 1.0 and row['invalid_repeats'] == 0 for row in report['rows']))
        self.assertEqual(report['skipped_counts'], {'no_edited_md': 1, 'trial_not_valid': 2})
        means = {row['arm']: row for row in report['means']}
        self.assertEqual(set(means), {'baseline', 'explicit', 'discovery'})
        self.assertEqual((means['baseline']['trials_scored'], means['baseline']['skipped_no_edited_md']), (1, 1))
        self.assertEqual((means['explicit']['mean_accuracy'], means['explicit']['skipped_trial_not_valid']), (1.0, 1))
        self.assertIsNone(means['discovery']['mean_accuracy'])
        prompts = [call['prompt'] for call in self.calls()]
        self.assertEqual(len(prompts), 4)
        self.assertEqual(sum('Explicit edit' in p for p in prompts), 2)
        self.assertFalse(any('Half-written' in p or 'Not a prose-reader' in p for p in prompts))
        self.assertAlmostEqual(report['cost_usd'], 0.04)
        self.assertIn('demo', report['questions_sha256'])


def grade(case, workspace):
    done = subprocess.run([sys.executable, str(CASES / 'grade.py'), case, str(workspace)], capture_output=True, text=True, check=True)
    return json.loads(done.stdout)


class ReaderCaseTests(unittest.TestCase):
    def test_four_cases_with_answers_outside_the_workspace(self):
        self.assertEqual(len(CASE_IDS), 4)
        for case in CASE_IDS:
            with self.subTest(case=case):
                directory = CASES / case
                self.assertEqual(sorted(p.name for p in (directory / 'fixture').iterdir()), ['draft.md', 'notes.md'])
                for name in ('questions.json', 'protected.json', 'oracle/edited.md'):
                    self.assertTrue((directory / name).is_file(), name)

    def test_keys_index_substantive_options(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                questions = MOD.load_questions(CASES / case / 'questions.json')
                self.assertTrue(6 <= len(questions) <= 8)
                for question in questions:
                    self.assertEqual(len(question['options']), 5)
                    self.assertEqual(question['options'][-1], MOD.NOT_STATED)
                    self.assertIn(question['answer'], range(4))
                    self.assertEqual(len(set(question['options'])), 5)

    def test_word_budgets(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                fixture = CASES / case / 'fixture'
                self.assertTrue(300 <= len((fixture / 'notes.md').read_text().split()) <= 600)
                self.assertTrue(150 <= len((fixture / 'draft.md').read_text().split()) <= 350)

    def test_case_text_is_plain_ascii(self):
        for path in sorted(CASES.rglob('*')):
            if path.is_file() and path.suffix in ('.md', '.json', '.py'):
                with self.subTest(path=path.relative_to(CASES)):
                    self.assertTrue(path.read_bytes().isascii())

    def test_prompts_name_the_files_and_not_the_measure(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                prompt = (CASES / case / 'prompt.md').read_text()
                for name in ('draft.md', 'edited.md', 'notes.md'):
                    self.assertIn(name, prompt)
                self.assertNotIn('question', prompt.lower())

    def test_untold_prompts_do_not_reveal_the_reader_gap(self):
        giveaways = ('notes', 'log', 'context', 'question', 'define', 'expand', 'self-contained',
                     'has not', "hasn't", 'not seen', 'not followed', 'unfamiliar', 'every fact', 'detail')
        texts = set()
        for case in CASE_IDS:
            with self.subTest(case=case):
                prompt = (CASES / case / 'prompt-untold.md').read_text()
                texts.add(prompt)
                for name in ('draft.md', 'edited.md'):
                    self.assertIn(name, prompt)
                self.assertEqual([word for word in giveaways if word in prompt.lower()], [])
                self.assertTrue(2 <= prompt.count('. ') + prompt.count('? ') + 1 <= 3)
        self.assertEqual(len(texts), len(CASE_IDS))

    def test_protected_strings_survive_in_draft_and_oracle(self):
        for case in CASE_IDS:
            with self.subTest(case=case):
                protected = json.loads((CASES / case / 'protected.json').read_text())
                self.assertTrue(protected)
                for name in ('fixture/draft.md', 'oracle/edited.md'):
                    text = (CASES / case / name).read_text()
                    self.assertEqual([t for t in protected if t not in text], [])

    def test_grader_passes_oracle_and_fails_unedited_draft(self):
        for case in CASE_IDS:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / 'workspace'
                shutil.copytree(CASES / case / 'fixture', workspace)
                self.assertFalse(grade(case, workspace)['passed'])
                shutil.copyfile(workspace / 'draft.md', workspace / 'edited.md')
                unedited = grade(case, workspace)
                self.assertFalse(unedited['passed'])
                self.assertFalse(unedited['checks']['edited_differs'])
                shutil.copyfile(CASES / case / 'oracle' / 'edited.md', workspace / 'edited.md')
                oracle = grade(case, workspace)
                self.assertTrue(oracle['passed'], oracle)
                self.assertTrue(oracle['requires_human_review'])
                self.assertEqual(set(oracle['metrics']), {'draft', 'edited', 'word_ratio'})
                self.assertGreater(oracle['metrics']['edited']['words'], 0)
                (workspace / 'notes.md').write_text('rewritten\n')
                self.assertFalse(grade(case, workspace)['passed'])

    def test_grader_fails_a_dropped_protected_string(self):
        case = CASE_IDS[0]
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / 'workspace'
            shutil.copytree(CASES / case / 'fixture', workspace)
            token = json.loads((CASES / case / 'protected.json').read_text())[0]
            oracle = (CASES / case / 'oracle' / 'edited.md').read_text()
            (workspace / 'edited.md').write_text(oracle.replace(token, '[redacted]'))
            result = grade(case, workspace)
            self.assertFalse(result['passed'])
            self.assertFalse(result['checks'][f'protected:{token}'])


if __name__ == '__main__':
    unittest.main()
