"""No model calls: validate adapter exposure and result handling with a fake CLI."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

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
        binary.write_text('#!/usr/bin/env python3\nimport json,sys\nfrom pathlib import Path\nif "--version" in sys.argv:\n print("fake-version"); sys.exit(0)\nassert "--restricted" in sys.argv and "--safe-mode" in sys.argv\nassert "Bash" not in sys.argv\nassert "bypassPermissions" not in sys.argv\nPath("artifact.txt").write_text("done")\nprint(' + repr(json.dumps(response)) + ')\nsys.exit(' + str(exit_code) + ')\n')
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
        self.assertIsNone(metrics['skills_loaded'])
        self.assertIsNone(metrics['cost_usd'])
        self.assertTrue((self.root / 'work' / 'artifact.txt').exists())
        self.assertTrue((self.root / 'effective-prompt.txt').exists())

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
