#!/usr/bin/env python3
"""Check the replay grader's verdict logic without Docker or the target repository."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade  # noqa: E402

JUNIT = '''<testsuites><testsuite>
<testcase classname="tests.test_a" name="test_fixed"/>
<testcase classname="tests.test_a" name="test_kept"/>
<testcase classname="tests.test_a" name="test_broken"><failure message="x"/></testcase>
<testcase classname="tests.test_a" name="test_crashed"><error message="x"/></testcase>
<testcase classname="tests.test_a" name="test_skipped"><skipped/></testcase>
</testsuite></testsuites>'''


class GradeTest(unittest.TestCase):
    def setUp(self):
        self.outcomes = grade.outcomes_from_junit(JUNIT)

    def test_outcomes_name_each_state(self):
        self.assertEqual(self.outcomes, {
            'tests.test_a::test_fixed': 'passed', 'tests.test_a::test_kept': 'passed',
            'tests.test_a::test_broken': 'failed', 'tests.test_a::test_crashed': 'error',
            'tests.test_a::test_skipped': 'skipped'})

    def test_passes_only_when_every_named_test_is_green(self):
        case = {'fail_to_pass': ['tests.test_a::test_fixed'], 'pass_to_pass': ['tests.test_a::test_kept']}
        self.assertTrue(grade.verdict(case, self.outcomes)['passed'])

    def test_a_regression_fails_the_case(self):
        case = {'fail_to_pass': ['tests.test_a::test_fixed'], 'pass_to_pass': ['tests.test_a::test_broken']}
        result = grade.verdict(case, self.outcomes)
        self.assertFalse(result['passed'])
        self.assertEqual(result['checks'], {'fail_to_pass': True, 'pass_to_pass': False})

    def test_a_missing_or_skipped_test_is_not_a_pass(self):
        case = {'fail_to_pass': ['tests.test_a::test_gone', 'tests.test_a::test_skipped'], 'pass_to_pass': []}
        result = grade.verdict(case, self.outcomes)
        self.assertFalse(result['passed'])
        self.assertEqual(result['fail_to_pass_passed'], 0)

    def test_no_outcomes_fails(self):
        case = {'fail_to_pass': ['tests.test_a::test_fixed'], 'pass_to_pass': []}
        self.assertFalse(grade.verdict(case, {})['passed'])

    def test_test_file_hashes_see_a_new_test(self):
        with tempfile.TemporaryDirectory() as root:
            tests = Path(root) / 'app' / 'tests'
            tests.mkdir(parents=True)
            (tests / 'test_a.py').write_text('x = 1\n')
            before = grade.test_file_hashes(Path(root), 'app')
            (tests / 'test_b.py').write_text('y = 2\n')
            after = grade.test_file_hashes(Path(root), 'app')
        self.assertEqual(sorted(set(after) - set(before)), ['app/tests/test_b.py'])


if __name__ == '__main__':
    unittest.main()
