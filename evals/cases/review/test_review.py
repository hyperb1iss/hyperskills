"""Every review case holds real defects and a clean twin, and the grader scores both."""
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
CASE_KEYS = {'split', 'kind', 'twin', 'class', 'trap'}
# Records when a former holdout stopped being untouched.
OPTIONAL_KEYS = {'held_out_until'}
DEFECT_KEYS = {'id', 'class', 'file', 'start_line', 'end_line', 'function', 'also_accept'}
HINT = re.compile(r'\b(?:defect|bugs?|todo|fixme)\b', re.I)
HINT_RADIUS = 10
LAYOUT = ('prompt.md', 'case.json', 'fixture/change.diff', 'fixture/PR.md', 'proof/test_proof.py',
          'oracle/review.json', 'wrong/review.json')
# (diff lines, files the diff touches, tree lines, source files) per tier; None means unchecked.
TIERS = {
    'single': {'diff': (80, 200), 'touched': (3, None), 'python_lines': (300, 700), 'sources': (4, 7)},
    'multi': {'diff': (500, 800), 'touched': (8, 14), 'tree_lines': (1200, 2000)},
}


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


def multi_cases():
    return [c for c in defect_cases() if 'defects' in load(c)]


def defects_of(case):
    return G.planted_defects(load(case))


def tier(case):
    data = load(case)
    defect_side = data if data['kind'] == 'defect' else load(data['twin'])
    return 'multi' if 'defects' in defect_side else 'single'


def outcome_check(case):
    data = load(case)
    if data['kind'] == 'clean':
        return 'no_blocking_findings'
    return 'all_defects_found' if 'defects' in data else 'defect_found'


def finding(file, line, blocking=True):
    return {'file': file, 'line': line, 'blocking': blocking, 'title': 'probe',
            'trigger': 'probe trigger', 'impact': 'probe impact'}


def blocking_review(*anchors):
    return {'verdict': 'needs_changes', 'findings': [finding(file, line) for file, line in anchors]}


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


def tree_sizes(fixture):
    files = [p for p in fixture.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    python = [p for p in files if p.suffix == '.py']
    tests = [p for p in python if 'tests' in p.relative_to(fixture).parts or p.name.startswith('test_')]
    lines = lambda paths: sum(len(p.read_text(encoding='utf-8').splitlines()) for p in paths)
    return {'sources': len([p for p in python if p not in tests]), 'python_lines': lines(python),
            'tree_lines': lines([p for p in files if p.name not in ('change.diff', 'PR.md')])}


def within(value, bounds):
    low, high = bounds
    return value >= low and (high is None or value <= high)


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
                self.assertTrue(CASE_KEYS <= set(data), set(data))
                self.assertIn(data['split'], ('development', 'holdout'))
                self.assertIn(data['kind'], ('defect', 'clean'))
                self.assertTrue(isinstance(data['class'], str) and data['class'])
                self.assertTrue(data['trap'] is None or (isinstance(data['trap'], str) and data['trap']))
                if 'defects' in data:
                    self.assertEqual(set(data) - CASE_KEYS - OPTIONAL_KEYS, {'defects'} | ({'also_accept'} & set(data)))
                    self.assertEqual(data.get('also_accept', []), [])
                else:
                    extra = {'also_accept', 'defect'} if data['kind'] == 'defect' else {'also_accept'}
                    self.assertEqual(set(data) - CASE_KEYS - OPTIONAL_KEYS, extra)
                if data['kind'] == 'clean':
                    self.assertEqual(data['also_accept'], [])
                spans = list(data.get('also_accept', []))
                for defect in defects_of(case) if data['kind'] == 'defect' else []:
                    spans += [defect] + defect['also_accept']
                    source = (fixture / defect['file']).read_text(encoding='utf-8')
                    G.function_span(source, defect['function'], defect['start_line'], defect['end_line'])
                for span in spans:
                    lines = (fixture / span['file']).read_text(encoding='utf-8').splitlines()
                    self.assertTrue(1 <= span['start_line'] <= span['end_line'] <= len(lines), span)

    def test_multi_defect_entries_are_independent(self):
        for case in multi_cases():
            with self.subTest(case=case):
                defects = load(case)['defects']
                self.assertGreaterEqual(len(defects), 2)
                for defect in defects:
                    self.assertEqual(set(defect), DEFECT_KEYS)
                    self.assertTrue(isinstance(defect['id'], str) and defect['id'])
                for key in ('id', 'class', 'file'):
                    self.assertEqual(len({defect[key] for defect in defects}), len(defects), key)

    def test_fixture_size_follows_the_tier(self):
        for case in CASES:
            with self.subTest(case=case, tier=tier(case)):
                fixture = HERE / case / 'fixture'
                limits = TIERS[tier(case)]
                sizes = tree_sizes(fixture)
                diff_text = (fixture / 'change.diff').read_text(encoding='utf-8')
                sizes['diff'] = len(diff_text.splitlines())
                sizes['touched'] = len(G.diff_files(diff_text))
                for key, bounds in limits.items():
                    self.assertTrue(within(sizes[key], bounds), (key, sizes[key], bounds))
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

    def test_twin_trees_differ_only_at_the_defects(self):
        """Each fix stays near its defect lines and may also touch that defect's also_accept files (a test
        that encoded the defect, a caller); nothing else in the tree or the diff may differ."""
        for case in defect_cases():
            with self.subTest(case=case):
                defects = defects_of(case)
                defect_files = {d['file'] for d in defects}
                fix_files = defect_files | {s['file'] for d in defects for s in d['also_accept']}
                head, clean = HERE / case / 'fixture', HERE / load(case)['twin'] / 'fixture'
                self.assertEqual(G.tree_files(head), G.tree_files(clean))
                changed = {p for p in G.tree_files(head) if (head / p).read_bytes() != (clean / p).read_bytes()}
                self.assertEqual(sorted(defect_files - changed), [])
                self.assertEqual(sorted(changed - fix_files - {'change.diff'}), [])
                for path in defect_files:
                    windows = [(d['start_line'] - G.WINDOW, d['end_line'] + G.WINDOW) for d in defects if d['file'] == path]
                    before = (head / path).read_text(encoding='utf-8').splitlines()
                    after = (clean / path).read_text(encoding='utf-8').splitlines()
                    for tag, i1, i2, _, _ in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes():
                        if tag != 'equal':
                            self.assertTrue(any(low <= i1 + 1 and max(i1, i2) <= high for low, high in windows),
                                            (path, tag, i1 + 1, i2))
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

    def test_no_hint_words_near_a_defect(self):
        for case in defect_cases():
            for defect in defects_of(case):
                for fixture_case in (case, load(case)['twin']):
                    with self.subTest(case=fixture_case, defect=defect['id']):
                        path = HERE / fixture_case / 'fixture' / defect['file']
                        lines = path.read_text(encoding='utf-8').splitlines()
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
        """A single-defect proof needs one failing test; a multi-defect proof needs one failing test per
        defect and no test that passes on the defect tree."""
        for case in defect_cases():
            twin = load(case)['twin']
            count = len(defects_of(case))
            with self.subTest(case=case):
                code, ran, output = run_proof(case, case)
                self.assertNotEqual(code, 0, output[-2000:])
                self.assertNotRegex(output, r'(ImportError|ModuleNotFoundError|SyntaxError)')
                failures = re.search(r'FAILED \(failures=(\d+)\)', output)
                self.assertIsNotNone(failures, output[-2000:])
                if count > 1:
                    self.assertGreaterEqual(ran, count)
                    self.assertEqual(int(failures.group(1)), ran, output[-2000:])
            with self.subTest(case=twin):
                code, ran, output = run_proof(twin, twin)
                self.assertEqual(code, 0, output[-2000:])
                self.assertGreaterEqual(ran, count, output[-2000:])


class GraderTests(unittest.TestCase):
    def test_oracles_pass(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case, review_of(case, 'oracle'))
                self.assertTrue(result['passed'], result)
                self.assertTrue(result['requires_human_review'])
                if load(case)['kind'] == 'defect':
                    self.assertEqual(result['metrics']['defects_found'], result['metrics']['defects_total'])
                    self.assertEqual(sorted(result['metrics']['found_ids']), sorted(d['id'] for d in defects_of(case)))

    def test_wrong_reviews_fail_on_the_outcome_check(self):
        for case in CASES:
            with self.subTest(case=case):
                result = grade(case, review_of(case, 'wrong'))
                self.assertFalse(result['passed'], result)
                self.assertIs(result['checks']['review_shape'], True)
                self.assertIs(result['checks'][outcome_check(case)], False)

    def test_metrics_are_reported(self):
        common = {'verdict', 'findings', 'blocking', 'other_blocking', 'nonblocking', 'anchors_outside_diff',
                  'unknown_files', 'diff_line_anchors', 'extra_files'}
        for case in CASES:
            with self.subTest(case=case):
                metrics = grade(case, review_of(case, 'oracle'))['metrics']
                expected = set(common)
                if load(case)['kind'] == 'defect':
                    expected |= {'defects_total', 'defects_found', 'found_ids', 'defects_found_strict', 'strict_ids'}
                self.assertTrue(expected <= set(metrics), expected - set(metrics))

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
        first = oracle['findings'][0]
        broken = [
            dict(oracle, verdict='lgtm'),
            dict(oracle, findings=[dict(first, line=str(first['line']))] + oracle['findings'][1:]),
            dict(oracle, findings=[dict(first, trigger='')] + oracle['findings'][1:]),
            dict(oracle, findings=[dict(first, blocking='yes')] + oracle['findings'][1:]),
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
                path = defects_of(case)[0]['file'] if load(case)['kind'] == 'defect' else 'PR.md'
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
            defects = defects_of(case)
            known = G.tree_files(HERE / case / 'fixture')
            for spelling in ('./', 'b/', 'absolute', 'bare'):
                with self.subTest(case=case, spelling=spelling):
                    if spelling == 'bare' and any(sum(1 for p in known if Path(p).name == Path(d['file']).name) != 1
                                                  for d in defects):
                        continue

                    def review(workspace, spelling=spelling):
                        def spell(path):
                            return {'./': './' + path, 'b/': 'b/' + path, 'absolute': str(workspace / path),
                                    'bare': Path(path).name}[spelling]
                        return blocking_review(*[(spell(d['file']), d['start_line']) for d in defects])
                    self.assertTrue(grade(case, review)['passed'])

    def test_anywhere_in_the_enclosing_function_passes(self):
        probed = 0
        for case in defect_cases():
            defects = defects_of(case)
            for index, defect in enumerate(defects):
                source = (HERE / case / 'fixture' / defect['file']).read_text(encoding='utf-8')
                first, last = G.function_span(source, defect['function'], defect['start_line'], defect['end_line'])
                if first >= defect['start_line'] - G.WINDOW:
                    continue
                probed += 1
                others = [(d['file'], d['start_line']) for d in defects if d is not defect]
                with self.subTest(case=case, defect=defect['id']):
                    result = grade(case, blocking_review((defect['file'], first), *others))
                    self.assertTrue(result['passed'], result)
                    self.assertEqual(result['metrics']['defects_found_strict'], len(defects) - 1)
                    # A line just past the function earns no credit, unless that number
                    # read as a diff line lands back inside an accepted location.
                    fixture = HERE / case / 'fixture'
                    by_diff = G.diff_line_map((fixture / 'change.diff').read_text(encoding='utf-8'))
                    accepted = [(defect['file'], first, last)] + [
                        (s['file'], s['start_line'], s['end_line']) for s in defect.get('also_accept', [])]
                    mapped = by_diff.get(last + 1)
                    lands_inside = bool(mapped) and any(
                        mapped[0] == f and lo <= mapped[1] <= hi for f, lo, hi in accepted)
                    in_accepted = any(defect['file'] == f and lo <= last + 1 <= hi for f, lo, hi in accepted)
                    if last + 1 <= len(source.splitlines()) and not lands_inside and not in_accepted:
                        outside = grade(case, blocking_review((defect['file'], last + 1), *others))
                        self.assertNotIn(defect['id'], outside['metrics']['found_ids'])
        self.assertGreater(probed, 0)

    def test_a_diff_line_number_valid_as_a_file_line_still_matches(self):
        probed = 0
        for case in defect_cases():
            fixture = HERE / case / 'fixture'
            by_diff = G.diff_line_map((fixture / 'change.diff').read_text(encoding='utf-8'))
            oracle = review_of(case, 'oracle')
            renumbered = []
            for item in oracle['findings']:
                length = len((fixture / item['file']).read_text(encoding='utf-8').splitlines())
                cited = [number for number, (path, line) in by_diff.items()
                         if path == item['file'] and line == item['line'] and number <= length and number != line]
                renumbered.append(dict(item, line=cited[0]) if cited else item)
                probed += bool(cited)
            with self.subTest(case=case):
                self.assertTrue(grade(case, dict(oracle, findings=renumbered))['passed'])
        self.assertGreater(probed, 0)

    def test_strict_metric_uses_the_window(self):
        for case in defect_cases():
            defect = defects_of(case)[0]
            length = len((HERE / case / 'fixture' / defect['file']).read_text(encoding='utf-8').splitlines())
            with self.subTest(case=case):
                for line in (defect['start_line'] - G.WINDOW, defect['end_line'] + G.WINDOW):
                    if 1 <= line <= length:
                        result = grade(case, blocking_review((defect['file'], line)))
                        self.assertIn(defect['id'], result['metrics']['strict_ids'], line)

    def test_nonblocking_finding_at_a_defect_does_not_count(self):
        for case in defect_cases():
            defect = defects_of(case)[0]
            with self.subTest(case=case):
                review = {'verdict': 'approve', 'findings': [finding(defect['file'], defect['start_line'], blocking=False)]}
                result = grade(case, review)
                self.assertFalse(result['passed'])
                self.assertEqual((result['metrics']['blocking'], result['metrics']['defects_found']), (0, 0))

    def test_also_accept_spans_count(self):
        for case in defect_cases():
            defects = defects_of(case)
            for defect in defects:
                others = [(d['file'], d['start_line']) for d in defects if d is not defect]
                for span in defect['also_accept']:
                    with self.subTest(case=case, defect=defect['id'], span=span):
                        result = grade(case, blocking_review((span['file'], span['end_line']), *others))
                        self.assertTrue(result['passed'], result)

    def test_a_review_missing_one_defect_fails(self):
        for case in multi_cases():
            defects = defects_of(case)
            for missing in defects:
                anchors = [(d['file'], d['start_line']) for d in defects if d is not missing]
                with self.subTest(case=case, missing=missing['id']):
                    result = grade(case, blocking_review(*anchors))
                    self.assertFalse(result['passed'])
                    self.assertIs(result['checks']['all_defects_found'], False)
                    self.assertEqual(result['metrics']['defects_found'], len(defects) - 1)
                    self.assertNotIn(missing['id'], result['metrics']['found_ids'])

    def test_one_finding_counts_toward_one_defect_only(self):
        spans = [{'file': 'a.py', 'start_line': 10, 'end_line': 12}, {'file': 'a.py', 'start_line': 11, 'end_line': 14}]
        matches = lambda finding_, span: G.in_span(finding_, span)
        self.assertEqual(G.max_matching([{'file': 'a.py', 'line': 11}], spans, matches), [0])
        both = [{'file': 'a.py', 'line': 11}, {'file': 'a.py', 'line': 10}]
        self.assertEqual(G.max_matching(both, spans, matches), [0, 1])
        for case in multi_cases():
            defect = defects_of(case)[0]
            with self.subTest(case=case):
                twice = blocking_review((defect['file'], defect['start_line']), (defect['file'], defect['end_line']))
                self.assertEqual(grade(case, twice)['metrics']['defects_found'], 1)

    def test_diff_line_numbers_past_the_end_of_a_file_are_read_as_diff_lines(self):
        probed = 0
        for case in defect_cases():
            fixture = HERE / case / 'fixture'
            mapping = G.diff_line_map((fixture / 'change.diff').read_text(encoding='utf-8'))
            defects = defects_of(case)
            for defect in defects:
                length = len((fixture / defect['file']).read_text(encoding='utf-8').splitlines())
                numbers = [n for n, (path, line) in mapping.items()
                           if path == defect['file'] and line == defect['start_line'] and n > length]
                if not numbers:
                    continue
                probed += 1
                others = [(d['file'], d['start_line']) for d in defects if d is not defect]
                with self.subTest(case=case, defect=defect['id']):
                    result = grade(case, blocking_review((defect['file'], numbers[0]), *others))
                    self.assertTrue(result['passed'], result)
                    self.assertEqual(result['metrics']['diff_line_anchors'], 1)
        self.assertGreater(probed, 0)

    def test_diff_line_map(self):
        text = ('diff --git a/x.py b/x.py\nindex 1..2 100644\n--- a/x.py\n+++ b/x.py\n'
                '@@ -3,3 +3,4 @@ def f():\n a\n-b\n+c\n+d\n e\n'
                'diff --git a/new.py b/new.py\nnew file mode 100644\n--- /dev/null\n+++ b/new.py\n@@ -0,0 +1 @@\n+z\n')
        mapping = G.diff_line_map(text)
        self.assertEqual([mapping.get(n) for n in range(1, 17)],
                         [None, None, None, None, ('x.py', 3), ('x.py', 3), ('x.py', 4), ('x.py', 4), ('x.py', 5),
                          ('x.py', 6), None, None, None, None, ('new.py', 1), ('new.py', 1)])

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
            twin_defect = defects_of(load(case)['twin'])[0]
            with self.subTest(case=case):
                soft = {'verdict': 'approve', 'findings': [finding(twin_defect['file'], twin_defect['start_line'], blocking=False)]}
                self.assertTrue(grade(case, soft)['passed'])
                result = grade(case, blocking_review((twin_defect['file'], twin_defect['start_line'])))
                self.assertFalse(result['passed'])
                self.assertEqual(result['metrics']['other_blocking'], 1)

    def test_diff_file_parser(self):
        text = ('diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n'
                'diff --git a/new.py b/new.py\n--- /dev/null\n+++ b/new.py\n'
                'diff --git a/gone.py b/gone.py\n--- a/gone.py\n+++ /dev/null\n')
        self.assertEqual(G.diff_files(text), {'x.py', 'new.py', 'gone.py'})


if __name__ == '__main__':
    unittest.main()
