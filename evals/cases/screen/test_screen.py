"""The reference solution passes every check and the untouched fixture fails, for every screen case."""
import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = sorted(p.name for p in HERE.iterdir() if (p / 'prompt.md').is_file())


def grade(case, overlay):
    with tempfile.TemporaryDirectory() as temp:
        trial = Path(temp)
        shutil.copytree(HERE / case / 'fixture', trial / 'workspace')
        if overlay:
            shutil.copytree(HERE / case / 'oracle', trial / 'workspace', dirs_exist_ok=True)
            (trial / 'actions-0.json').write_text(json.dumps({'actions': [{'type': 'text', 'role': 'assistant', 'text': 'Two contacts share an email that differs only by case, and one has a null email; I skipped the null one.'}]}))
        else:
            (trial / 'actions-0.json').write_text(json.dumps({'actions': [{'type': 'text', 'role': 'assistant', 'text': 'Done.'}]}))
        out = subprocess.run([sys.executable, str(HERE / 'grade.py'), case, str(trial / 'workspace')], cwd=trial, capture_output=True, text=True, timeout=120)
        return json.loads(out.stdout)


class ScreenGraderTests(unittest.TestCase):
    def test_eight_cases(self):
        self.assertEqual(len(CASES), 8)

    def test_reference_solutions_pass(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case, overlay=True)
                self.assertTrue(result['passed'], result)

    def test_untouched_fixtures_fail(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case, overlay=False)
                self.assertFalse(result['passed'], result)
                self.assertFalse(result['feature_passed'], result)


if __name__ == '__main__':
    unittest.main()
