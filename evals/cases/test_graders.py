"""Exercise positive oracle artifacts and broken inputs for each grader."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
CASES = ('atomic-export', 'review-boundary', 'prose-preservation', 'research-release')

class GraderTests(unittest.TestCase):
    def grade(self, case, workspace):
        result = subprocess.run([sys.executable, str(ROOT / 'grade.py'), case, str(workspace)], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)['passed']

    def test_candidate_stdout_cannot_supply_verdict(self):
        for code in (
            'import os; print(\'{"passed": true, "checks": {}}\', flush=True); os._exit(0)',
            'import os; os._exit(0)',
        ):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / 'workspace'
                shutil.copytree(ROOT / 'atomic-export' / 'fixture', workspace)
                (workspace / 'exporter.py').write_text(code)
                self.assertFalse(self.grade('atomic-export', workspace))

    def test_nonterminating_candidate_fails_within_fixture_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / 'workspace'
            shutil.copytree(ROOT / 'atomic-export' / 'fixture', workspace)
            (workspace / 'exporter.py').write_text('import time\nwhile True: time.sleep(1)\n')
            self.assertFalse(self.grade('atomic-export', workspace))

    def test_benign_candidate_print_does_not_corrupt_grading(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / 'workspace'
            shutil.copytree(ROOT / 'atomic-export' / 'fixture', workspace)
            request = Path(temp) / 'request.json'
            request.write_text(json.dumps({'workspace': str(workspace)}))
            subprocess.run([sys.executable, str(ROOT / 'oracle_adapter.py'), str(request)], check=True, capture_output=True)
            candidate = workspace / 'exporter.py'
            candidate.write_text('print("candidate diagnostic")\n' + candidate.read_text())
            self.assertTrue(self.grade('atomic-export', workspace))

    def test_buffered_in_place_write_fails_encoding_preservation(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / 'workspace'
            shutil.copytree(ROOT / 'atomic-export' / 'fixture', workspace)
            (workspace / 'exporter.py').write_text(
                'from pathlib import Path\n'
                'def export_lines(lines, destination):\n'
                '    data = "".join(line + "\\n" for line in lines)\n'
                '    Path(destination).write_text(data, encoding="utf-8")\n'
            )
            self.assertFalse(self.grade('atomic-export', workspace))

    def test_wrong_plausible_artifacts_fail(self):
        wrong = {
            'review-boundary': ('review.json', json.dumps({'findings': [
                {'file': 'unique.py', 'line': 3, 'trigger': 'empty input', 'impact': 'wrong result'}
            ]})),
            'prose-preservation': ('edited.md', 'The pilot processed 240 files; 7 failed. Recovery takes 2 hours.'),
            'research-release': ('answer.json', json.dumps({
                'version': '2.3.4', 'evidence_file': 'releases.json',
                'limitation': 'The latest publication may be a backport.'
            })),
        }
        for case, (name, artifact) in wrong.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / 'workspace'
                shutil.copytree(ROOT / case / 'fixture', workspace)
                (workspace / name).write_text(artifact)
                self.assertFalse(self.grade(case, workspace))

    def test_original_fails_and_oracle_passes(self):
        for case in CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                workspace = Path(temp) / 'workspace'
                shutil.copytree(ROOT / case / 'fixture', workspace)
                self.assertFalse(self.grade(case, workspace))
                request = Path(temp) / 'request.json'
                request.write_text(json.dumps({'workspace': str(workspace)}))
                subprocess.run([sys.executable, str(ROOT / 'oracle_adapter.py'), str(request)], check=True, capture_output=True)
                self.assertTrue(self.grade(case, workspace))
                original = next((ROOT / case / 'fixture').iterdir())
                (workspace / original.name).write_text('unrelated corruption')
                self.assertFalse(self.grade(case, workspace))

if __name__ == '__main__':
    unittest.main()
