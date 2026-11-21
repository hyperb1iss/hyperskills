"""Oracles pass, wrong edits fail on the check their trap targets, and broken workspaces fail readably."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CASES = sorted(p.name for p in HERE.iterdir() if (p / 'prompt.md').is_file())
TRAPS = ('padded-slop', 'citation-trap', 'voice-trap', 'hedge-trap')
METRIC_KEYS = {'words', 'numbers_introduced', 'contrast_frames', 'contractions', 'first_person', 'similarity'}


def load_spec(case):
    return json.loads((HERE / case / 'spec.json').read_text(encoding='utf-8'))


def edit_from(case, kind):
    source = HERE / case / 'fixture' / 'draft.md' if kind == 'unchanged' else HERE / case / kind / 'edited.md'
    return source.read_text(encoding='utf-8')


def grade(case, edit=None, draft=None, argv=None):
    with tempfile.TemporaryDirectory() as temp:
        workspace = Path(temp) / 'workspace'
        shutil.copytree(HERE / case / 'fixture', workspace)
        if edit is not None:
            (workspace / 'edited.md').write_text(edit, encoding='utf-8')
        if draft is not None:
            (workspace / 'draft.md').write_text(draft, encoding='utf-8')
        command = argv or [case, str(workspace)]
        out = subprocess.run([sys.executable, str(HERE / 'grade.py'), *command],
                             capture_output=True, text=True, timeout=60, check=True)
        return json.loads(out.stdout)


def grader_module():
    spec = importlib.util.spec_from_file_location('preserve_grade', HERE / 'grade.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreserveGraderTests(unittest.TestCase):
    def test_two_cases_per_trap_with_a_valid_split(self):
        self.assertEqual(len(CASES), 8)
        for trap in TRAPS:
            splits = [load_spec(c)['split'] for c in CASES if load_spec(c)['trap'] == trap]
            self.assertEqual(len(splits), 2, trap)
            self.assertTrue(set(splits) <= {'development', 'holdout'}, trap)

    def test_case_layout(self):
        for case in CASES:
            with self.subTest(case=case):
                self.assertEqual([p.name for p in (HERE / case / 'fixture').iterdir()], ['draft.md'])
                for kind in ('oracle', 'wrong'):
                    self.assertTrue((HERE / case / kind / 'edited.md').is_file())

    def test_spec_strings_and_patterns_match_their_own_draft(self):
        for case in CASES:
            with self.subTest(case=case):
                checks = grade(case, edit_from(case, 'unchanged'))['checks']
                targeted = {k: v for k, v in checks.items() if k.startswith(('protected:', 'calibration:'))}
                self.assertTrue(targeted)
                self.assertEqual([k for k, v in targeted.items() if v is not True], [])

    def test_oracles_pass(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case, edit_from(case, 'oracle'))
                self.assertTrue(result['passed'], result)
                self.assertTrue(result['requires_human_review'])
                self.assertTrue(METRIC_KEYS <= set(result['metrics']), result['metrics'])

    def test_wrong_edits_fail_on_their_intended_checks(self):
        for case in CASES:
            with self.subTest(case=case):
                expected = load_spec(case)['wrong_must_fail']
                result = grade(case, edit_from(case, 'wrong'))
                self.assertFalse(result['passed'], result)
                self.assertTrue(expected)
                for name in expected:
                    self.assertIs(result['checks'].get(name), False, (name, result['checks']))

    def test_unchanged_copy_passes_voice_and_fails_padded_slop(self):
        for case in CASES:
            trap = load_spec(case)['trap']
            if trap not in ('voice-trap', 'padded-slop'):
                continue
            with self.subTest(case=case):
                result = grade(case, edit_from(case, 'unchanged'))
                if trap == 'voice-trap':
                    self.assertTrue(result['passed'], result)
                else:
                    self.assertFalse(result['passed'], result)
                    self.assertIs(result['checks']['shorter_than_draft'], False)

    def test_missing_edit_fails_readably(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case)
                self.assertFalse(result['passed'])
                self.assertIs(result['checks']['edited_readable'], False)
                self.assertIn('edited.md is missing', result['checks']['error'])

    def test_empty_edit_fails_readably(self):
        result = grade(CASES[0], '  \n')
        self.assertFalse(result['passed'])
        self.assertIn('empty', result['checks']['error'])

    def test_modified_draft_fails_even_with_a_good_edit(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case, edit_from(case, 'oracle'), draft='rewritten in place\n')
                self.assertFalse(result['passed'])
                self.assertIs(result['checks']['source_preserved'], False)

    def test_unknown_case_fails_readably(self):
        result = grade(CASES[0], 'text', argv=['../escape', str(HERE)])
        self.assertFalse(result['passed'])
        self.assertIn('unknown case', result['checks']['error'])

    def test_metric_patterns(self):
        g = grader_module()
        self.assertEqual(g.contrast_frames('It is not just fast but cheap.'), 1)
        self.assertEqual(g.contrast_frames('The fault was not the parser but the file.'), 1)
        self.assertEqual(g.contrast_frames("I'm not sure, but it helps."), 0)
        self.assertEqual(g.contrast_frames('Use the cache rather than the disk.'), 1)
        self.assertEqual(g.contrast_frames('It is a pilot, not a rollout.'), 1)
        self.assertEqual(g.contrast_frames("It isn't the parser; it's the file."), 1)
        self.assertEqual(g.count(g.CONTRACTION, "We're sure it's Dana's and they'll say so; don't."), 4)
        self.assertEqual(g.count(g.FIRST_PERSON, 'I told my team we would; us too.'), 4)
        self.assertEqual(g.introduced_numbers('Moved 1,840 of three queues in 2.50 s.', 'Moved 1840 of 3 queues in 2.5 s; one left.'), [])
        self.assertEqual(g.introduced_numbers('Took 3 weeks.', 'Steps:\n1. Took 3 weeks, a 40% gain.'), ['40'])
        self.assertEqual(g.certainty_added('This may help.', 'This does not prove it, but it clearly helps.', ['prove', 'clearly']), {'clearly': 1})
        self.assertEqual(g.similarity('Hey, it works.', 'hey it works'), 1.0)
        curly = '\u201cdon\u2019t\u201d \u2013 3\u20134\u00a0weeks \u2014 \u22124'
        self.assertEqual(g.flatten(curly), '"don\'t" - 3-4 weeks - -4')
        self.assertEqual(g.count(g.CONTRACTION, curly), 1)

    def test_negation_does_not_cross_a_sentence_boundary(self):
        probe = ' The investigation is not complete. Results prove the rollback fixes the problem.'
        edit = edit_from('hedge-trap-postmortem', 'oracle').rstrip('\n') + probe + '\n'
        result = grade('hedge-trap-postmortem', edit)
        self.assertFalse(result['passed'])
        self.assertIs(result['checks']['no_certainty_upgrade'], False)
        self.assertEqual(result['metrics']['certainty_terms_added'], {'prove': 1})
        g = grader_module()
        self.assertEqual(g.certainty_added('', 'This does not prove it.', ['prove']), {})
        self.assertEqual(g.certainty_added('', 'Not yet; this proves it.', ['proves']), {'proves': 1})
        self.assertEqual(g.certainty_added('', 'We did not see 2.5 proven gains.', ['proven']), {})

    def test_prose_terms_ignore_case_and_exact_items_do_not(self):
        postmortem = edit_from('hedge-trap-postmortem', 'oracle')
        bulleted = (postmortem
                    .replace('The retry storm that followed', '- **Retry storm:** the storm that followed')
                    .replace('the connection-pool change in build', 'the **Connection-pool change** in build'))
        self.assertNotIn('retry storm', bulleted)
        self.assertNotIn('connection-pool', bulleted)
        result = grade('hedge-trap-postmortem', bulleted)
        self.assertTrue(result['passed'], result)
        status = edit_from('padded-slop-status-update', 'oracle')
        command = grade('padded-slop-status-update', status.replace('`tidectl move', '`Tidectl move'))
        self.assertFalse(command['passed'])
        self.assertIs(command['checks']['protected:tidectl move --queue <name> --verify'], False)
        quote = grade('padded-slop-status-update', status.replace('"Nothing gets', '"nothing gets'))
        self.assertFalse(quote['passed'])
        self.assertEqual([k for k, v in quote['checks'].items() if v is not True],
                         ['protected:Nothing gets deleted from the old cluster until the verify step reports zero drift'])

    def test_commitment_phrasing_keeps_the_claim_and_a_bare_estimate_does_not(self):
        oracle = edit_from('padded-slop-status-update', 'oracle')
        original = 'That is an estimate, not a guarantee; the timeline'
        self.assertIn(original, oracle)
        kept = grade('padded-slop-status-update', oracle.replace(original, 'This is an estimate, not a commitment. The timeline'))
        self.assertTrue(kept['passed'], kept)
        bare = grade('padded-slop-status-update', oracle.replace(original, 'This is an estimate. The timeline'))
        self.assertFalse(bare['passed'])
        self.assertIs(bare['checks']['calibration:not a guarantee'], False)
        self.assertIs(bare['checks']['calibration:estimate'], True)

    def test_calibration_examples_match_and_counterexamples_do_not(self):
        g = grader_module()
        for case in CASES:
            for item in load_spec(case).get('calibrations', []):
                with self.subTest(case=case, calibration=item['label']):
                    self.assertGreaterEqual(len(item['accepts']), 3)
                    self.assertTrue(item['rejects'])
                    for text in item['accepts']:
                        self.assertTrue(g.calibration_holds(item['patterns'], text), text)
                    for text in item['rejects']:
                        self.assertFalse(g.calibration_holds(item['patterns'], text), text)

    def test_protected_items_are_strings_lists_or_exact_objects(self):
        g = grader_module()
        for case in CASES:
            for item in load_spec(case)['protected']:
                with self.subTest(case=case, item=item):
                    options, exact = g.protected_options(item)
                    self.assertTrue(options and all(isinstance(o, str) and o for o in options))
                    self.assertEqual(exact, isinstance(item, dict))


if __name__ == '__main__':
    unittest.main()
