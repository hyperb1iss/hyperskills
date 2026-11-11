#!/usr/bin/env python3
"""Controlled file-task Claude adapter; discovery is a supplied catalog, not plugins."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import uuid

from eval_trace import normalize

TOOLS = 'Read,Write,Edit,Glob,Grep'


def verify_container(request):
    marker = Path('/inputs/transport.json')
    if not Path('/.dockerenv').is_file() or not marker.is_file():
        raise ValueError('shell profile requires the Docker transport')
    proof = json.loads(marker.read_text())
    if proof.get('transport') != 'docker' or not proof.get('image_id'):
        raise ValueError('missing Docker transport provenance')
    if request['workspace'] != '/workspace' or request['skills'] != '/skills' or request['prompt'] != '/inputs/prompt.txt':
        raise ValueError('shell profile requires transport-owned mount paths')



def build_prompt(request: dict, shell=False) -> str:
    prompt = Path(request['prompt']).read_text()
    root = Path(request['skills'])
    capability = 'File and Bash tools are available in the isolated trial container.' if shell else 'File tools are available; shell, network, and delegation are unavailable.'
    parts = ['Complete the task in the working directory. It holds the whole project; do not search its parent directories. ' + capability, prompt]
    if request.get('interactive'):
        parts.append('If you need clarification, write clarification.json in the working directory containing {"question": "your question"}, then end your turn. The host will deliver the user reply and removes clarification.json when it does; do not recreate, empty, or delete that file yourself. Otherwise complete the task without asking.')
    if request['arm'] == 'explicit':
        for entry in sorted(root.glob('*/SKILL.md')):
            parts.append(f'Relevant skill ({entry}):\n{entry.read_text()}')
    elif request['arm'] == 'discovery':
        entries = []
        for entry in sorted(root.glob('*/SKILL.md')):
            text = entry.read_text()
            # Preserve the metadata verbatim, including multiline descriptions.
            metadata = text.split('---', 2)[1] if text.startswith('---\n') else entry.parent.name
            entries.append(f'{entry}\n{metadata}')
        parts.append('Available skill catalog. Read relevant SKILL.md files when useful:\n' + '\n'.join(entries))
    elif request['arm'] != 'baseline':
        raise ValueError('unknown arm')
    return '\n\n'.join(parts)


def run(request_path: Path, container_shell=False) -> int:
    request = json.loads(request_path.read_text())
    if container_shell:
        verify_container(request)
    elif request.get('configuration', {}).get('settings', {}).get('profile', 'file') != 'file':
        raise ValueError('shell profile must be launched by Docker transport')
    config = request['configuration']
    settings = config.get('settings', {})
    binary = settings.get('claude_bin', 'claude')
    expected_version = settings.get('claude_version')
    expected_models = settings.get('expected_served_models')
    if not isinstance(expected_version, str) or not expected_version.strip():
        raise ValueError('settings.claude_version must pin exact CLI version output')
    if not isinstance(expected_models, list) or not expected_models or any(not isinstance(x, str) or not x for x in expected_models):
        raise ValueError('settings.expected_served_models must pin served model identities')
    version = subprocess.run([binary, '--version'], capture_output=True, text=True, check=True).stdout.strip()
    metrics = {'cost_usd': None, 'tokens': None, 'skills_loaded': None,
               'cli_version': version, 'served_models': None,
               'cost_scope': 'session_cumulative', 'tokens_scope': 'turn',
               'session_id': None,
               'harness_mode': 'controlled-shell-catalog' if container_shell else 'controlled-file-tools-catalog',
               'limitations': 'Discovery is a supplied catalog, not native plugin routing. Read events observe file access, not semantic use.'}
    metrics_path = Path(request['metrics'])
    metrics_path.write_text(json.dumps(metrics, indent=2) + '\n')
    if version != expected_version:
        raise ValueError(f'CLI version mismatch: expected {expected_version!r}, observed {version!r}')
    command = [binary, '-p', '--safe-mode', '--restricted',
               '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
               '--tools', TOOLS + (',Bash' if container_shell else ''), '--allowedTools', TOOLS + (',Bash' if container_shell else ''), '--permission-mode', 'dontAsk',
               '--output-format', 'stream-json', '--verbose', '--model', config['model']]
    turn = request.get('turn', 0)
    if type(turn) is not int or turn < 0:
        raise ValueError('turn must be a nonnegative integer')
    if request.get('interactive'):
        session_id = str(uuid.UUID(request['session_id']))
        command += ['--resume' if turn else '--session-id', session_id]
    else:
        if turn:
            raise ValueError('continuation requires interactive session')
        command += ['--no-session-persistence']
    if request['arm'] != 'baseline':
        command += ['--add-dir', request['skills']]
    if 'effort' in settings:
        command += ['--effort', settings['effort']]
    prompt = Path(request['prompt']).read_text() if turn else build_prompt(request, container_shell)
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError('continuation requires a nonempty followup')
    request_path.with_name(f'effective-prompt-{turn}.txt').write_text(prompt)
    request_path.with_name('effective-prompt.txt').write_text(prompt)
    event_path = request_path.with_name(f'claude-events-{turn}.jsonl')
    error_path = request_path.with_name(f'claude-stderr-{turn}.log')
    with event_path.open('w') as event_file, error_path.open('w') as error_file:
        result = subprocess.run(command, input=prompt, text=True, stdout=event_file, stderr=error_file, cwd=request['workspace'])
    raw_events, raw_errors = event_path.read_text(), error_path.read_text()
    try:
        events = [json.loads(line) for line in raw_events.splitlines() if line.strip()]
        trace = normalize(events, request['skills'])
        request_path.with_name(f'actions-{turn}.json').write_text(json.dumps(trace, indent=2) + '\n')
        metrics['skills_loaded'] = trace['skills_read_successfully']
        metrics['skills_preloaded'] = sorted(p.parent.name for p in Path(request['skills']).glob('*/SKILL.md')) if request['arm'] == 'explicit' and not turn else []
        results = [event for event in events if isinstance(event, dict) and event.get('type') == 'result']
        output = results[-1] if results else None
    except json.JSONDecodeError:
        if result.returncode:
            sys.stderr.write(raw_errors)
            return result.returncode
        raise ValueError('Claude did not return JSON') from None
    if not isinstance(output, dict):
        metrics_path.write_text(json.dumps(metrics, indent=2) + '\n')
        raise ValueError('Claude did not return a result object')
    usage = output.get('usage', {})
    token_fields = ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')
    if isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in token_fields):
        metrics['tokens'] = sum(usage[k] for k in token_fields)
    models = output.get('modelUsage')
    if isinstance(models, dict) and models:
        metrics['served_models'] = sorted(models)
    metrics['cost_usd'] = output.get('total_cost_usd')
    metrics['session_id'] = output.get('session_id')
    metrics_path.write_text(json.dumps(metrics, indent=2) + '\n')
    if result.returncode:
        sys.stderr.write(raw_errors)
        return result.returncode
    if output.get('type') != 'result' or output.get('is_error') is not False:
        raise ValueError('Claude did not return a successful result event')
    if output.get('permission_denials'):
        raise ValueError('Claude reported denied tool operations; trial is not a successful execution')
    if request.get('interactive') and output.get('session_id') != request['session_id']:
        raise ValueError('result session identity differs from requested interactive session')
    if metrics['served_models'] != sorted(set(expected_models)):
        raise ValueError('served model identities missing or different from settings.expected_served_models')
    sys.stdout.write(output.get('result', ''))
    return 0


def main() -> int:
    try:
        args = sys.argv[1:]
        shell = bool(args and args[0] == '--container-shell')
        if shell:
            args = args[1:]
        if len(args) != 1:
            raise ValueError('usage: eval_claude.py [--container-shell] REQUEST.json')
        return run(Path(args[0]).resolve(), container_shell=shell)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'Claude adapter failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
