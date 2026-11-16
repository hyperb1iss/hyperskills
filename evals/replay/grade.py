#!/usr/bin/env python3
"""Grade a replayed fix: run the fix commit's own tests against a submitted tree.

Usage: grade.py [--outcomes] CASE_JSON WORKSPACE

Beside case.json sits hidden/, the test files as the fix commit left them. The
workspace is copied to scratch first, because the grading mount is read-only
and the hidden tests must replace whatever the submission left at those paths.

When the case's fixture/ directory is also present, the tests the submission
wrote are run twice more: on the submitted tree, and on the tree before the fix
with only the submission's test files laid over it. A test that fails before
and passes after is a regression test for the fix.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

SKIP = shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', '.venv', 'node_modules')
TIMEOUT = 900


def outcomes_from_junit(text: str) -> dict[str, str]:
    """Map 'classname::name' to passed, failed, error, or skipped."""
    found = {}
    for case in ET.fromstring(text).iter('testcase'):
        key = f"{case.get('classname', '')}::{case.get('name', '')}"
        kinds = {child.tag for child in case}
        found[key] = next((kind for kind in ('error', 'failure', 'skipped') if kind in kinds), 'passed')
    return {key: {'failure': 'failed'}.get(value, value) for key, value in found.items()}


def verdict(case: dict, outcomes: dict[str, str]) -> dict:
    def passing(names):
        return [name for name in names if outcomes.get(name) == 'passed']

    fixed, kept = passing(case['fail_to_pass']), passing(case['pass_to_pass'])
    checks = {
        'fail_to_pass': len(fixed) == len(case['fail_to_pass']),
        'pass_to_pass': len(kept) == len(case['pass_to_pass']),
    }
    return {
        'passed': all(checks.values()),
        'checks': checks,
        'fail_to_pass_passed': len(fixed),
        'fail_to_pass_total': len(case['fail_to_pass']),
        'pass_to_pass_passed': len(kept),
        'pass_to_pass_total': len(case['pass_to_pass']),
        'not_passing': sorted(n for n in case['fail_to_pass'] + case['pass_to_pass'] if outcomes.get(n) != 'passed'),
    }


def test_file_hashes(root: Path, project: str) -> dict[str, str]:
    base = root / project / 'tests'
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(base.rglob('*.py')) if '__pycache__' not in path.parts}


def lay_over(source: Path, tree: Path, paths=None) -> None:
    """Copy files from source into tree at the same relative paths."""
    chosen = [source / path for path in paths] if paths is not None else sorted(source.rglob('*'))
    for item in chosen:
        if item.is_file():
            target = tree / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)


def pytest_outcomes(case: dict, tree: Path, tests: list[str], scratch: Path) -> tuple[dict[str, str], str]:
    """Run test files of the case's project inside tree; scratch must be new."""
    project = tree / case['project']
    report = scratch / 'junit.xml'
    home = scratch / 'home'
    home.mkdir(parents=True)
    env = {**os.environ, **case.get('env', {}), 'HOME': str(home), 'PYTHONDONTWRITEBYTECODE': '1',
           'PYTHONPATH': os.pathsep.join(str(tree / root) for root in case['source_roots'])}
    command = [case['python'], '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-o', 'junit_family=xunit1',
               f'--junitxml={report}', *[str(Path(path).relative_to(case['project'])) for path in tests]]
    try:
        done = subprocess.run(command, cwd=project, env=env, text=True, capture_output=True, timeout=TIMEOUT)
        log = done.stdout[-4000:] + done.stderr[-2000:]
    except subprocess.TimeoutExpired:
        return {}, f'pytest exceeded {TIMEOUT}s'
    return (outcomes_from_junit(report.read_text()) if report.is_file() else {}), log


def run_tests(case: dict, case_dir: Path, workspace: Path, scratch: Path) -> tuple[dict[str, str], str]:
    tree = scratch / 'tree'
    shutil.copytree(workspace, tree, ignore=SKIP, symlinks=True)
    lay_over(case_dir / 'hidden', tree)
    return pytest_outcomes(case, tree, case['tests'], scratch / 'hidden-run')


def own_test_verdict(before: dict[str, str], after: dict[str, str]) -> dict:
    """Sort the submission's passing tests by how they fared before the fix."""
    green = sorted(name for name, state in after.items() if state == 'passed')
    return {
        'ran': len(after),
        'fail_before_pass_after': [name for name in green if before.get(name) == 'failed'],
        'pass_before': sum(before.get(name) == 'passed' for name in green),
        # Collected only once the fix exists, or broken at setup before it: weaker evidence than an assertion.
        'not_runnable_before': [name for name in green if before.get(name) not in ('passed', 'failed')],
        'not_passing_after': sorted(name for name, state in after.items() if state != 'passed'),
    }


def run_own_tests(case: dict, fixture: Path, workspace: Path, scratch: Path, changed: list[str]) -> dict:
    """Run the test files the submission wrote, after the fix and before it."""
    modules = [path for path in changed if Path(path).name.startswith('test_')]
    if not modules:
        return own_test_verdict({}, {})
    submitted, unfixed = scratch / 'submitted', scratch / 'unfixed'
    shutil.copytree(workspace, submitted, ignore=SKIP, symlinks=True)
    shutil.copytree(fixture, unfixed, ignore=SKIP, symlinks=True)
    # Helpers and conftest edits travel with the tests; source files do not.
    lay_over(workspace, unfixed, changed)
    after, _ = pytest_outcomes(case, submitted, modules, scratch / 'after-run')
    before, _ = pytest_outcomes(case, unfixed, modules, scratch / 'before-run')
    return own_test_verdict(before, after)


def main() -> int:
    args = sys.argv[1:]
    raw = bool(args and args[0] == '--outcomes')
    if raw:
        args = args[1:]
    if len(args) != 2:
        print('usage: grade.py [--outcomes] CASE_JSON WORKSPACE', file=sys.stderr)
        return 2
    case_file, workspace = Path(args[0]).resolve(), Path(args[1]).resolve()
    case_dir, case = case_file.parent, json.loads(case_file.read_text())
    before = case.get('fixture_test_hashes', {})
    after = test_file_hashes(workspace, case['project'])
    changed = sorted(path for path, digest in after.items() if before.get(path) != digest)
    fixture = case_dir.parent / 'fixture'
    with tempfile.TemporaryDirectory(prefix='replay-') as scratch:
        outcomes, log = run_tests(case, case_dir, workspace, Path(scratch))
        own = None if raw or not fixture.is_dir() else run_own_tests(case, fixture, workspace, Path(scratch), changed)
    if raw:
        print(json.dumps({'outcomes': outcomes, 'log': log}))
        return 0
    result = verdict(case, outcomes)
    # Observations only: neither field changes the verdict.
    result['submission_changed_tests'] = changed
    if own is not None:
        result['own_tests'] = own
        result['ships_regression_test'] = bool(own['fail_before_pass_after'])
    if not outcomes:
        result['log'] = log
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
