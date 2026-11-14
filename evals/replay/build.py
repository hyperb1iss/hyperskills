#!/usr/bin/env python3
"""Turn fix commits from a local clone into replay cases.

validate     run each commit's tests before and after the fix, inside the
             pinned image, and record which tests the fix turns green
materialize  export the pre-fix trees and hidden tests, and write a manifest

The target repository's source is exported into an ignored directory. Only
commit identities, test names, and task prompts live in this repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'scripts'))
from eval_container import execute, image_identity, mount  # noqa: E402


def git(repo, *args, binary=False):
    done = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, check=True)
    return done.stdout if binary else done.stdout.decode()


def export(repo, revision, paths, destination):
    """Write the listed paths of one revision; a path absent there is skipped."""
    destination.mkdir(parents=True)
    present = [p for p in paths if subprocess.run(['git', '-C', str(repo), 'cat-file', '-e', f'{revision}:{p}'],
                                                  capture_output=True).returncode == 0]
    archive = subprocess.run(['git', '-C', str(repo), 'archive', revision, *present], capture_output=True, check=True)
    subprocess.run(['tar', '-x', '-C', str(destination)], input=archive.stdout, check=True)


def changed_tests(repo, sha):
    names = git(repo, 'show', '--name-only', '--diff-filter=AM', '--format=', sha).split()
    return sorted(n for n in names if '/tests/' in n and Path(n).name.startswith('test_') and n.endswith('.py'))


def project_of(tests):
    roots = {path.split('/tests/')[0] for path in tests}
    if len(roots) != 1:
        raise ValueError(f'tests span several projects: {sorted(roots)}')
    return roots.pop()


def case_record(suite, repo, entry, fixture):
    project = project_of(entry['tests'])
    base = fixture / project / 'tests'
    hashes = {str(p.relative_to(fixture)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(base.rglob('*.py'))}
    # A project's test environment applies only where the file it needs exists.
    setup = suite.get('project_env', {}).get(project, {})
    env = setup.get('env', {}) if (fixture / setup.get('requires', '')).exists() else {}
    return {'project': project, 'tests': entry['tests'], 'python': suite['python'],
            'source_roots': suite['source_roots'], 'env': env,
            'fail_to_pass': entry.get('fail_to_pass', []), 'pass_to_pass': entry.get('pass_to_pass', []),
            'fixture_test_hashes': hashes}


def write_case(suite, repo, entry, destination):
    """Lay out fixture/ (the tree before the fix) and case/ (private grading inputs)."""
    fixture, private = destination / 'fixture', destination / 'case'
    export(repo, entry['sha'] + '^', suite['paths'], fixture)
    for path in entry['tests']:
        target = private / 'hidden' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git(repo, 'show', f"{entry['sha']}:{path}", binary=True))
    (private / 'case.json').write_text(json.dumps(case_record(suite, repo, entry, fixture), indent=1) + '\n')
    return fixture, private


def outcomes(image, private, tree):
    mounts = [mount(tree, '/workspace'), mount(HERE / 'grade.py', '/grader/grade.py'), mount(private, '/grader/case')]
    code, out, err = execute(image, mounts, ['python3', '/grader/grade.py', '--outcomes', '/grader/case/case.json', '/workspace'],
                             network=False)
    if code:
        raise ValueError(f'grader exited {code}: {err[-800:]}')
    return json.loads(out)


def validate(args):
    suite = json.loads(Path(args.suite).read_text())
    image = image_identity(args.image)
    report = Path(args.output).open('x')

    def emit(record):
        # One line per commit, written as it lands, so a long sweep can be read midway.
        report.write(json.dumps(record) + '\n')
        report.flush()

    for sha in args.sha:
        sha = git(args.repo, 'rev-parse', sha).strip()
        entry = {'sha': sha, 'tests': changed_tests(args.repo, sha)}
        record = {'sha': sha, 'subject': git(args.repo, 'show', '-s', '--format=%s', sha).strip(), 'tests': entry['tests']}
        with tempfile.TemporaryDirectory(prefix='replay-validate-', dir=args.scratch) as scratch:
            try:
                fixture, private = write_case(suite, args.repo, entry, Path(scratch) / 'case')
                fixed = Path(scratch) / 'fixed'
                export(args.repo, sha, suite['paths'], fixed)
                before, after = outcomes(image, private, fixture), outcomes(image, private, fixed)
            except (ValueError, subprocess.CalledProcessError) as error:
                record['error'] = str(error)[-600:]
                emit(record)
                continue
        green = {name for name, state in after['outcomes'].items() if state == 'passed'}
        was_green = {name for name, state in before['outcomes'].items() if state == 'passed'}
        record.update(fail_to_pass=sorted(green - was_green), pass_to_pass=sorted(green & was_green),
                      not_green_after=sorted(set(after['outcomes']) - green))
        if not after['outcomes']:
            record['log'] = after['log'][-1500:]
        emit(record)


def materialize(args):
    suite_path = Path(args.suite).resolve()
    suite = json.loads(suite_path.read_text())
    out = Path(args.output).resolve()
    out.mkdir(parents=True)
    tasks = []
    for entry in suite['cases']:
        fixture, private = write_case(suite, args.repo, entry, out / 'cases' / entry['id'])
        tasks.append({'id': entry['id'], 'family': 'replay', 'split': entry.get('split', 'development'),
                      'prompt': str(suite_path.parent / 'prompts' / f"{entry['id']}.md"), 'fixture': str(fixture),
                      'skills': suite['skills'],
                      'grader': ['python3', str(HERE / 'grade.py'), str(private / 'case.json')],
                      'grader_inputs': [str(private / 'hidden')]})
    configurations = json.loads(Path(args.configurations).read_text())
    manifest = {'version': 1, 'name': args.name, 'skills_root': str(Path(args.skills).resolve()),
                'configurations': configurations, 'tasks': tasks}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(out / 'manifest.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--suite', default=str(HERE / 'suite.json'))
    parser.add_argument('--repo', required=True, help='local clone of the target repository')
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('validate')
    check.add_argument('--image', required=True)
    check.add_argument('--output', required=True)
    check.add_argument('--scratch', default=None)
    check.add_argument('sha', nargs='+')
    check.set_defaults(run=validate)
    build = commands.add_parser('materialize')
    build.add_argument('--output', required=True)
    build.add_argument('--skills', default=str(HERE.parents[1] / 'skills'))
    build.add_argument('--configurations', required=True, help='JSON list of manifest configurations')
    build.add_argument('--name', default='fix-replay')
    build.set_defaults(run=materialize)
    args = parser.parse_args()
    args.run(args)


if __name__ == '__main__':
    main()
