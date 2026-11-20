"""Grade one review case against its case.json.

Usage: grade.py CASE WORKSPACE. Prints one JSON object. A defect case passes when a
blocking finding anchors at the defect; a clean case passes when nothing blocks.
Neither proves the reviewer understood the change; see README.md.
"""
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WINDOW = 3
VERDICTS = ('approve', 'needs_changes')
TEXT_FIELDS = ('title', 'trigger', 'impact')
SCRATCH = {'__pycache__', '.pytest_cache'}


class Unreadable(Exception):
    pass


def tree_files(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob('*')
                  if p.is_file() and not SCRATCH.intersection(p.relative_to(root).parts))


def diff_files(diff_text):
    """Paths a unified diff touches, from its ---/+++ headers."""
    paths = set()
    for line in diff_text.splitlines():
        if line.startswith(('--- ', '+++ ')):
            path = line[4:].split('\t')[0].strip()
            if path != '/dev/null':
                paths.add(path[2:] if path.startswith(('a/', 'b/')) else path)
    return paths


def function_span(source, name, start, end):
    """Lines of the innermost function called name that encloses start..end, decorators included."""
    best = None
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            first = min([node.lineno] + [d.lineno for d in node.decorator_list])
            if first <= start and node.end_lineno >= end and (best is None or node.end_lineno - first < best[1] - best[0]):
                best = (first, node.end_lineno)
    if best is None:
        raise ValueError(f'no function {name} encloses lines {start}-{end}')
    return best


def normalize_path(raw, workspace, known):
    """Map a reviewer's file string onto a tree path: tolerate ./, a/ or b/, the absolute
    workspace prefix, and a bare name that matches exactly one tree file."""
    text = raw.strip().replace('\\', '/')
    for root in {str(workspace), str(workspace.resolve())}:
        if text.startswith(root.rstrip('/') + '/'):
            text = text[len(root.rstrip('/')) + 1:]
    while text.startswith('./'):
        text = text[2:]
    if text in known:
        return text
    if text.startswith(('a/', 'b/')) and text[2:] in known:
        return text[2:]
    suffix = [path for path in known if path.endswith('/' + text)]
    return suffix[0] if len(suffix) == 1 else text


def finding_problems(finding):
    if not isinstance(finding, dict):
        return ['is not an object']
    problems = []
    if not isinstance(finding.get('file'), str) or not finding['file'].strip():
        problems.append('file must be a nonempty string')
    if type(finding.get('line')) is not int or finding['line'] < 1:
        problems.append('line must be a positive integer')
    if type(finding.get('blocking')) is not bool:
        problems.append('blocking must be true or false')
    for key in TEXT_FIELDS:
        if not isinstance(finding.get(key), str):
            problems.append(f'{key} must be a string')
    if isinstance(finding.get('title'), str) and not finding['title'].strip():
        problems.append('title must not be empty')
    if finding.get('blocking') is True and any(not str(finding.get(k) or '').strip() for k in ('trigger', 'impact')):
        problems.append('a blocking finding needs a trigger and an impact')
    return problems


def shape_problems(review):
    if not isinstance(review, dict):
        return ['review.json must hold an object']
    problems = []
    if review.get('verdict') not in VERDICTS:
        problems.append('verdict must be "approve" or "needs_changes"')
    findings = review.get('findings')
    if not isinstance(findings, list):
        return problems + ['findings must be a list']
    for index, finding in enumerate(findings):
        problems.extend(f'findings[{index}] {problem}' for problem in finding_problems(finding))
    return problems


def read_review(workspace):
    path = workspace / 'review.json'
    if not path.is_file():
        raise Unreadable(f'review.json is missing from the workspace ({workspace})')
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise Unreadable(f'review.json is not readable JSON: {error}') from error


def in_span(finding, span, window=0):
    return (finding['file'] == span['file']
            and span['start_line'] - window <= finding['line'] <= span['end_line'] + window)


def evaluate(case, fixture, workspace, review):
    known = tree_files(fixture)
    touched = diff_files((fixture / 'change.diff').read_text(encoding='utf-8'))
    raw = review.get('findings') if isinstance(review, dict) else None
    findings = [dict(f, file=normalize_path(f['file'], workspace, known))
                for f in (raw if isinstance(raw, list) else []) if not finding_problems(f)]
    blocking = [f for f in findings if f['blocking']]
    accept = case.get('also_accept') or []
    defect = case.get('defect')

    def matches(finding):
        return defect is not None and (in_span(finding, defect, WINDOW) or any(in_span(finding, s) for s in accept))

    checks, metrics = {}, {
        'verdict': review.get('verdict') if isinstance(review, dict) else None,
        'findings': len(findings),
        'blocking': len(blocking),
        'other_blocking': sum(1 for f in blocking if not matches(f)),
        'nonblocking': len(findings) - len(blocking),
        'anchors_outside_diff': any(f['file'] not in touched for f in findings),
        'unknown_files': sorted({f['file'] for f in findings if f['file'] not in known}),
    }
    if case['kind'] == 'defect':
        checks['defect_found_strict'] = any(matches(f) for f in blocking)
        source = (fixture / defect['file']).read_text(encoding='utf-8')
        first, last = function_span(source, defect['function'], defect['start_line'], defect['end_line'])
        enclosing = dict(defect, start_line=first, end_line=last)
        metrics['defect_found_loose'] = any(in_span(f, enclosing) or any(in_span(f, s) for s in accept) for f in blocking)
    else:
        checks['no_blocking_findings'] = not blocking
    return checks, metrics


def main():
    checks, metrics, case = {}, {}, {}
    try:
        if len(sys.argv) != 3:
            raise ValueError('usage: grade.py CASE WORKSPACE')
        name, workspace = sys.argv[1], Path(sys.argv[2])
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or not (HERE / name / 'case.json').is_file():
            raise ValueError(f'unknown case: {name}')
        case = json.loads((HERE / name / 'case.json').read_text(encoding='utf-8'))
        if case.get('kind') not in ('defect', 'clean'):
            raise ValueError(f'case.json kind must be "defect" or "clean", got {case.get("kind")!r}')
        fixture = HERE / name / 'fixture'
        checks['fixture_unchanged'] = all(
            (workspace / path).is_file() and (workspace / path).read_bytes() == (fixture / path).read_bytes()
            for path in tree_files(fixture))
        metrics['extra_files'] = sorted(set(tree_files(workspace)) - set(tree_files(fixture)) - {'review.json'})
        review = read_review(workspace)
        checks['review_readable'] = True
        problems = shape_problems(review)
        checks['review_shape'] = not problems
        found_checks, found_metrics = evaluate(case, fixture, workspace, review)
        checks.update(found_checks)
        metrics.update(found_metrics)
        if problems:
            checks['error'] = '; '.join(problems[:5])
    except Unreadable as error:
        checks['review_readable'] = False
        checks['error'] = str(error)
    except Exception as error:
        checks['grader_completed'] = False
        checks['error'] = f'{type(error).__name__}: {error}'
    flags = {key: value for key, value in checks.items() if key != 'error'}
    passed = (bool(flags) and all(value is True for value in flags.values())
              and ('defect_found_strict' in flags or 'no_blocking_findings' in flags))
    print(json.dumps({
        'passed': passed,
        'checks': checks,
        'metrics': metrics,
        'case': {key: case.get(key) for key in ('kind', 'class', 'split', 'twin')},
        'trap': case.get('trap'),
        'grading_scope': 'deterministic-anchor-only',
        'requires_human_review': True,
    }))


if __name__ == '__main__':
    main()
