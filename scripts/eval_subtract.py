#!/usr/bin/env python3
"""Prepare one exact skill-section subtraction without changing source skills."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def hashes(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'symlinks are not supported in copied skill trees: {path}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def subtract(text: str, section: str) -> tuple[str, str]:
    heading = f'## {section}'
    matches = list(re.finditer(r'^' + re.escape(heading) + r'\r?$', text, re.MULTILINE))
    if len(matches) != 1:
        raise ValueError('section must identify exactly one level-two heading')
    start = matches[0].start()
    remaining = text[matches[0].end():]
    next_heading = re.search(r'^#{1,2} ', remaining, re.MULTILINE)
    end = matches[0].end() + next_heading.start() if next_heading else len(text)
    return text[:start] + text[end:], text[start:end]


def prepare(source: Path, output: Path, experiment_path: Path) -> dict:
    source, output = source.resolve(), output.resolve()
    if not source.is_dir():
        raise ValueError('source must be an existing skill tree')
    if source == output or source in output.parents or output in source.parents:
        raise ValueError('output and source must be separate directory trees')
    if output.exists():
        raise ValueError('output already exists; choose a fresh directory')
    experiment = json.loads(experiment_path.read_text())
    for key in ('skill', 'section', 'hypothesis'):
        if not isinstance(experiment.get(key), str) or not experiment[key].strip():
            raise ValueError(f'experiment needs nonempty {key}')
    skill = experiment['skill']
    if Path(skill).name != skill or skill in ('.', '..'):
        raise ValueError('skill must be one directory name')
    relative = f'{skill}/SKILL.md'
    before = hashes(source)
    if relative not in before:
        raise ValueError('selected skill entrypoint does not exist')
    original = (source / relative).read_bytes().decode('utf-8')
    candidate, removed = subtract(original, experiment['section'])
    output.mkdir(parents=True)
    copied = output / 'skills'
    shutil.copytree(source, copied)
    if hashes(copied) != before or hashes(source) != before:
        raise ValueError('source changed during copying; discard this incomplete candidate')
    (copied / relative).write_bytes(candidate.encode('utf-8'))
    after = hashes(copied)
    changed = [name for name in before if before[name] != after[name]]
    if changed != [relative]:
        raise ValueError('candidate must change exactly the requested entrypoint')
    receipt = {
        'version': 1, 'experiment': experiment,
        'source': str(source), 'skills_root': str(copied),
        'source_hashes': before, 'candidate_hashes': after,
        'changed_paths': changed,
        'removed_sha256': hashlib.sha256(removed.encode('utf-8')).hexdigest(),
        'status': 'prepared-not-evaluated',
    }
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('prepare')
    command.add_argument('--source', type=Path, required=True)
    command.add_argument('--output', type=Path, required=True)
    command.add_argument('--experiment', type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = prepare(args.source, args.output, args.experiment)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps({'skills_root': receipt['skills_root'], 'status': receipt['status'], 'changed_paths': receipt['changed_paths']}))


if __name__ == '__main__':
    main()
