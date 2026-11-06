"""Deterministic outcome checks; prose/review quality still needs blind review."""
import json
from pathlib import Path
import sys
import shutil
import subprocess
import tempfile

case, workspace = sys.argv[1], Path(sys.argv[2])
checks = {}
fixture = Path(__file__).parent / case / 'fixture'

def unchanged(name):
    return (workspace / name).read_bytes() == (fixture / name).read_bytes()

try:
    if case == 'atomic-export':
        checks['unrelated_preserved'] = unchanged('notes.txt')
        with tempfile.TemporaryDirectory() as temp:
            child = Path(temp)
            shutil.copyfile(workspace / 'exporter.py', child / 'exporter.py')
            result = subprocess.run(
                [sys.executable, '-I', str(Path(__file__).with_name('atomic_worker.py'))],
                cwd=child,
                env={'HOME': temp, 'TMPDIR': temp, 'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'},
                capture_output=True,
                timeout=10,
            )
            checks['candidate_completed'] = result.returncode == 0 and (child / 'checks.json').is_file()
            if checks['candidate_completed']:
                child_checks = json.loads((child / 'checks.json').read_text())
                expected = {
                    f'{failure}-{existing}-{after}'
                    for failure in ('RuntimeError', 'Cancelled')
                    for existing in (False, True)
                    for after in (0, 1, 3)
                } | {'success-0', 'success-3', 'encoding-False', 'encoding-True'}
                checks['candidate_checks_complete'] = set(child_checks) == expected
                checks.update({f'candidate:{key}': value is True for key, value in child_checks.items()})
    elif case == 'review-boundary':
        findings = json.loads((workspace / 'review.json').read_text())['findings']
        checks['sources_preserved'] = unchanged('cache.py') and unchanged('unique.py')
        checks['finding_structure'] = len(findings) == 1 and findings[0]['file'] == 'cache.py' and findings[0]['line'] in (2, 3) and all(isinstance(findings[0].get(k), str) and findings[0][k].strip() for k in ('trigger', 'impact'))
        # A human checks whether trigger and impact actually explain the defect.
    elif case == 'prose-preservation':
        text = (workspace / 'edited.md').read_text()
        checks['source_preserved'] = unchanged('draft.md')
        for token in ('240', '2-4 hours', '"Keep the original until verification finishes."', '`exportctl retry --limit 7`'):
            checks[f'required_string_present:{token}'] = token in text
        checks['edited'] = text != (workspace / 'draft.md').read_text()
        # Meaning, uncertainty, scope and clarity require blind human grading.
    elif case == 'research-release':
        answer = json.loads((workspace / 'answer.json').read_text())
        checks['stable_semver'] = answer['version'] == '2.4.0'
        checks['primary_evidence'] = answer['evidence_file'] == 'releases.json'
        checks['limitation_present'] = isinstance(answer.get('limitation'), str) and bool(answer['limitation'].strip())
        checks['sources_preserved'] = unchanged('releases.json') and unchanged('news.md')
    else:
        raise ValueError(f'Unknown case: {case}')
except Exception as error:
    checks['artifact_readable'] = False
    checks['error'] = f'{type(error).__name__}: {error}'
print(json.dumps({
    'passed': all(value is True for value in checks.values()),
    'checks': checks,
    'grading_scope': 'deterministic-outcomes-only',
    'requires_human_review': True,
}))
