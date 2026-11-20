#!/usr/bin/env python3
"""Reader stage for prose-reader cases: a context-free model answers fixed questions from an edited text.

A prose-reader trial asks an editor to turn a draft written from inside a
working context into something a reader without that context can use. The
case grader (evals/cases/prose/reader/grade.py) only checks preservation. This
stage measures the outcome: a reader model receives nothing but the edited
text and the case's multiple-choice questions, and its answers are scored
against a key that is never shown to the editor or the reader.

Reader accuracy is reported separately from the grader's boolean `passed` and
never changes it. Graders run without network access, so this stage runs
afterwards, over a finished skill_eval run directory.

Limits. A model reader is a proxy for a human reader: it tolerates dense,
compressed prose far better than a person does, so a high score shows that the
facts asked about are recoverable from the text, not that the text is easy or
pleasant to read. Accuracy also rewards completeness, so an edit that pastes
the working notes wholesale can score well; read it together with the
grader's length metrics and blind human review.

Subcommands:
  ask    score one text file against one questions file
  score  score every prose-reader trial in a skill_eval run directory
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

TASK_PREFIX = 'prose-reader-'
NOT_STATED = 'The text does not say'
SYSTEM_PROMPT = (
    'You are reading a document with no background on its subject. '
    'Answer multiple-choice questions using only what the document says. '
    f'When the document does not give the answer, choose "{NOT_STATED}" rather than guessing from what seems likely. '
    'Reply with a single JSON object and nothing else.'
)
SCOPE = ('Model-reader proxy for a cold human reader, reported separately from the deterministic grader verdict. '
         'Invalid repeats are excluded from accuracy and counted; missing cost is unknown, not zero.')
FENCE = re.compile(r'^```(?:json)?\s*\n(.*)\n```$', re.S)
CALL_TIMEOUT_SECONDS = 600


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_questions(path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    questions = data.get('questions') if isinstance(data, dict) else None
    if not isinstance(questions, list) or not questions:
        raise ValueError(f'{path}: questions must be a nonempty list')
    seen = set()
    for question in questions:
        if not isinstance(question, dict):
            raise ValueError(f'{path}: each question must be an object')
        qid, options, answer = question.get('id'), question.get('options'), question.get('answer')
        if not isinstance(qid, str) or not qid or qid in seen:
            raise ValueError(f'{path}: question ids must be unique nonempty strings')
        seen.add(qid)
        if not isinstance(question.get('question'), str) or not question['question'].strip():
            raise ValueError(f'{path}: {qid} needs question text')
        if not isinstance(options, list) or len(options) < 3 or any(not isinstance(x, str) or not x.strip() for x in options):
            raise ValueError(f'{path}: {qid} needs at least two substantive options plus "{NOT_STATED}"')
        if options[-1] != NOT_STATED:
            raise ValueError(f'{path}: {qid} must end with the option "{NOT_STATED}"')
        if type(answer) is not int or not 0 <= answer < len(options) - 1:
            raise ValueError(f'{path}: {qid} answer must index a substantive option')
    return questions


def build_prompt(text: str, questions: list[dict]) -> str:
    lines = ['Read the document below, then answer the questions.', '', '<document>', text.strip(), '</document>', '', 'Questions:']
    for question in questions:
        lines += ['', f'{question["id"]}: {question["question"]}']
        lines += [f'  {index}. {option}' for index, option in enumerate(question['options'])]
    ids = ', '.join(f'"{question["id"]}"' for question in questions)
    lines += ['', f'Reply with one JSON object whose keys are exactly {ids} and whose values are the number '
                  'of the option you choose for that question. Output only the JSON object.']
    return '\n'.join(lines) + '\n'


class DuplicateKeyError(ValueError):
    pass


def unique_object(pairs):
    # json.loads keeps the last duplicate silently; an ambiguous object must fail instead.
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise DuplicateKeyError('JSON object repeats a key')
    return dict(pairs)


def parse_answers(raw, questions: list[dict]) -> dict:
    if not isinstance(raw, str):
        raise ValueError('reader returned no text')
    body = raw.strip()
    fenced = FENCE.match(body)
    if fenced:
        body = fenced.group(1).strip()
    try:
        answers = json.loads(body, object_pairs_hook=unique_object)
    except DuplicateKeyError:
        raise ValueError('reader output repeats a question id') from None
    except ValueError:
        raise ValueError('reader output is not JSON') from None
    if not isinstance(answers, dict):
        raise ValueError('reader output is not a JSON object')
    sizes = {question['id']: len(question['options']) for question in questions}
    if set(answers) != set(sizes):
        raise ValueError('reader answer keys differ from the question ids')
    for qid, choice in answers.items():
        if type(choice) is not int or not 0 <= choice < sizes[qid]:
            raise ValueError(f'reader chose an invalid option for {qid}')
    return answers


def check_version(binary: str, expected: str) -> str:
    if not isinstance(expected, str) or not expected.strip():
        raise ValueError('--claude-version must pin the exact CLI version output')
    observed = subprocess.run([binary, '--version'], capture_output=True, text=True, check=True).stdout.strip()
    if observed != expected:
        raise ValueError(f'CLI version mismatch: expected {expected!r}, observed {observed!r}')
    return observed


def reader_command(binary: str, model: str) -> list[str]:
    return [binary, '-p', '--safe-mode', '--restricted',
            '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
            '--tools', '', '--permission-mode', 'dontAsk', '--disable-slash-commands',
            '--no-session-persistence', '--system-prompt', SYSTEM_PROMPT,
            '--output-format', 'json', '--model', model]


def call_reader(binary: str, model: str, prompt: str) -> dict:
    """Run one reader with a fresh HOME and config directory and an empty working directory."""
    with tempfile.TemporaryDirectory(prefix='reader-') as temp:
        home, cwd = Path(temp) / 'home', Path(temp) / 'cwd'
        home.mkdir()
        cwd.mkdir()
        env = dict(os.environ, HOME=str(home), CLAUDE_CONFIG_DIR=str(home / '.claude'),
                   XDG_CONFIG_HOME=str(home / '.config'), XDG_CACHE_HOME=str(home / '.cache'))
        try:
            done = subprocess.run(reader_command(binary, model), input=prompt, capture_output=True, text=True,
                                  cwd=cwd, env=env, timeout=CALL_TIMEOUT_SECONDS)
        except (OSError, subprocess.SubprocessError) as error:
            return {'exit_code': None, 'event': None, 'error': f'{type(error).__name__}: {error}'}
    try:
        event = json.loads(done.stdout)
    except ValueError:
        event = None
    return {'exit_code': done.returncode, 'event': event if isinstance(event, dict) else None, 'stderr': done.stderr[-2000:]}


def assess(call: dict, questions: list[dict], model: str, repeat: int) -> dict:
    event = call.get('event') or {}
    models, cost, raw = event.get('modelUsage'), event.get('total_cost_usd'), event.get('result')
    record = {'repeat': repeat, 'valid': False, 'error': None, 'exit_code': call.get('exit_code'),
              'served_models': sorted(models) if isinstance(models, dict) and models else None,
              'cost_usd': cost if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0 else None,
              'raw_result': raw if isinstance(raw, str) else None,
              'answers': None, 'correct': None, 'accuracy': None, 'not_stated': None}
    try:
        if call.get('error'):
            raise ValueError(call['error'])
        if call.get('exit_code') != 0:
            raise ValueError(f'reader exited with {call.get("exit_code")}')
        if event.get('type') != 'result' or event.get('is_error') is not False:
            raise ValueError('reader did not return a successful result event')
        if record['served_models'] != [model]:
            raise ValueError('served model missing or different from --model')
        answers = parse_answers(raw, questions)
    except ValueError as error:
        record['error'] = str(error)
        return record
    correct = {question['id']: answers[question['id']] == question['answer'] for question in questions}
    record.update(valid=True, answers=answers, correct=correct, accuracy=sum(correct.values()) / len(correct),
                  not_stated=sum(answers[q['id']] == len(q['options']) - 1 for q in questions))
    return record


def summarize(records: list[dict], questions: list[dict]) -> dict:
    valid = [record for record in records if record['valid']]
    costs = [record['cost_usd'] for record in records]
    return {
        'repeats': records,
        'valid_repeats': len(valid),
        'invalid_repeats': len(records) - len(valid),
        'accuracy': sum(r['accuracy'] for r in valid) / len(valid) if valid else None,
        'per_question': {q['id']: (sum(r['correct'][q['id']] for r in valid) / len(valid) if valid else None) for q in questions},
        'not_stated_rate': sum(r['not_stated'] for r in valid) / (len(valid) * len(questions)) if valid else None,
        'served_models': sorted({m for r in records for m in (r['served_models'] or [])}),
        'cost_usd': sum(costs) if costs and all(c is not None for c in costs) else None,
        'cost_missing_repeats': sum(c is None for c in costs),
    }


def run_calls(prompts: dict, binary: str, model: str, jobs: int) -> dict:
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        futures = {key: pool.submit(call_reader, binary, model, prompt) for key, prompt in prompts.items()}
        return {key: future.result() for key, future in futures.items()}


def write_new(path: Path, value: dict) -> None:
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def ask(text_path, questions_path, model, claude_version, repeats=3, binary='claude', output=None, jobs=4) -> dict:
    output = Path(output)
    if output.exists():
        raise ValueError(f'{output} already exists; reader receipts are never overwritten')
    if repeats < 1:
        raise ValueError('repeats must be positive')
    questions = load_questions(questions_path)
    text = Path(text_path).read_text(encoding='utf-8')
    version = check_version(binary, claude_version)
    prompt = build_prompt(text, questions)
    calls = run_calls({repeat: prompt for repeat in range(repeats)}, binary, model, jobs)
    records = [assess(calls[repeat], questions, model, repeat) for repeat in range(repeats)]
    result = {'version': 1, 'kind': 'prose-reader-ask', 'model': model, 'cli_version': version,
              'text': str(text_path), 'text_sha256': sha256(text.encode('utf-8')), 'text_words': len(text.split()),
              'questions': str(questions_path), 'questions_sha256': sha256(Path(questions_path).read_bytes()),
              **summarize(records, questions), 'scope': SCOPE}
    write_new(output, result)
    return result


def score(run_dir, cases_dir, model, claude_version, repeats=3, binary='claude', output=None, jobs=4) -> dict:
    run_dir, cases_dir, output = Path(run_dir), Path(cases_dir), Path(output)
    if output.exists():
        raise ValueError(f'{output} already exists; reader receipts are never overwritten')
    if repeats < 1:
        raise ValueError('repeats must be positive')
    plan = json.loads((run_dir / 'plan.json').read_text())
    trials = [trial for trial in plan['trials'] if trial['task'].startswith(TASK_PREFIX)]
    if not trials:
        raise ValueError('run directory has no prose-reader trials')
    question_sets = {}
    for trial in trials:
        case = trial['task'][len(TASK_PREFIX):]
        if case not in question_sets:
            path = cases_dir / case / 'questions.json'
            question_sets[case] = (load_questions(path), sha256(path.read_bytes()))
    version = check_version(binary, claude_version)
    scorable, skipped = [], []
    for trial in trials:
        base = {key: trial[key] for key in ('configuration', 'task', 'arm', 'repeat')}
        base['trial'] = trial['id']
        result_path = run_dir / trial['id'] / 'result.json'
        result = json.loads(result_path.read_text()) if result_path.is_file() else None
        edited = run_dir / trial['id'] / 'workspace' / 'edited.md'
        if not result or result.get('status') != 'valid':
            skipped.append({**base, 'reason': 'trial_not_valid', 'status': result.get('status') if result else None})
        elif edited.is_symlink() or not edited.is_file():
            skipped.append({**base, 'reason': 'no_edited_md'})
        else:
            scorable.append((base, result, edited.read_text(encoding='utf-8')))
    prompts = {}
    for base, _, text in scorable:
        questions = question_sets[base['task'][len(TASK_PREFIX):]][0]
        prompt = build_prompt(text, questions)
        prompts.update({(base['trial'], r): prompt for r in range(repeats)})
    calls = run_calls(prompts, binary, model, jobs)
    rows = []
    for base, result, text in scorable:
        case = base['task'][len(TASK_PREFIX):]
        questions = question_sets[case][0]
        records = [assess(calls[(base['trial'], r)], questions, model, r) for r in range(repeats)]
        rows.append({**base, 'case': case, 'deterministic_passed': result.get('passed'),
                     'edited_sha256': sha256(text.encode('utf-8')), 'edited_words': len(text.split()),
                     **summarize(records, questions)})
    groups = {}
    for item in rows + skipped:
        groups.setdefault((item['configuration'], item['task'], item['arm']), {'rows': [], 'skipped': []})
    for row in rows:
        groups[(row['configuration'], row['task'], row['arm'])]['rows'].append(row)
    for item in skipped:
        groups[(item['configuration'], item['task'], item['arm'])]['skipped'].append(item['reason'])
    means = []
    for (configuration, task, arm), group in sorted(groups.items()):
        scored = [row['accuracy'] for row in group['rows'] if row['accuracy'] is not None]
        means.append({'configuration': configuration, 'task': task, 'arm': arm,
                      'trials_scored': len(scored),
                      'trials_all_repeats_invalid': len(group['rows']) - len(scored),
                      'skipped_no_edited_md': group['skipped'].count('no_edited_md'),
                      'skipped_trial_not_valid': group['skipped'].count('trial_not_valid'),
                      'mean_accuracy': sum(scored) / len(scored) if scored else None})
    costs = [row['cost_usd'] for row in rows]
    report = {'version': 1, 'kind': 'prose-reader-score', 'run': str(run_dir), 'model': model, 'cli_version': version,
              'reader_repeats': repeats,
              'questions_sha256': {case: digest for case, (_, digest) in sorted(question_sets.items())},
              'rows': rows, 'skipped': skipped,
              'skipped_counts': {reason: sum(s['reason'] == reason for s in skipped) for reason in ('no_edited_md', 'trial_not_valid')},
              'means': means,
              'cost_usd': sum(costs) if all(c is not None for c in costs) else None,
              'scope': SCOPE}
    write_new(output, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='action', required=True)
    for name in ('ask', 'score'):
        command = sub.add_parser(name)
        if name == 'ask':
            command.add_argument('--text', required=True)
            command.add_argument('--questions', required=True)
        else:
            command.add_argument('run_dir')
            command.add_argument('--cases', required=True)
        command.add_argument('--model', required=True, help='exact model id the reader must be served')
        command.add_argument('--claude-version', required=True, help='exact `claude --version` output')
        command.add_argument('--repeats', type=int, default=3)
        command.add_argument('--claude-bin', default='claude')
        command.add_argument('--jobs', type=int, default=4, help='concurrent reader invocations')
        command.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        if args.action == 'ask':
            result = ask(args.text, args.questions, args.model, args.claude_version, args.repeats,
                         args.claude_bin, args.output, args.jobs)
            summary = {key: result[key] for key in ('accuracy', 'valid_repeats', 'invalid_repeats', 'not_stated_rate', 'cost_usd')}
        else:
            result = score(args.run_dir, args.cases, args.model, args.claude_version, args.repeats,
                           args.claude_bin, args.output, args.jobs)
            summary = {'means': result['means'], 'skipped_counts': result['skipped_counts'], 'cost_usd': result['cost_usd']}
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        print(f'eval_reader failed: {error}', file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
