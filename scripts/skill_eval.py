#!/usr/bin/env python3
"""Plan, execute, and summarize paired skill trials using explicit adapters."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import time

ARMS = ('baseline', 'explicit', 'discovery')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def digest(path):
    path = Path(path)
    h = hashlib.sha256()
    files = sorted(path.rglob('*')) if path.is_dir() else [path]
    for file in files:
        if file.is_symlink() and path.is_dir():
            raise ValueError(f'symlink not allowed in input: {file}')
        if file.is_file():
            h.update(str(file.relative_to(path) if path.is_dir() else file.name).encode())
            h.update(b'\0')
            if file.is_symlink():
                h.update(os.readlink(file).encode())
            h.update(file.read_bytes())
    return h.hexdigest()


def command(argv, base):
    if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or not x for x in argv):
        raise ValueError('commands must be nonempty string argv arrays')
    return [str((base / x).absolute()) if (base / x).is_file() else x for x in argv]


def suite(path):
    path = Path(path).resolve()
    data = read(path)
    if data.get('version') != 1 or not isinstance(data.get('name'), str):
        raise ValueError('suite needs version 1 and name')
    base = path.parent
    root = (base / data['skills_root']).resolve()
    if not root.is_dir():
        raise ValueError('skills_root must exist')
    data['skills_root'] = str(root)
    for collection in ('tasks', 'configurations'):
        if not isinstance(data.get(collection), list):
            raise ValueError(f'{collection} must be an array')
        ids = [x['id'] for x in data[collection]]
        if len(ids) != len(set(ids)) or any(not isinstance(x, str) or not x for x in ids):
            raise ValueError(f'{collection} needs unique nonempty ids')
    if not data['tasks']:
        raise ValueError('tasks cannot be empty')
    for task in data['tasks']:
        if task['split'] not in ('development', 'holdout') or not task.get('family'):
            raise ValueError('task needs family and development/holdout split')
        for key in ('prompt', 'fixture'):
            target = (base / task[key]).resolve()
            if not (target.is_file() if key == 'prompt' else target.is_dir()):
                raise ValueError(f'invalid {key}: {target}')
            task[key] = str(target)
        if not isinstance(task['skills'], list) or not task['skills']:
            raise ValueError('task skills must be a nonempty list')
        for name in task['skills']:
            if not isinstance(name, str) or Path(name).name != name or not (root / name / 'SKILL.md').is_file():
                raise ValueError(f'invalid skill: {name}')
        task['grader'] = command(task['grader'], base)
        dependencies = task.get('grader_inputs', [])
        if not isinstance(dependencies, list) or any(not isinstance(x, str) for x in dependencies):
            raise ValueError('grader_inputs must be a list of paths')
        task['grader_inputs'] = [str((base / x).absolute()) for x in dependencies]
        if any(not Path(x).exists() for x in task['grader_inputs']):
            raise ValueError('grader_inputs must exist')
    for config in data['configurations']:
        if not config.get('model') or not config.get('harness'):
            raise ValueError('configuration needs pinned model and harness identities')
        config['adapter'] = command(config['adapter'], base)
    return data


def inputs(data):
    paths = {data['skills_root']}
    for task in data['tasks']:
        paths.update([task['prompt'], task['fixture']])
        paths.update(task.get('grader_inputs', []))
        paths.update(x for x in task['grader'] if Path(x).is_file())
    for config in data['configurations']:
        paths.update(x for x in config['adapter'] if Path(x).is_file())
    return {x: digest(x) for x in sorted(paths)}


def plan(path, output, repeats=3, seed=0, split='development'):
    if repeats < 1:
        raise ValueError('repeats must be positive')
    data = suite(path)
    if not data['configurations']:
        raise ValueError('configure at least one adapter before planning')
    tasks = [t for t in data['tasks'] if t['split'] == split]
    if not tasks:
        raise ValueError('no tasks in selected split')
    trials = []
    for config in data['configurations']:
        for task in tasks:
            for repeat in range(repeats):
                for arm in ARMS:
                    trials.append({'configuration': config['id'], 'task': task['id'], 'repeat': repeat, 'arm': arm})
    random.Random(seed).shuffle(trials)
    for index, trial in enumerate(trials):
        trial['id'] = f'{index:06d}'
    result = {'version': 1, 'suite': data, 'hashes': inputs(data), 'seed': seed, 'split': split, 'trials': trials}
    with Path(output).open('x') as stream:
        json.dump(result, stream, indent=2)
    return result


def invoke(argv, cwd, env, prefix):
    start = time.monotonic()
    try:
        with Path(str(prefix) + '.stdout').open('w') as out, Path(str(prefix) + '.stderr').open('w') as err:
            process = subprocess.run(argv, cwd=cwd, env=env, stdout=out, stderr=err, check=False)
        return {'exit_code': process.returncode, 'elapsed_seconds': time.monotonic() - start}
    except OSError as exc:
        return {'exit_code': None, 'elapsed_seconds': time.monotonic() - start, 'error': str(exc)}


def run(path, output):
    frozen = read(path)
    if inputs(frozen['suite']) != frozen['hashes']:
        raise ValueError('inputs changed after plan; create a new plan')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'plan.json', frozen)
    tasks = {x['id']: x for x in frozen['suite']['tasks']}
    configs = {x['id']: x for x in frozen['suite']['configurations']}
    for trial in frozen['trials']:
        directory = output / trial['id']
        directory.mkdir()
        try:
            unchanged = inputs(frozen['suite']) == frozen['hashes']
        except (OSError, ValueError):
            unchanged = False
        if not unchanged:
            write(directory / 'result.json', {**trial, 'status': 'input_changed', 'passed': None, 'cost_usd': None, 'tokens': None})
            break
        workspace = directory / 'workspace'
        task, config = tasks[trial['task']], configs[trial['configuration']]
        shutil.copytree(task['fixture'], workspace)
        home = directory / 'home'
        home.mkdir()
        skills = directory / 'skills'
        skills.mkdir()
        root = Path(frozen['suite']['skills_root'])
        selected = [] if trial['arm'] == 'baseline' else task['skills']
        if trial['arm'] == 'discovery':
            selected = [x.name for x in root.iterdir() if (x / 'SKILL.md').is_file()]
        for name in selected:
            shutil.copytree(root / name, skills / name)
        prompt = directory / 'prompt.txt'
        prompt.write_text(Path(task['prompt']).read_text())
        request = {'version': 1, **trial, 'workspace': str(workspace), 'home': str(home), 'skills': str(skills), 'prompt': str(prompt), 'configuration': config, 'metrics': str(directory / 'metrics.json'), 'exposure': 'preload' if trial['arm'] == 'explicit' else 'discover', 'isolation': 'Adapter must enforce external sandbox and disable ambient skills/config/memory; cwd and HOME alone are not isolation.'}
        write(directory / 'request.json', request)
        env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'), XDG_CACHE_HOME=str(home / '.cache'))
        result = {**trial, 'adapter': invoke(config['adapter'] + [str(directory / 'request.json')], workspace, env, directory / 'adapter'), 'status': 'adapter_error', 'passed': None, 'cost_usd': None, 'tokens': None}
        if result['adapter']['exit_code'] == 0:
            result['grader'] = invoke(task['grader'] + [str(workspace)], directory, os.environ.copy(), directory / 'grader')
            try:
                grade = read(directory / 'grader.stdout')
                if result['grader']['exit_code'] != 0 or not isinstance(grade, dict) or type(grade.get('passed')) is not bool:
                    raise ValueError('grader must exit zero and emit boolean passed')
                result['grade'] = grade
                result['passed'] = grade['passed']
                result['status'] = 'valid'
            except (ValueError, OSError) as exc:
                result['grading_error'] = str(exc)
                result['status'] = 'grading_error'
        if (directory / 'metrics.json').exists():
            try:
                metrics = read(directory / 'metrics.json')
                if not isinstance(metrics, dict):
                    raise ValueError('metrics must be an object')
                result['reported_metrics'] = metrics
                for key in ('cost_usd', 'tokens'):
                    value = metrics.get(key)
                    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0 and value < float('inf'):
                        result[key] = value
            except (ValueError, OSError) as exc:
                result['metrics_error'] = str(exc)
        try:
            unchanged = inputs(frozen['suite']) == frozen['hashes']
        except (OSError, ValueError):
            unchanged = False
        if not unchanged:
            result['status'], result['passed'] = 'input_changed', None
        write(directory / 'result.json', result)
        if not unchanged:
            break


def summary_rows(groups):
    rows = []
    for (config, arm, family), tasks in sorted(groups.items()):
        deltas = {task: statistics.mean(values) for task, values in tasks.items()}
        values = list(deltas.values())
        interval = None
        if len(values) > 1:
            rng = random.Random(0)
            samples = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(2000))
            interval = [samples[49], samples[1949]]
        rows.append({'configuration': config, 'arm': arm, 'family': family, 'task_deltas': deltas,
                     'mean_delta': statistics.mean(values), 'task_bootstrap_95_interval': interval})
    return rows


def outcomes(directory, plan):
    return {(t['configuration'], t['task'], t['repeat'], t['arm']): read(Path(directory) / t['id'] / 'result.json')
            for t in plan['trials'] if (Path(directory) / t['id'] / 'result.json').is_file()}


def metadata(rows):
    versions = {r.get('reported_metrics', {}).get('cli_version') for r in rows}
    models = {tuple(sorted((r.get('reported_metrics', {}).get('served_models') or []))) for r in rows}
    return {'cli_versions': sorted(v for v in versions if v), 'served_models': sorted(set(m for group in models for m in group)),
            'unknown': not rows or None in versions or () in models}


def report(path):
    directory = Path(path)
    frozen = read(directory / 'plan.json')
    results = outcomes(directory, frozen)
    families = {t['id']: t['family'] for t in frozen['suite']['tasks']}
    groups, excluded = {}, []
    for config in frozen['suite']['configurations']:
        for arm in ARMS[1:]:
            missing = invalid = 0
            for trial in frozen['trials']:
                if trial['configuration'] != config['id'] or trial['arm'] != arm:
                    continue
                key = (config['id'], trial['task'], trial['repeat'])
                treated, baseline = results.get((*key, arm)), results.get((*key, 'baseline'))
                if treated is None or baseline is None:
                    missing += 1
                elif treated.get('status') != 'valid' or baseline.get('status') != 'valid':
                    invalid += 1
                else:
                    groups.setdefault((config['id'], arm, families[trial['task']]), {}).setdefault(trial['task'], []).append(int(treated['passed']) - int(baseline['passed']))
            excluded.append({'configuration': config['id'], 'arm': arm, 'missing_pairs': missing, 'invalid_pairs': invalid})
    resources = []
    for config in frozen['suite']['configurations']:
        for arm in ARMS:
            rows = [r for r in results.values() if r['configuration'] == config['id'] and r['arm'] == arm]
            costs = [r['cost_usd'] for r in rows]
            statuses = {status: sum(r.get('status') == status for r in rows) for status in ('valid', 'adapter_error', 'grading_error', 'input_changed')}
            resources.append({'configuration': config['id'], 'arm': arm, 'completed': len(rows), 'status_counts': statuses,
                              'pending_human_review': sum(bool(r.get('grade', {}).get('requires_human_review', False)) for r in rows),
                              'cost_usd': sum(costs) if costs and all(c is not None for c in costs) else None,
                              'adapter_elapsed_seconds': sum(r.get('adapter', {}).get('elapsed_seconds', 0) for r in rows),
                              'metadata': metadata(rows)})
    return {'resources': resources, 'task_families': families, 'completed': len(results), 'planned': len(frozen['trials']),
            'missing_cost_records': sum(x['cost_usd'] is None for x in results.values()), 'comparisons': summary_rows(groups), 'excluded_pairs': excluded,
            'configurations': [{'id': c['id'], 'harness': c['harness'], 'evidence_class': c.get('settings', {}).get('purpose', 'unclassified')} for c in frozen['suite']['configurations']],
            'scope': 'Deterministic checks only; pending human review is not a final quality verdict.',
            'interpretation': 'Descriptive family-level estimates, not proof of efficacy or equivalence. Infrastructure-invalid attempts are excluded and counted. Missing metadata is unknown, not a pinned model claim.'}


def compare(incumbent, candidate):
    """Compare skill revisions only when the non-skill experiment is unchanged."""
    left, right = [read(Path(p) / 'plan.json') for p in (incumbent, candidate)]
    def signature(plan):
        return {'suite': {k: v for k, v in plan['suite'].items() if k != 'skills_root'},
                'hashes': {k: v for k, v in plan['hashes'].items() if k != plan['suite']['skills_root']},
                'split': plan['split'],
                'trials': sorted((t['configuration'], t['task'], t['repeat'], t['arm']) for t in plan['trials'])}
    if signature(left) != signature(right):
        raise ValueError('comparison requires identical non-skill inputs, configurations and trial coverage')
    old, new = outcomes(incumbent, left), outcomes(candidate, right)
    families = {t['id']: t['family'] for t in left['suite']['tasks']}
    groups, invalid, unknown = {}, 0, []
    for config in left['suite']['configurations']:
        old_meta = metadata([r for k, r in old.items() if k[0] == config['id']])
        new_meta = metadata([r for k, r in new.items() if k[0] == config['id']])
        for field in ('cli_versions', 'served_models'):
            if old_meta[field] and new_meta[field] and old_meta[field] != new_meta[field]:
                raise ValueError(f'observed {field} differ between runs')
        if old_meta['unknown'] or new_meta['unknown']:
            unknown.append(config['id'])
    for key in old.keys() & new.keys():
        config, task, repeat, arm = key
        for field in ('cli_version', 'served_models'):
            old_value = old[key].get('reported_metrics', {}).get(field)
            new_value = new[key].get('reported_metrics', {}).get(field)
            if old_value and new_value and old_value != new_value:
                raise ValueError(f'observed {field} differ in paired trials')
        if old[key].get('status') != 'valid' or new[key].get('status') != 'valid':
            invalid += 1
            continue
        groups.setdefault((config, arm, families[task]), {}).setdefault(task, []).append(int(new[key]['passed']) - int(old[key]['passed']))
    return {'direction': 'candidate minus incumbent', 'comparisons': summary_rows(groups), 'invalid_pairs': invalid,
            'missing_pairs': len(left['trials']) - len(old.keys() & new.keys()), 'unknown_metadata_configurations': unknown,
            'scope': 'Deterministic family-level exploratory results; not efficacy evidence when metadata is unknown or adapters are synthetic.',
            'incumbent_resources': report(incumbent)['resources'], 'candidate_resources': report(candidate)['resources']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    validate = sub.add_parser('validate')
    validate.add_argument('suite')
    create = sub.add_parser('plan')
    create.add_argument('suite')
    create.add_argument('--output', required=True)
    create.add_argument('--repeats', type=int, default=3)
    create.add_argument('--seed', type=int, default=0)
    create.add_argument('--split', choices=['development', 'holdout'], default='development')
    execute = sub.add_parser('run')
    execute.add_argument('plan')
    execute.add_argument('--output', required=True)
    summarize = sub.add_parser('report')
    summarize.add_argument('run')
    comparison = sub.add_parser('compare')
    comparison.add_argument('incumbent')
    comparison.add_argument('candidate')
    args = parser.parse_args()
    try:
        if args.action == 'validate':
            suite(args.suite)
            print('Suite valid')
        elif args.action == 'plan':
            plan(args.suite, args.output, args.repeats, args.seed, args.split)
        elif args.action == 'run':
            run(args.plan, args.output)
        elif args.action == 'compare':
            print(json.dumps(compare(args.incumbent, args.candidate), indent=2))
        else:
            print(json.dumps(report(args.run), indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, f'error: {exc}\n')


if __name__ == '__main__':
    main()
