"""No model calls: validate adapter exposure and result handling with a fake CLI."""
import importlib.util
import json
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('eval_claude', Path(__file__).parents[1] / 'scripts/eval_claude.py')
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ClaudeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'work').mkdir()
        (self.root / 'skills' / 'example').mkdir(parents=True)
        (self.root / 'skills' / 'example' / 'SKILL.md').write_text('---\nname: example\ndescription: A useful skill\n---\nSECRET BODY')
        (self.root / 'prompt').write_text('TASK')
        self.request = {'arm': 'baseline', 'prompt': str(self.root / 'prompt'), 'skills': str(self.root / 'skills'), 'workspace': str(self.root / 'work'), 'metrics': str(self.root / 'metrics.json'), 'configuration': {'model': 'pinned-model', 'settings': {'claude_version': 'fake-version', 'expected_served_models': ['pinned-model']}}}

    def test_exposure(self):
        self.assertNotIn('example', MOD.build_prompt(self.request))
        self.request['arm'] = 'discovery'
        self.assertIn('A useful skill', MOD.build_prompt(self.request))
        self.assertNotIn('SECRET BODY', MOD.build_prompt(self.request))
        self.request['arm'] = 'explicit'
        self.assertIn('SECRET BODY', MOD.build_prompt(self.request))

    def fake(self, response, exit_code=0):
        binary = self.root / 'claude'
        binary.write_text('#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\nif "--version" in sys.argv:\n print("fake-version"); sys.exit(0)\nassert "--restricted" in sys.argv and "--safe-mode" in sys.argv\nassert "Bash" not in sys.argv\nassert "bypassPermissions" not in sys.argv\nPath("argv.json").write_text(json.dumps(sys.argv))\nPath("artifact.txt").write_text("done")\nprint(' + repr('\n'.join(json.dumps(event) for event in response) if isinstance(response, list) else json.dumps(response)) + ')\nsys.exit(' + str(exit_code) + ')\n')
        binary.chmod(0o755)
        self.request['configuration']['settings']['claude_bin'] = str(binary)
        path = self.root / 'request.json'
        path.write_text(json.dumps(self.request))
        return path

    def test_success_records_missing_metrics_as_unknown(self):
        path = self.fake({'type': 'result', 'is_error': False, 'result': 'done', 'modelUsage': {'pinned-model': {}}})
        self.assertEqual(MOD.run(path), 0)
        metrics = json.loads((self.root / 'metrics.json').read_text())
        self.assertIsNone(metrics['tokens'])
        self.assertEqual(metrics['skills_loaded'], [])
        self.assertIsNone(metrics['cost_usd'])
        self.assertTrue((self.root / 'work' / 'artifact.txt').exists())
        self.assertTrue((self.root / 'effective-prompt.txt').exists())

    def test_stream_records_successful_skill_read_and_hides_thinking(self):
        self.request['arm'] = 'discovery'
        path = str(self.root / 'skills' / 'example' / 'SKILL.md')
        events = [
            {'type': 'assistant', 'message': {'content': [{'type': 'thinking', 'thinking': 'PRIVATE'}, {'type': 'tool_use', 'id': 'r', 'name': 'Read', 'input': {'file_path': path}}]}},
            {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 'r', 'content': 'skill text'}]}},
            {'type': 'result', 'is_error': False, 'result': 'done', 'modelUsage': {'pinned-model': {}}}
        ]
        self.assertEqual(MOD.run(self.fake(events)), 0)
        self.assertEqual(json.loads((self.root / 'metrics.json').read_text())['skills_loaded'], ['example'])
        self.assertNotIn('PRIVATE', (self.root / 'actions-0.json').read_text())
        self.assertIn('PRIVATE', (self.root / 'claude-events-0.jsonl').read_text())

    def test_interaction_resumes_same_session_and_sends_only_reply(self):
        self.request.update(interactive=True, session_id='a496e781-2a62-4e1e-9c4c-657d78d67c3e', turn=0)
        response = {'type': 'result', 'is_error': False, 'result': 'done', 'modelUsage': {'pinned-model': {}}, 'session_id': self.request['session_id']}
        MOD.run(self.fake(response))
        argv = json.loads((self.root / 'work' / 'argv.json').read_text())
        self.assertIn('--session-id', argv)
        self.assertNotIn('--no-session-persistence', argv)
        self.request['turn'] = 1
        (self.root / 'prompt').write_text('Keep the first occurrence.')
        MOD.run(self.fake(response))
        argv = json.loads((self.root / 'work' / 'argv.json').read_text())
        self.assertIn('--resume', argv)
        self.assertEqual((self.root / 'effective-prompt-1.txt').read_text(), 'Keep the first occurrence.')
        self.assertTrue((self.root / 'claude-events-0.jsonl').exists())
        self.assertTrue((self.root / 'claude-events-1.jsonl').exists())

    def test_shell_setting_cannot_enable_local_shell(self):
        self.request['configuration']['settings']['profile'] = 'shell'
        with self.assertRaisesRegex(ValueError, 'Docker transport'):
            MOD.run(self.fake({}))
        self.assertFalse((self.root / 'work' / 'artifact.txt').exists())

    def test_session_mismatch_preserves_observed_identity_and_cost(self):
        self.request.update(interactive=True, session_id='a496e781-2a62-4e1e-9c4c-657d78d67c3e', turn=1)
        response = {'type': 'result', 'is_error': False, 'result': 'done',
                    'modelUsage': {'pinned-model': {}}, 'session_id': 'unexpected-session',
                    'total_cost_usd': 0.4}
        with self.assertRaisesRegex(ValueError, 'session identity'):
            MOD.run(self.fake(response))
        metrics = json.loads((self.root / 'metrics.json').read_text())
        self.assertEqual(metrics['session_id'], 'unexpected-session')
        self.assertEqual(metrics['cost_usd'], 0.4)

    def test_container_shell_rejects_missing_marker(self):
        with patch.object(MOD.Path, 'is_file', return_value=False):
            with self.assertRaisesRegex(ValueError, 'Docker transport'):
                MOD.verify_container(self.request)

    def test_version_mismatch_prevents_provider_invocation(self):
        self.request['configuration']['settings']['claude_version'] = 'another-version'
        with self.assertRaisesRegex(ValueError, 'CLI version mismatch'):
            MOD.run(self.fake({'type': 'result', 'is_error': False}))
        self.assertFalse((self.root / 'work' / 'artifact.txt').exists())
        self.assertEqual(json.loads((self.root / 'metrics.json').read_text())['cli_version'], 'fake-version')

    def test_served_model_mismatch_preserves_spend(self):
        with self.assertRaisesRegex(ValueError, 'served model'):
            MOD.run(self.fake({'type': 'result', 'is_error': False, 'modelUsage': {'different-model': {}}, 'total_cost_usd': 0.4}))
        metrics = json.loads((self.root / 'metrics.json').read_text())
        self.assertEqual(metrics['cost_usd'], 0.4)
        self.assertEqual(metrics['served_models'], ['different-model'])

    def test_nonzero_exit_preserves_returned_spend(self):
        path = self.fake({'type': 'result', 'is_error': True, 'total_cost_usd': 0.5}, exit_code=2)
        self.assertEqual(MOD.run(path), 2)
        self.assertEqual(json.loads((self.root / 'metrics.json').read_text())['cost_usd'], 0.5)

    def test_error_event_and_denial_are_not_success(self):
        for response in [{'type': 'result', 'is_error': True}, {'type': 'result', 'is_error': False, 'permission_denials': [{'tool': 'Write'}]}]:
            with self.assertRaises(ValueError):
                MOD.run(self.fake({**response, 'total_cost_usd': 0.25, 'modelUsage': {'pinned-model': {}}}))
            metrics = json.loads((self.root / 'metrics.json').read_text())
            self.assertEqual(metrics['cost_usd'], 0.25)
            self.assertEqual(metrics['served_models'], ['pinned-model'])


if __name__ == '__main__':
    unittest.main()
