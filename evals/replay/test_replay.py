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


    def test_own_tests_are_sorted_by_how_they_fared_before_the_fix(self):
        after = {'t::regression': 'passed', 't::always_green': 'passed', 't::needs_new_symbol': 'passed',
                 't::setup_broke': 'passed', 't::still_red': 'failed'}
        before = {'t::regression': 'failed', 't::always_green': 'passed', 't::setup_broke': 'error', 't::still_red': 'failed'}
        self.assertEqual(grade.own_test_verdict(before, after), {
            'ran': 5, 'fail_before_pass_after': ['t::regression'], 'pass_before': 1,
            'not_runnable_before': ['t::needs_new_symbol', 't::setup_broke'], 'not_passing_after': ['t::still_red']})

    def test_no_own_tests_ships_no_regression_test(self):
        self.assertEqual(grade.own_test_verdict({}, {})['fail_before_pass_after'], [])

    def test_only_the_submissions_test_files_reach_the_unfixed_tree(self):
        with tempfile.TemporaryDirectory() as root:
            work, tree = Path(root, 'work'), Path(root, 'tree')
            for path, text in (('p/tests/test_a.py', 'new'), ('p/tests/conftest.py', 'helper'), ('p/src/m.py', 'fixed')):
                (work / path).parent.mkdir(parents=True, exist_ok=True)
                (work / path).write_text(text)
            (tree / 'p/src').mkdir(parents=True)
            (tree / 'p/src/m.py').write_text('broken')
            grade.lay_over(work, tree, ['p/tests/test_a.py', 'p/tests/conftest.py'])
            self.assertEqual((tree / 'p/tests/test_a.py').read_text(), 'new')
            self.assertEqual((tree / 'p/tests/conftest.py').read_text(), 'helper')
            self.assertEqual((tree / 'p/src/m.py').read_text(), 'broken')


if __name__ == '__main__':
    unittest.main()
