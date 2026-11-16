#!/usr/bin/env python3
"""Run one agent or grader invocation in an explicitly pinned local Docker image."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid


PIN = re.compile(r'(?:[^\s]+@)?sha256:[0-9a-f]{64}$')
CREDENTIALS = {'ANTHROPIC_API_KEY', 'CLAUDE_CODE_OAUTH_TOKEN'}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def docker(args, **kwargs):
    return subprocess.run(['docker', *args], text=True, capture_output=True, check=True, **kwargs)


def image_identity(image):
    if not isinstance(image, str) or not PIN.fullmatch(image):
        raise ValueError('container_image must be an immutable sha256 image ID or repository@sha256 digest')
    # Inspect never pulls. Absence is an explicit setup failure.
    identity = docker(['image', 'inspect', '--format', '{{.Id}}', image]).stdout.strip()
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', identity):
        raise ValueError('Docker did not report an immutable image identity')
    return identity


def mount(source, target, readonly=True):
    source = Path(source).resolve()
    if ',' in str(source) or ',' in target:
        raise ValueError('commas in bind mount paths are unsupported')
    if not source.exists():
        raise ValueError(f'mount input does not exist: {source}')
    return ['--mount', f'type=bind,src={source},dst={target}' + (',readonly' if readonly else '')]


def execute(image, mounts, command, credentials=(), network=True):
    """Remove only our uniquely named container, including interrupted executions."""
    if any(name not in CREDENTIALS for name in credentials):
        raise ValueError('only explicit Claude credential environment names can be forwarded')
    missing = [name for name in credentials if not os.environ.get(name)]
    if missing:
        raise ValueError('missing credential variables: ' + ', '.join(missing))
    name = 'hyperskills-eval-' + uuid.uuid4().hex
    args = ['create', '--name', name, '--pull', 'never', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--workdir', '/workspace',
            '--tmpfs', '/tmp:rw,nosuid,nodev', '--env', 'HOME=/home/agent',
            '--env', 'EVAL_INTERACTION_LOG=/interactions.json',
            '--env', 'XDG_CONFIG_HOME=/home/agent/.config', '--env', 'XDG_CACHE_HOME=/home/agent/.cache']
    if not network:
        args += ['--network', 'none']
    for variable in credentials:
        args += ['--env', variable]
    for entry in mounts:
        args += entry
    args += [image, *command]
    created = False
    try:
        docker(args)
        created = True
        result = subprocess.run(['docker', 'start', '--attach', name], text=True, capture_output=True, check=False)
        state = docker(['inspect', '--format', '{{.State.Status}}', name]).stdout.strip()
        if state not in ('exited', 'dead'):
            raise ValueError(f'container did not finish: {state}')
        status = int(docker(['wait', name]).stdout.strip())
        return status, result.stdout, result.stderr
    finally:
        if created:
            docker(['rm', '--force', name])


def run(request_path):
    request_path = Path(request_path).resolve()
    request = read(request_path)
    settings = request['configuration'].get('settings', {})
    image = settings.get('container_image')
    identity = image_identity(image)
    parent = request_path.parent
    transport = parent / 'container'
    inputs, outputs = [transport / name for name in ('inputs', 'outputs')]
    home = Path(request['home']).resolve()
    for directory in (inputs, outputs, home):
        directory.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(request['prompt'], inputs / 'prompt.txt')
    write(inputs / 'transport.json', {'transport': 'docker', 'image_id': identity})
    # Copy only the supported one-turn protocol. Never carry host reply packets or paths.
    allowed = ('arm', 'interactive', 'session_id', 'turn')
    sanitized = {key: request[key] for key in allowed if key in request}
    adapter_settings = {key: settings[key] for key in ('claude_version', 'expected_served_models', 'effort') if key in settings}
    sanitized.update(workspace='/workspace', home='/home/agent', skills='/skills', prompt='/inputs/prompt.txt', metrics='/outputs/metrics.json',
                     configuration={'id': request['configuration']['id'], 'model': request['configuration']['model'], 'harness': request['configuration']['harness'], 'settings': adapter_settings})
    write(outputs / 'request.json', sanitized)
    adapter_root = Path(__file__).parent
    mounts = [mount(request['workspace'], '/workspace', False), mount(request['skills'], '/skills'),
              mount(inputs, '/inputs'), mount(outputs, '/outputs', False), mount(home, '/home/agent', False),
              mount(adapter_root / 'eval_claude.py', '/adapter/eval_claude.py'), mount(adapter_root / 'eval_trace.py', '/adapter/eval_trace.py')]
    # A previous turn's metrics must not masquerade as this invocation's evidence.
    metrics_file = outputs / 'metrics.json'
    if metrics_file.exists():
        metrics_file.unlink()
    metrics = {'container_image': image, 'container_image_id': identity}
    write(request['metrics'], metrics)
    code, stdout, stderr = execute(identity, mounts, ['python3', '/adapter/eval_claude.py', '--container-shell', '/outputs/request.json'], settings.get('credential_env', []))
    if metrics_file.is_symlink():
        raise ValueError('container metrics must not be a symlink')
    if metrics_file.exists():
        metrics.update(read(metrics_file))
    write(request['metrics'], metrics)
    # Keep traces in a separate turn directory without copying the container's session HOME.
    traces = parent / f'container-turn-{request.get("turn", 0)}'
    traces.mkdir(exist_ok=False)
    for path in outputs.iterdir():
        if path.is_symlink():
            raise ValueError('container output must not be a symlink')
        if path.is_file() and path.name != 'request.json':
            shutil.copyfile(path, traces / path.name)
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    return code


def grade(request_path):
    """Grade generated code without credentials, network or host execution."""
    request = read(request_path)
    identity = image_identity(request['container_image'])
    workspace = Path(request['workspace']).resolve()
    grader = request['grader']
    # The interpreter comes from the pinned image, not the host's virtual environment.
    if Path(grader[0]).name not in ('python', 'python3') and not Path(grader[0]).name.startswith('python3.'):
        raise ValueError('container grading currently supports Python graders only')
    sources = [Path(x).resolve() for x in grader[1:] if Path(x).is_file()]
    sources.extend(Path(x).resolve() for x in request.get('grader_inputs', []))
    if not sources:
        raise ValueError('grader needs an explicit script file')
    common = Path(os.path.commonpath([str(source.parent) for source in sources]))
    mapped = {str(source): '/grader/' + str(source.relative_to(common)) for source in sources}
    mounts = [mount(workspace, '/workspace')]
    mounts += [mount(source, mapped[str(source)]) for source in sources]
    interaction = workspace.parent / 'interactions.json'
    if interaction.exists():
        mounts.append(mount(interaction, '/interactions.json'))
    argv = ['python3'] + [mapped[str(Path(x).resolve())] if Path(x).is_file() else x for x in grader[1:]] + ['/workspace']
    code, stdout, stderr = execute(identity, mounts, argv, network=False)
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    return code


def main():
    try:
        if len(sys.argv) == 3 and sys.argv[1] == '--grade':
            return grade(Path(sys.argv[2]))
        if len(sys.argv) == 2:
            return run(Path(sys.argv[1]))
        raise ValueError('usage: eval_container.py [--grade] REQUEST.json')
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        # Do not print command environments or provider credentials.
        print(f'Container adapter failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
