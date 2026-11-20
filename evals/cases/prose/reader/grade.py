"""Deterministic checks for one prose-reader case.

Usage: grade.py CASE WORKSPACE. Checks preservation only; whether the edit works
for a cold reader is measured separately by scripts/eval_reader.py.
"""
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def words(text):
    return re.findall(r'\S+', text)


def sentences(text):
    # Approximate: every nonblank line (heading, bullet, paragraph) is split on
    # terminal punctuation followed by whitespace.
    units = []
    for line in text.splitlines():
        units.extend(part for part in re.split(r'(?<=[.!?])\s+', line.strip()) if words(part))
    return units


def profile(text):
    count = len(words(text))
    lengths = [len(words(sentence)) for sentence in sentences(text)]
    return {
        'words': count,
        'median_sentence_words': statistics.median(lengths) if lengths else 0,
        'semicolons_per_1000_words': round(1000 * text.count(';') / count, 2) if count else 0.0,
    }


def main():
    case, workspace = sys.argv[1], Path(sys.argv[2])
    fixture = HERE / case / 'fixture'
    checks, metrics = {}, {}
    try:
        protected = json.loads((HERE / case / 'protected.json').read_text(encoding='utf-8'))
        for name in ('draft.md', 'notes.md'):
            checks[f'{name}_unchanged'] = (workspace / name).read_bytes() == (fixture / name).read_bytes()
        edited_path = workspace / 'edited.md'
        checks['edited_exists'] = edited_path.is_file() and not edited_path.is_symlink()
        if checks['edited_exists']:
            draft = (fixture / 'draft.md').read_text(encoding='utf-8')
            edited = edited_path.read_text(encoding='utf-8')
            checks['edited_differs'] = edited.strip() != draft.strip()
            for token in protected:
                checks[f'protected:{token}'] = token in edited
            metrics = {'draft': profile(draft), 'edited': profile(edited)}
            if metrics['draft']['words']:
                metrics['word_ratio'] = round(metrics['edited']['words'] / metrics['draft']['words'], 3)
    except Exception as error:
        checks['artifact_readable'] = False
        checks['error'] = f'{type(error).__name__}: {error}'
    flags = {key: value for key, value in checks.items() if key != 'error'}
    print(json.dumps({
        'passed': bool(flags) and all(value is True for value in flags.values()),
        'checks': checks,
        'metrics': metrics,
        'grading_scope': 'deterministic-preservation-only',
        'requires_human_review': True,
        'reader_stage': 'Reader accuracy is scored separately by scripts/eval_reader.py score; metrics are descriptive and do not affect passed.',
    }))


main()
