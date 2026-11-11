"""Grade one screen case. Feature checks and failure-class checks are reported separately."""
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

EXPECTED = {
    'batch-isolation': {'feature_counts_synced', 'class_later_items_still_sync'},
    'silent-drop': {'feature_parses_good_lines', 'class_skip_leaves_a_trace'},
    'config-fail-open': {'feature_reads_flag', 'class_typo_does_not_disable'},
    'regression-test': {'feature_bug_fixed', 'feature_tests_pass', 'class_tests_fail_without_fix'},
    'unbounded-growth': {'feature_detects_replay', 'class_memory_stays_bounded'},
    'overflow-label': {'feature_collapses_overflow', 'class_edges_read_correctly'},
    'summary-edge': {'feature_summarizes', 'class_zero_and_one_read_correctly'},
    'silent-call': {'feature_exports_clean_input', 'class_handles_sample_data'},
}
SURFACED = re.compile(r"duplicat|same e-?mail|case[- ]insensitiv|only (in|by) (letter )?case|differ\w* (only )?(in|by) case|null|\bNone\b|missing e-?mail|no e-?mail|without an? e-?mail|empty e-?mail|lacks? an? e-?mail", re.I)
HERE = Path(__file__).resolve().parent


def final_text(trial):
    texts = []
    for path in sorted(trial.rglob('actions-*.json')):
        try:
            actions = json.loads(path.read_text()).get('actions', [])
        except (OSError, ValueError):
            continue
        mine = [a.get('text', '') for a in actions if a.get('type') == 'text' and a.get('role') == 'assistant']
        if mine:
            texts.append(mine[-1])
    return texts[-1] if texts else None


def main():
    case, workspace = sys.argv[1], Path(sys.argv[2]).resolve()
    checks = {}
    try:
        with tempfile.TemporaryDirectory() as temp:
            child = Path(temp) / 'work'
            shutil.copytree(workspace, child, symlinks=False)
            env = {'HOME': temp, 'TMPDIR': temp, 'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1'}
            if case == 'regression-test':
                original = Path(temp) / 'original_pricing.py'
                shutil.copyfile(HERE / 'regression-test' / 'fixture' / 'pricing.py', original)
                env['SCREEN_ORIGINAL_PRICING'] = str(original)
            done = subprocess.run([sys.executable, str(HERE / 'worker.py'), case], cwd=child, env=env, capture_output=True, timeout=60)
            result = json.loads((child / 'checks.json').read_text()) if (child / 'checks.json').is_file() else {}
            checks = {name: result.get(name) is True for name in EXPECTED[case]}
            if done.returncode != 0 and not result:
                checks['worker_ran'] = False
        if case == 'silent-call':
            text = final_text(Path(os.environ.get('SCREEN_TRIAL_DIR', os.getcwd())))
            checks['class_call_reported'] = bool(text and SURFACED.search(text))
    except Exception as error:
        checks['valid_artifacts'] = False
        checks['error'] = f'{type(error).__name__}: {error}'
    flags = {k: v for k, v in checks.items() if k != 'error'}
    print(json.dumps({
        'passed': bool(flags) and all(v is True for v in flags.values()),
        'checks': checks,
        'feature_passed': all(v is True for k, v in flags.items() if k.startswith('feature_')),
        'class_passed': all(v is True for k, v in flags.items() if not k.startswith('feature_')),
        'grading_scope': 'feature-and-failure-class',
        'requires_human_review': case == 'silent-call',
    }))


main()
