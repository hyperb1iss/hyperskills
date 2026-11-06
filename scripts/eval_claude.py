#!/usr/bin/env python3
"""Controlled file-task Claude adapter; discovery is a supplied catalog, not plugins."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

TOOLS = 'Read,Write,Edit,Glob,Grep'


def build_prompt(request: dict) -> str:
    prompt = Path(request['prompt']).read_text()
    root = Path(request['skills'])
    parts = ['Complete the task in the working directory. File tools are available; shell, network, and delegation are unavailable.', prompt]
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


def run(request_path: Path) -> int:
    request = json.loads(request_path.read_text())
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
               'harness_mode': 'controlled-file-tools-catalog',
               'limitations': 'No shell/network/delegation; discovery is a supplied catalog, not native plugin routing. Actual skill reads are unobserved.'}
    metrics_path = Path(request['metrics'])
    metrics_path.write_text(json.dumps(metrics, indent=2) + '\n')
    if version != expected_version:
        raise ValueError(f'CLI version mismatch: expected {expected_version!r}, observed {version!r}')
    command = [binary, '-p', '--safe-mode', '--restricted', '--no-session-persistence',
               '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
               '--tools', TOOLS, '--allowedTools', TOOLS, '--permission-mode', 'dontAsk',
               '--output-format', 'json', '--model', config['model']]
    if request['arm'] != 'baseline':
        command += ['--add-dir', request['skills']]
    if 'effort' in settings:
        command += ['--effort', settings['effort']]
    prompt = build_prompt(request)
    request_path.with_name('effective-prompt.txt').write_text(prompt)
    result = subprocess.run(command, input=prompt, text=True, capture_output=True, cwd=request['workspace'])
    request_path.with_name('claude-output.json').write_text(result.stdout)
    request_path.with_name('claude-stderr.log').write_text(result.stderr)
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        if result.returncode:
            sys.stderr.write(result.stderr)
            return result.returncode
        raise ValueError('Claude did not return JSON') from None
    if not isinstance(output, dict):
        raise ValueError('Claude did not return a result object')
    usage = output.get('usage', {})
    token_fields = ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')
    if isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in token_fields):
        metrics['tokens'] = sum(usage[k] for k in token_fields)
    models = output.get('modelUsage')
    if isinstance(models, dict) and models:
        metrics['served_models'] = sorted(models)
    metrics['cost_usd'] = output.get('total_cost_usd')
    metrics_path.write_text(json.dumps(metrics, indent=2) + '\n')
    if result.returncode:
        sys.stderr.write(result.stderr)
        return result.returncode
    if output.get('type') != 'result' or output.get('is_error') is not False:
        raise ValueError('Claude did not return a successful result event')
    if output.get('permission_denials'):
        raise ValueError('Claude reported denied tool operations; trial is not a successful execution')
    if metrics['served_models'] != sorted(set(expected_models)):
        raise ValueError('served model identities missing or different from settings.expected_served_models')
    sys.stdout.write(output.get('result', ''))
    return 0


def main() -> int:
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: eval_claude.py REQUEST.json')
        return run(Path(sys.argv[1]).resolve())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'Claude adapter failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
