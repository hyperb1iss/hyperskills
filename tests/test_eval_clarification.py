"""Question necessity is independent of export correctness and wording."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'evals/cases/clarification'

class ClarificationTests(unittest.TestCase):
    def oracle(self, workspace, variant, turn=0):
        request = workspace.parent / 'request.json'
        request.write_text(json.dumps({'workspace': str(workspace), 'task': f'clarification-{variant}', 'turn': turn}))
        subprocess.run([sys.executable, str(ROOT / 'oracle_adapter.py'), str(request)], check=True, capture_output=True)

    def grade(self, workspace, variant, turns):
        (workspace.parent / 'interactions.json').write_text(json.dumps({'turns': turns, 'exhausted': False}))
        result = subprocess.run([sys.executable, str(ROOT / 'grade.py'), variant, str(workspace)], env={**os.environ, 'EVAL_INTERACTION_LOG': str(workspace.parent / 'interactions.json')}, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def test_three_variants(self):
        for variant in ('missing', 'stated', 'discoverable'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / 'workspace'
                shutil.copytree(ROOT / variant / 'fixture', workspace)
                initial = (workspace / 'exporter.py').read_bytes()
                self.oracle(workspace, variant)
                turns = []
                if variant == 'missing':
                    self.assertEqual((workspace / 'exporter.py').read_bytes(), initial)
                    self.assertTrue((workspace / 'clarification.json').exists())
                    (workspace / 'clarification.json').unlink()
                    turns = [{'question': 'JSON or CSV?', 'reply': 'JSON.', 'workspace_changes': []}]
                    self.oracle(workspace, variant, turn=1)
                self.assertTrue(self.grade(workspace, variant, turns)['passed'])
                incorrect_turns = [] if variant == 'missing' else [{'question': 'Tell me the format.', 'reply': 'JSON.', 'workspace_changes': []}]
                result = self.grade(workspace, variant, incorrect_turns)
                self.assertTrue(result['checks']['outcome'])
                self.assertFalse(result['checks']['question_policy'])
                self.assertFalse(result['passed'])
                (workspace / 'exporter.py').write_text('def export_contacts(contacts): return "[]"\n')
                result = self.grade(workspace, variant, turns)
                self.assertFalse(result['checks']['outcome'])
                self.assertTrue(result['checks']['question_policy'])

    def test_premature_implementation_fails_independently(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / 'workspace'
            shutil.copytree(ROOT / 'missing/fixture', workspace)
            self.oracle(workspace, 'missing', turn=1)
            result = self.grade(workspace, 'missing', [{
                'question': 'Which format?', 'reply': 'JSON',
                'workspace_changes': ['exporter.py'],
            }])
            self.assertTrue(result['checks']['outcome'])
            self.assertTrue(result['checks']['question_policy'])
            self.assertFalse(result['checks']['asked_before_implementation'])
            self.assertFalse(result['passed'])
            missing_receipt = self.grade(workspace, 'missing', [{
                'question': 'Which format?', 'reply': 'JSON',
            }])
            self.assertFalse(missing_receipt['checks']['interaction_complete'])
            self.assertFalse(missing_receipt['passed'])

    def test_question_wording_not_graded(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / 'workspace'
            shutil.copytree(ROOT / 'missing/fixture', workspace)
            self.oracle(workspace, 'missing', turn=1)
            for question in ('Which format?', 'Please choose the team export representation.'):
                result = self.grade(workspace, 'missing', [{'question': question, 'reply': 'JSON', 'workspace_changes': []}])
                self.assertTrue(result['passed'])

if __name__ == '__main__':
    unittest.main()
