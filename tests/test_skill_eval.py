"""Executable protocol tests; stand-ins are not skill efficacy evidence."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('skill_eval', Path(__file__).parents[1] / 'scripts/skill_eval.py')
eval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(eval)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'skills/example').mkdir(parents=True)
        (self.root / 'skills/example/SKILL.md').write_text('Useful guidance')
        (self.root / 'fixture').mkdir()
        (self.root / 'fixture/input.txt').write_text('unchanged')
        (self.root / 'prompt.txt').write_text('Produce output')
        (self.root / 'adapter.py').write_text('import json,sys\nfrom pathlib import Path\nr=json.load(open(sys.argv[1]))\nw=Path(r["workspace"])\nassert (w/"input.txt").read_text()=="unchanged"\nassert bool(list(Path(r["skills"]).iterdir()))==(r["arm"]!="baseline")\n(w/"output.txt").write_text(r["arm"])\n')
        (self.root / 'grader.py').write_text('import json,sys\nfrom pathlib import Path\nprint(json.dumps({"passed":(Path(sys.argv[1])/"output.txt").read_text()!="baseline"}))\n')
        self.data = {'version': 1, 'name': 'test', 'skills_root': 'skills', 'tasks': [{'id': 'task', 'family': 'code', 'split': 'development', 'prompt': 'prompt.txt', 'fixture': 'fixture', 'skills': ['example'], 'grader': [sys.executable, 'grader.py']}], 'configurations': [{'id': 'fake', 'model': 'stand-in', 'harness': 'test', 'adapter': [sys.executable, 'adapter.py']}]}
        self.suite = self.root / 'suite.json'
        self.save()
        self.plan = self.root / 'plan.json'
        self.run = self.root / 'run'

    def save(self):
        self.suite.write_text(json.dumps(self.data))

    def test_paired_execution_and_missing_pairs(self):
        frozen = eval.plan(self.suite, self.plan, repeats=2)
        self.assertEqual(len(frozen['trials']), 6)
        eval.run(self.plan, self.run)
        report = eval.report(self.run)
        self.assertEqual(report['completed'], 6)
        self.assertEqual(report['missing_cost_records'], 6)
        self.assertTrue(all(c['mean_delta'] == 1 for c in report['comparisons']))
        self.assertEqual((self.root / 'fixture/input.txt').read_text(), 'unchanged')
        result = next(self.run.glob('*/result.json'))
        result.unlink()
        self.assertEqual(eval.report(self.run)['completed'], 5)
        self.assertTrue(any(c['missing_pairs'] for c in eval.report(self.run)['excluded_pairs']))

    def test_changed_inputs_and_overwrite_rejected(self):
        eval.plan(self.suite, self.plan)
        with self.assertRaises(FileExistsError):
            eval.plan(self.suite, self.plan)
        (self.root / 'prompt.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            eval.run(self.plan, self.run)

    def test_nonzero_adapter_is_recorded_failure(self):
        (self.root / 'adapter.py').write_text('raise SystemExit(7)')
        eval.plan(self.suite, self.plan, repeats=1)
        eval.run(self.plan, self.run)
        for path in self.run.glob('*/result.json'):
            result = eval.read(path)
            self.assertFalse(result['passed'])
            self.assertEqual(result['adapter']['exit_code'], 7)
        with self.assertRaises(FileExistsError):
            eval.run(self.plan, self.run)

    def test_grader_error_cannot_be_pass(self):
        (self.root / 'grader.py').write_text('print("not json")')
        eval.plan(self.suite, self.plan, repeats=1)
        eval.run(self.plan, self.run)
        for path in self.run.glob('*/result.json'):
            result = eval.read(path)
            self.assertFalse(result['passed'])
            self.assertIn('grading_error', result)

    def test_revision_comparison_and_malformed_metrics(self):
        with (self.root / 'adapter.py').open('a') as stream:
            stream.write('Path(r["metrics"]).write_text("malformed")\n')
        eval.plan(self.suite, self.plan, repeats=1)
        eval.run(self.plan, self.run)
        self.assertTrue(all('metrics_error' in eval.read(p) for p in self.run.glob('*/result.json')))
        (self.root / 'skills/example/SKILL.md').write_text('Revised guidance')
        next_plan, next_run = self.root / 'next.json', self.root / 'next'
        eval.plan(self.suite, next_plan, repeats=1, seed=4)
        eval.run(next_plan, next_run)
        comparison = eval.compare(self.run, next_run)
        self.assertEqual(comparison['missing_pairs'], 0)
        self.assertTrue(all(c['mean_delta'] == 0 for c in comparison['comparisons']))
        changed = eval.read(next_run / 'plan.json')
        changed['suite']['configurations'][0]['model'] = 'different'
        eval.write(next_run / 'plan.json', changed)
        with self.assertRaisesRegex(ValueError, 'identical non-skill'):
            eval.compare(self.run, next_run)

    def test_infrastructure_errors_excluded(self):
        (self.root / 'adapter.py').write_text('raise SystemExit(7)')
        eval.plan(self.suite, self.plan, repeats=1)
        eval.run(self.plan, self.run)
        report = eval.report(self.run)
        self.assertEqual(report['comparisons'], [])
        self.assertTrue(all(r['invalid_pairs'] == 1 for r in report['excluded_pairs']))
        self.assertTrue(all(r['status_counts']['adapter_error'] == 1 for r in report['resources']))

    def test_midrun_input_mutation_stops_with_receipt(self):
        with (self.root / 'adapter.py').open('a') as stream:
            stream.write(f'Path({str(self.root / "prompt.txt")!r}).write_text("mutated")\n')
        eval.plan(self.suite, self.plan, repeats=2)
        eval.run(self.plan, self.run)
        receipts = list(self.run.glob('*/result.json'))
        self.assertEqual(len(receipts), 1)
        self.assertEqual(eval.read(receipts[0])['status'], 'input_changed')
        self.assertEqual(eval.report(self.run)['comparisons'], [])

    def test_observed_metadata_mismatch_rejected(self):
        eval.plan(self.suite, self.plan, repeats=1)
        eval.run(self.plan, self.run)
        second = self.root / 'second'
        eval.run(self.plan, second)
        for directory, version in ((self.run, 'one'), (second, 'two')):
            for path in directory.glob('*/result.json'):
                row = eval.read(path)
                row['reported_metrics'] = {'cli_version': version, 'served_models': ['model-v1']}
                eval.write(path, row)
        with self.assertRaisesRegex(ValueError, 'cli_versions differ'):
            eval.compare(self.run, second)

    def test_command_preserves_symlink_interpreter(self):
        link = self.root / 'python'
        link.symlink_to(sys.executable)
        self.assertEqual(eval.command(['python'], self.root), [str(link)])

    def test_grader_dependencies_are_frozen(self):
        helper = self.root / 'helper.py'
        helper.write_text('original')
        self.data['tasks'][0]['grader_inputs'] = ['helper.py']
        self.save()
        eval.plan(self.suite, self.plan)
        helper.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'inputs changed'):
            eval.run(self.plan, self.run)

    def test_human_review_remains_pending(self):
        (self.root / 'grader.py').write_text('print(\'{"passed": true, "requires_human_review": true}\')')
        eval.plan(self.suite, self.plan, repeats=1)
        eval.run(self.plan, self.run)
        report = eval.report(self.run)
        self.assertTrue(all(r['pending_human_review'] == 1 for r in report['resources']))
        self.assertTrue(all(r['family'] == 'code' for r in report['comparisons']))

    def test_validation_and_holdout_selection(self):
        self.data['tasks'][0]['skills'] = ['../example']
        self.save()
        with self.assertRaises(ValueError):
            eval.suite(self.suite)
        self.data['tasks'][0]['skills'] = ['example']
        self.save()
        with self.assertRaisesRegex(ValueError, 'no tasks'):
            eval.plan(self.suite, self.plan, split='holdout')


if __name__ == '__main__':
    unittest.main()
