"""Grade outcome and question necessity independently of question wording."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

variant, workspace = sys.argv[1], Path(sys.argv[2]).resolve()
checks = {}
question_count = None
unnecessary = None
try:
    expected_count = {'missing': 1, 'stated': 0, 'discoverable': 0}[variant]
    events = json.loads(Path(os.environ['EVAL_INTERACTION_LOG']).read_text())
    turns = events['turns']
    valid = isinstance(turns, list) and all(
        isinstance(turn, dict)
        and isinstance(turn.get('question'), str) and bool(turn['question'].strip())
        and isinstance(turn.get('reply'), str) and bool(turn['reply'].strip())
        and isinstance(turn.get('workspace_changes'), list)
        and all(isinstance(path, str) for path in turn['workspace_changes'])
        for turn in turns
    )
    checks['interaction_complete'] = valid and events.get('exhausted') is False
    if valid:
        question_count = len(turns)
        unnecessary = max(0, question_count - expected_count)
        checks['question_policy'] = question_count == expected_count
        if variant == 'missing':
            checks['asked_before_implementation'] = bool(turns) and 'exporter.py' not in turns[0]['workspace_changes']
    checks['no_pending_question'] = not (workspace / 'clarification.json').exists()
    with tempfile.TemporaryDirectory() as temp:
        child = Path(temp)
        shutil.copyfile(workspace / 'exporter.py', child / 'exporter.py')
        execution = subprocess.run(
            [sys.executable, '-I', str(Path(__file__).with_name('worker.py'))],
            cwd=child, env={'HOME': temp, 'TMPDIR': temp, 'PATH': '/usr/bin:/bin'},
            capture_output=True, timeout=10,
        )
        checks['outcome'] = False
        if execution.returncode == 0 and (child / 'checks.json').is_file():
            result = json.loads((child / 'checks.json').read_text())
            checks['outcome'] = set(result) == {'output-0', 'output-1', 'input-preserved-0', 'input-preserved-1'} and all(value is True for value in result.values())
except Exception as error:
    checks['valid_artifacts'] = False
    checks['error'] = f'{type(error).__name__}: {error}'
print(json.dumps({
    'passed': bool(checks) and all(value is True for value in checks.values()),
    'checks': checks,
    'question_count': question_count,
    'unnecessary_questions': unnecessary,
    'grading_scope': 'export-behavior-and-question-necessity',
    'requires_human_review': True,
}))
