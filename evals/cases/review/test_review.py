"""Every review case holds a real defect and a clean twin, and the grader scores both."""
import difflib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CASES = sorted(p.name for p in HERE.iterdir() if (p / 'case.json').is_file())
PROMPT = ('Review the pull request in this directory. PR.md is the author\'s description, change.diff is the diff '
          'against the base branch, and the tree is the pull request\'s head. Write review.json as {"verdict": '
          '"approve" or "needs_changes", "findings": [{"file": "path/in/tree.py", "line": 1, "blocking": true, '
          '"title": "...", "trigger": "...", "impact": "..."}]}. A finding is blocking when it must be fixed before '
          'merge. Line numbers refer to files in the tree. Do not modify any other file.')
CASE_KEYS = {'split', 'kind', 'twin', 'class', 'trap', 'also_accept'}
HINT = re.compile(r'\b(?:defect|bugs?|todo|fixme)\b', re.I)
HINT_RADIUS = 10
LAYOUT = ('prompt.md', 'case.json', 'fixture/change.diff', 'fixture/PR.md', 'proof/test_proof.py',
          'oracle/review.json', 'wrong/review.json')


def grader_module():
    spec = importlib.util.spec_from_file_location('review_grade', HERE / 'grade.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


G = grader_module()


def load(case):
    return json.loads((HERE / case / 'case.json').read_text(encoding='utf-8'))


def review_of(case, kind):
    return json.loads((HERE / case / kind / 'review.json').read_text(encoding='utf-8'))


def defect_cases():
    return [c for c in CASES if load(c)['kind'] == 'defect']


def clean_cases():
    return [c for c in CASES if load(c)['kind'] == 'clean']


def finding(file, line, blocking=True):
    return {'file': file, 'line': line, 'blocking': blocking, 'title': 'probe',
            'trigger': 'probe trigger', 'impact': 'probe impact'}


def grade(case, review=None, edits=None, extra=None, argv=None):
    """Grade a temporary copy of the fixture. review may be a dict, raw text, or a function of the workspace."""
    with tempfile.TemporaryDirectory() as temp:
        workspace = Path(temp) / 'workspace'
        shutil.copytree(HERE / case / 'fixture', workspace)
        if callable(review):
            review = review(workspace)
        if isinstance(review, (dict, list)):
            review = json.dumps(review)
        if review is not None:
            (workspace / 'review.json').write_text(review, encoding='utf-8')
        for path, text in (edits or {}).items():
            (workspace / path).write_text(text, encoding='utf-8')
        for path in extra or ():
            (workspace / path).parent.mkdir(parents=True, exist_ok=True)
            (workspace / path).write_text('x', encoding='utf-8')
        command = argv or [case, str(workspace)]
        out = subprocess.run([sys.executable, str(HERE / 'grade.py'), *command],
                             capture_output=True, text=True, timeout=60, check=True)
        return json.loads(out.stdout)


def run_tests(fixture, args, cwd=None):
    """Run unittest on a temporary copy of a fixture; returns (returncode, tests run, output)."""
    with tempfile.TemporaryDirectory() as temp:
        copy = Path(temp) / 'fixture'
        shutil.copytree(fixture, copy)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(copy))
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', *args], cwd=cwd or copy,
                                env=env, capture_output=True, text=True, timeout=120)
    output = result.stdout + result.stderr
    ran = re.search(r'^Ran (\d+) tests?', output, re.M)
    return result.returncode, int(ran.group(1)) if ran else 0, output


def run_proof(case, fixture_case):
    with tempfile.TemporaryDirectory() as temp:
        proof = Path(temp) / 'proof'
        shutil.copytree(HERE / case / 'proof', proof)
        return run_tests(HERE / fixture_case / 'fixture', ['test_proof'], cwd=proof)


def file_sections(diff_text):
    """Split a unified diff into {path: lines}, dropping index lines whose blob hashes always differ."""
    sections, current = {}, None
    for line in diff_text.splitlines():
        header = re.match(r'^diff --git a/(\S+) b/(\S+)$', line)
        if header:
            current = header.group(2)
            sections[current] = []
        elif current is not None and not line.startswith('index '):
            sections[current].append(line)
    return sections


def source_files(fixture):
    files = [p for p in fixture.rglob('*.py') if '__pycache__' not in p.parts]
    tests = [p for p in files if 'tests' in p.relative_to(fixture).parts or p.name.startswith('test_')]
    return [p for p in files if p not in tests], files


class LayoutTests(unittest.TestCase):
    def test_cases_exist_in_twin_pairs(self):
        self.assertTrue(CASES)
        self.assertEqual(len(defect_cases()), len(clean_cases()))

    def test_every_case_has_the_contract_layout(self):
        for case in CASES:
            for path in LAYOUT:
                with self.subTest(case=case, path=path):
                    self.assertTrue((HERE / case / path).is_file())

    def test_prompt_is_identical_everywhere(self):
        texts = {case: (HERE / case / 'prompt.md').read_bytes() for case in CASES}
        self.assertEqual(len(set(texts.values())), 1, sorted(texts))
        self.assertEqual(next(iter(texts.values())).decode('utf-8').rstrip('\n'), PROMPT)

    def test_case_json_follows_the_contract(self):
        for case in CASES:
            with self.subTest(case=case):
                data = load(case)
                fixture = HERE / case / 'fixture'
                expected = CASE_KEYS | ({'defect'} if data['kind'] == 'defect' else set())
                self.assertEqual(set(data), expected)
                self.assertIn(data['split'], ('development', 'holdout'))
                self.assertIn(data['kind'], ('defect', 'clean'))
                self.assertTrue(isinstance(data['class'], str) and data['class'])
                self.assertTrue(data['trap'] is None or (isinstance(data['trap'], str) and data['trap']))
                spans = list(data['also_accept']) + ([data['defect']] if 'defect' in data else [])
                for span in spans:
                    lines = (fixture / span['file']).read_text(encoding='utf-8').splitlines()
                    self.assertTrue(1 <= span['start_line'] <= span['end_line'] <= len(lines), span)
                if 'defect' in data:
                    defect = data['defect']
                    source = (fixture / defect['file']).read_text(encoding='utf-8')
                    G.function_span(source, defect['function'], defect['start_line'], defect['end_line'])

    def test_fixture_size_follows_the_contract(self):
        for case in CASES:
            with self.subTest(case=case):
                fixture = HERE / case / 'fixture'
                sources, files = source_files(fixture)
                self.assertTrue(4 <= len(sources) <= 7, [p.name for p in sources])
                total = sum(len(p.read_text(encoding='utf-8').splitlines()) for p in files)
                self.assertTrue(300 <= total <= 700, total)
                self.assertTrue((fixture / 'PR.md').read_text(encoding='utf-8').strip())


class TwinTests(unittest.TestCase):
    def test_twins_pair_up(self):
        for case in CASES:
            with self.subTest(case=case):
                data = load(case)
                twin = data['twin']
                self.assertIn(twin, CASES)
                other = load(twin)
                self.assertEqual(other['twin'], case)
                self.assertNotEqual(other['kind'], data['kind'])
                for key in ('class', 'split', 'trap'):
                    self.assertEqual(other[key], data[key], key)
                for path in ('fixture/PR.md', 'prompt.md', 'proof/test_proof.py'):
                    self.assertEqual((HERE / case / path).read_bytes(), (HERE / twin / path).read_bytes(), path)

    def test_twin_trees_differ_only_at_the_defect(self):
        """The fix touches the defect lines and may also touch an also_accept file (a test that
        encoded the defect, a caller); nothing else in the tree or the diff may differ."""
        for case in defect_cases():
            with self.subTest(case=case):
                data = load(case)
                defect = data['defect']
                fix_files = {defect['file']} | {span['file'] for span in data['also_accept']}
                head, clean = HERE / case / 'fixture', HERE / data['twin'] / 'fixture'
                self.assertEqual(G.tree_files(head), G.tree_files(clean))
                changed = {p for p in G.tree_files(head) if (head / p).read_bytes() != (clean / p).read_bytes()}
                self.assertIn(defect['file'], changed)
                self.assertEqual(sorted(changed - fix_files - {'change.diff'}), [])
                before = (head / defect['file']).read_text(encoding='utf-8').splitlines()
                after = (clean / defect['file']).read_text(encoding='utf-8').splitlines()
                low, high = defect['start_line'] - G.WINDOW, defect['end_line'] + G.WINDOW
                for tag, i1, i2, _, _ in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
                    if tag != 'equal':
                        self.assertTrue(low <= i1 + 1 and max(i1, i2) <= high, (tag, i1 + 1, i2))
                ours = file_sections((head / 'change.diff').read_text(encoding='utf-8'))
                theirs = file_sections((clean / 'change.diff').read_text(encoding='utf-8'))
                for path in (set(ours) | set(theirs)) - fix_files:
                    self.assertEqual(ours.get(path), theirs.get(path), path)

    def test_change_diff_reverses_onto_the_head_tree(self):
        git = shutil.which('git')
        if git is None:
            self.skipTest('git is not installed')
        for case in CASES:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                copy = Path(temp) / 'head'
                shutil.copytree(HERE / case / 'fixture', copy)
                env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                           GIT_CEILING_DIRECTORIES=temp)
                result = subprocess.run([git, 'apply', '--check', '-R', 'change.diff'], cwd=copy, env=env,
                                        capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr)
                diff_text = (copy / 'change.diff').read_text(encoding='utf-8')
                self.assertTrue(80 <= len(diff_text.splitlines()) <= 200, len(diff_text.splitlines()))
                self.assertGreaterEqual(len(G.diff_files(diff_text)), 3)

    def test_no_hint_words_near_the_defect(self):
        for case in defect_cases():
            defect = load(case)['defect']
            for fixture_case in (case, load(case)['twin']):
                with self.subTest(case=fixture_case):
                    lines = (HERE / fixture_case / 'fixture' / defect['file']).read_text(encoding='utf-8').splitlines()
                    start = max(0, defect['start_line'] - 1 - HINT_RADIUS)
                    nearby = lines[start:defect['end_line'] + HINT_RADIUS]
                    self.assertEqual([line for line in nearby if HINT.search(line)], [])


class ExecutionTests(unittest.TestCase):
    def test_fixture_tests_pass_in_both_twins(self):
        for case in CASES:
            with self.subTest(case=case):
                code, ran, output = run_tests(HERE / case / 'fixture', ['discover', '-s', '.', '-t', '.'])
                self.assertEqual(code, 0, output[-2000:])
                self.assertGreater(ran, 0, output[-2000:])

    def test_proof_fails_on_the_defect_and_passes_on_the_clean_twin(self):
        for case in defect_cases():
            twin = load(case)['twin']
            with self.subTest(case=case):
                code, ran, output = run_proof(case, case)
                self.assertNotEqual(code, 0, output[-2000:])
                self.assertGreater(ran, 0, output[-2000:])
                self.assertIn('FAILED (failures=', output)
                self.assertNotRegex(output, r'(ImportError|ModuleNotFoundError|SyntaxError)')
            with self.subTest(case=twin):
                code, ran, output = run_proof(twin, twin)
                self.assertEqual(code, 0, output[-2000:])
                self.assertGreater(ran, 0, output[-2000:])


class GraderTests(unittest.TestCase):
    def test_oracles_pass(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case, review_of(case, 'oracle'))
                self.assertTrue(result['passed'], result)
                self.assertTrue(result['requires_human_review'])
                if load(case)['kind'] == 'defect':
                    self.assertIs(result['metrics']['defect_found_loose'], True)

    def test_wrong_reviews_fail_on_the_outcome_check(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case, review_of(case, 'wrong'))
                self.assertFalse(result['passed'], result)
                self.assertIs(result['checks']['review_shape'], True)
                key = 'defect_found_strict' if load(case)['kind'] == 'defect' else 'no_blocking_findings'
                self.assertIs(result['checks'][key], False)

    def test_metrics_are_reported(self):
        for case in CASES:
            with self.subTest(case=case):
                metrics = grade(case, review_of(case, 'oracle'))['metrics']
                for key in ('verdict', 'findings', 'blocking', 'other_blocking', 'nonblocking', 'anchors_outside_diff'):
                    self.assertIn(key, metrics)

    def test_missing_review_fails_readably(self):
        result = grade(CASES[0])
        self.assertFalse(result['passed'])
        self.assertIs(result['checks']['review_readable'], False)
        self.assertIn('review.json is missing', result['checks']['error'])

    def test_malformed_review_fails_readably(self):
        result = grade(CASES[0], '{"verdict": "approve", "findings": [')
        self.assertFalse(result['passed'])
        self.assertIs(result['checks']['review_readable'], False)

    def test_shape_errors_fail_even_when_the_anchor_matches(self):
        case = defect_cases()[0]
        oracle = review_of(case, 'oracle')
        broken = [
            dict(oracle, verdict='lgtm'),
            dict(oracle, findings=[dict(oracle['findings'][0], line=str(oracle['findings'][0]['line']))]),
            dict(oracle, findings=[dict(oracle['findings'][0], trigger='')]),
            dict(oracle, findings=[dict(oracle['findings'][0], blocking='yes')]),
        ]
        for review in broken:
            with self.subTest(review=review):
                result = grade(case, review)
                self.assertFalse(result['passed'])
                self.assertIs(result['checks']['review_shape'], False)
                self.assertIn('error', result['checks'])

    def test_modified_fixture_fails_even_with_a_good_review(self):
        for case in (defect_cases()[0], clean_cases()[0]):
            with self.subTest(case=case):
                path = load(case).get('defect', {}).get('file') or 'PR.md'
                result = grade(case, review_of(case, 'oracle'), edits={path: 'rewritten\n'})
                self.assertFalse(result['passed'])
                self.assertIs(result['checks']['fixture_unchanged'], False)

    def test_scratch_and_extra_files_do_not_fail(self):
        case = defect_cases()[0]
        result = grade(case, review_of(case, 'oracle'), extra=['__pycache__/x.pyc', 'notes.txt'])
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['metrics']['extra_files'], ['notes.txt'])

    def test_unknown_case_fails_readably(self):
        result = grade(CASES[0], '{}', argv=['../escape', str(HERE)])
        self.assertFalse(result['passed'])
        self.assertIn('unknown case', result['checks']['error'])

    def test_file_spellings_are_normalized(self):
        for case in defect_cases():
            target = load(case)['defect']['file']
            spellings = ['./' + target, 'b/' + target, lambda ws: str(ws / target)]
            if sum(1 for p in G.tree_files(HERE / case / 'fixture') if Path(p).name == Path(target).name) == 1:
                spellings.append(Path(target).name)
            for spelling in spellings:
                with self.subTest(case=case, spelling=spelling):
                    def review(workspace, spelling=spelling):
                        name = spelling(workspace) if callable(spelling) else spelling
                        return {'verdict': 'needs_changes', 'findings': [finding(name, load(case)['defect']['start_line'])]}
                    self.assertTrue(grade(case, review)['passed'])

    def test_strict_window_edges(self):
        for case in defect_cases():
            defect = load(case)['defect']
            accept = load(case)['also_accept']

            def accepted(line):
                return any(s['file'] == defect['file'] and s['start_line'] <= line <= s['end_line'] for s in accept)
            with self.subTest(case=case):
                for line in (defect['start_line'] - G.WINDOW, defect['end_line'] + G.WINDOW):
                    if line >= 1:
                        review = {'verdict': 'needs_changes', 'findings': [finding(defect['file'], line)]}
                        self.assertTrue(grade(case, review)['checks']['defect_found_strict'], line)
                outside = defect['start_line'] - G.WINDOW - 1
                if outside >= 1 and not accepted(outside):
                    review = {'verdict': 'needs_changes', 'findings': [finding(defect['file'], outside)]}
                    self.assertFalse(grade(case, review)['checks']['defect_found_strict'], outside)

    def test_loose_match_covers_the_enclosing_function_only(self):
        probed = 0
        for case in defect_cases():
            defect = load(case)['defect']
            source = (HERE / case / 'fixture' / defect['file']).read_text(encoding='utf-8')
            first, last = G.function_span(source, defect['function'], defect['start_line'], defect['end_line'])
            if first >= defect['start_line'] - G.WINDOW:
                continue
            probed += 1
            with self.subTest(case=case):
                review = {'verdict': 'needs_changes', 'findings': [finding(defect['file'], first)]}
                result = grade(case, review)
                self.assertFalse(result['passed'])
                self.assertIs(result['metrics']['defect_found_loose'], True)
                self.assertEqual(result['metrics']['other_blocking'], 1)
                if last + 1 <= len(source.splitlines()):
                    outside = {'verdict': 'needs_changes', 'findings': [finding(defect['file'], last + 1)]}
                    self.assertIs(grade(case, outside)['metrics']['defect_found_loose'], False)
        self.assertGreater(probed, 0)

    def test_nonblocking_finding_at_the_defect_does_not_count(self):
        for case in defect_cases():
            defect = load(case)['defect']
            with self.subTest(case=case):
                review = {'verdict': 'approve', 'findings': [finding(defect['file'], defect['start_line'], blocking=False)]}
                result = grade(case, review)
                self.assertFalse(result['passed'])
                self.assertEqual((result['metrics']['blocking'], result['metrics']['nonblocking']), (0, 1))

    def test_also_accept_spans_count_as_strict(self):
        for case in defect_cases():
            for span in load(case)['also_accept']:
                with self.subTest(case=case, span=span):
                    review = {'verdict': 'needs_changes', 'findings': [finding(span['file'], span['end_line'])]}
                    self.assertTrue(grade(case, review)['passed'])

    def test_other_blocking_and_outside_diff_are_metrics_only(self):
        for case in defect_cases():
            fixture = HERE / case / 'fixture'
            touched = G.diff_files((fixture / 'change.diff').read_text(encoding='utf-8'))
            untouched = [p for p in G.tree_files(fixture) if p.endswith('.py') and p not in touched]
            if not untouched:
                continue
            with self.subTest(case=case):
                oracle = review_of(case, 'oracle')
                review = dict(oracle, findings=oracle['findings'] + [finding(untouched[0], 1)])
                result = grade(case, review)
                self.assertTrue(result['passed'], result)
                self.assertGreaterEqual(result['metrics']['other_blocking'], 1)
                self.assertIs(result['metrics']['anchors_outside_diff'], True)

    def test_clean_case_allows_nonblocking_and_rejects_any_blocking(self):
        for case in clean_cases():
            twin_defect = load(load(case)['twin'])['defect']
            with self.subTest(case=case):
                soft = {'verdict': 'approve', 'findings': [finding(twin_defect['file'], twin_defect['start_line'], blocking=False)]}
                self.assertTrue(grade(case, soft)['passed'])
                hard = {'verdict': 'approve', 'findings': [finding(twin_defect['file'], twin_defect['start_line'])]}
                result = grade(case, hard)
                self.assertFalse(result['passed'])
                self.assertEqual(result['metrics']['other_blocking'], 1)

    def test_diff_file_parser(self):
        text = ('diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n'
                'diff --git a/new.py b/new.py\n--- /dev/null\n+++ b/new.py\n'
                'diff --git a/gone.py b/gone.py\n--- a/gone.py\n+++ /dev/null\n')
        self.assertEqual(G.diff_files(text), {'x.py', 'new.py', 'gone.py'})


if __name__ == '__main__':
    unittest.main()
