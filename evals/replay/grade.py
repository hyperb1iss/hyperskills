#!/usr/bin/env python3
"""Grade a replayed fix: run the fix commit's own tests against a submitted tree.

Usage: grade.py [--outcomes] CASE_JSON WORKSPACE

Beside case.json sits hidden/, the test files as the fix commit left them. The workspace is copied to scratch first, because the grading mount is
read-only and the hidden tests must replace whatever the submission left at
those paths.
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


def run_tests(case: dict, case_dir: Path, workspace: Path, scratch: Path) -> tuple[dict[str, str], str]:
    tree = scratch / 'tree'
    shutil.copytree(workspace, tree, ignore=SKIP, symlinks=True)
    for hidden in sorted((case_dir / 'hidden').rglob('*')):
        if hidden.is_file():
            target = tree / hidden.relative_to(case_dir / 'hidden')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(hidden, target)
    project = tree / case['project']
    report = scratch / 'junit.xml'
    home = scratch / 'home'
    home.mkdir()
    env = {**os.environ, **case.get('env', {}), 'HOME': str(home), 'PYTHONDONTWRITEBYTECODE': '1',
           'PYTHONPATH': os.pathsep.join(str(tree / root) for root in case['source_roots'])}
    tests = [str(Path(path).relative_to(case['project'])) for path in case['tests']]
    command = [case['python'], '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-o', 'junit_family=xunit1',
               f'--junitxml={report}', *tests]
    try:
        done = subprocess.run(command, cwd=project, env=env, text=True, capture_output=True, timeout=TIMEOUT)
        log = done.stdout[-4000:] + done.stderr[-2000:]
    except subprocess.TimeoutExpired:
        return {}, f'pytest exceeded {TIMEOUT}s'
    return (outcomes_from_junit(report.read_text()) if report.is_file() else {}), log


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
    with tempfile.TemporaryDirectory(prefix='replay-') as scratch:
        outcomes, log = run_tests(case, case_dir, workspace, Path(scratch))
    if raw:
        print(json.dumps({'outcomes': outcomes, 'log': log}))
        return 0
    result = verdict(case, outcomes)
    before = case.get('fixture_test_hashes', {})
    after = test_file_hashes(workspace, case['project'])
    # Observation only: whether the submission wrote or changed a test.
    result['submission_changed_tests'] = sorted(path for path, digest in after.items() if before.get(path) != digest)
    if not outcomes:
        result['log'] = log
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
