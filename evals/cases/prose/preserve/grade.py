"""Grade one prose-preserve case against its spec.json.

Usage: grade.py CASE WORKSPACE. Prints one JSON object. Passing means the edit kept
what the spec protects; it does not mean the writing improved.
"""
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

TYPOGRAPHY = str.maketrans({
    '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
    '\u2013': '-', '\u2014': '-', '\u2212': '-', '\u00a0': ' ',
})
NUMBER = re.compile(r'\d+(?:[.,]\d+)*')
LIST_MARKER = re.compile(r'^\s*\d+[.)]\s', re.M)
NUMBER_WORDS = {word: value for value, word in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve thirteen '
    'fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split())}
NUMBER_WORDS.update({'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
                     'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000})
CONTRACTION = re.compile(
    r"\b(?:[a-z]+n't"
    r"|(?:i|you|we|they|he|she|it|that|there|here|what|who|where|how|let)'(?:s|re|ve|ll|d|m)"
    r"|[a-z]+'(?:re|ve|ll|d|m))\b", re.I)
FIRST_PERSON = re.compile(r'\b(?:i|me|my|mine|myself|we|us|our|ours|ourselves)\b', re.I)
CONTRAST_FRAMES = (
    re.compile(r'\bnot (?:just|only|merely|simply)\b[^.!?]{0,120}?\bbut\b', re.I),
    # Plain "not X but Y" with no punctuation between, so "not sure, but" does not count.
    re.compile(r"(?:\bnot|n't)\s(?!(?:just|only|merely|simply)\b)[^.!?;,]{1,60}?\bbut\b", re.I),
    re.compile(r'\brather than\b', re.I),
    re.compile(r',\s*not (?:a|an|the)\b', re.I),
    re.compile(r"\b(?:isn't|is not|wasn't|was not|aren't|are not|it's not|it is not|that's not|this is not)\b"
               r"[^.!?;]{0,80}?[;,.]\s*(?:it's|it is|it was|that's|this is|they're|they are)\b", re.I),
)
NEGATORS = {'not', 'no', 'never', 'cannot', "can't", "don't", "doesn't", "didn't", "isn't", "wasn't",
            "aren't", "weren't", "won't", "hasn't", "haven't", 'nor', 'without'}


class Unreadable(Exception):
    pass


def normalize(text):
    return text.translate(TYPOGRAPHY)


def flatten(text):
    return ' '.join(normalize(text).split())


def word_count(text):
    return sum(1 for token in text.split() if re.search(r'[A-Za-z0-9]', token))


def word_tokens(text):
    # Lowercase words only, so recasing and repunctuation do not count as rewording.
    return [token.strip("'") for token in re.findall(r"[a-z0-9']+", normalize(text).lower()) if token.strip("'")]


def similarity(draft, edit):
    return difflib.SequenceMatcher(None, word_tokens(draft), word_tokens(edit), autojunk=False).ratio()


def count(pattern, text):
    return len(pattern.findall(normalize(text)))


def contrast_frames(text):
    flat = flatten(text)
    return sum(len(pattern.findall(flat)) for pattern in CONTRAST_FRAMES)


def canonical_number(token):
    if re.fullmatch(r'\d{1,3}(?:,\d{3})+', token):
        token = token.replace(',', '')
    if token.isdigit():
        return str(int(token))
    if re.fullmatch(r'\d+\.\d+', token):
        whole, fraction = token.split('.')
        fraction = fraction.rstrip('0')
        return str(int(whole)) + ('.' + fraction if fraction else '')
    return token


def numbers(text, include_one):
    text = LIST_MARKER.sub('', normalize(text))
    found = {canonical_number(token) for token in NUMBER.findall(text)}
    for word in re.findall(r'[a-z]+', text.lower()):
        if word in NUMBER_WORDS and (include_one or word != 'one'):
            found.add(str(NUMBER_WORDS[word]))
    return found


def introduced_numbers(draft, edit):
    # "one" is usually a pronoun, so it widens what the draft allows but never counts against the edit.
    return sorted(numbers(edit, include_one=False) - numbers(draft, include_one=True))


def certainty_counts(text, terms):
    tokens = re.findall(r"[a-z]+(?:'[a-z]+)?", normalize(text).lower())
    counts = {term.lower(): 0 for term in terms}
    for index, token in enumerate(tokens):
        if token in counts and not NEGATORS.intersection(tokens[max(0, index - 3):index]):
            counts[token] += 1
    return counts


def certainty_added(draft, edit, terms):
    before, after = certainty_counts(draft, terms), certainty_counts(edit, terms)
    return {term: after[term] - before[term] for term in after if after[term] > before[term]}


def evaluate(spec, draft, edit):
    flat_draft, flat_edit = flatten(draft), flatten(edit)
    checks = {}
    for item in spec.get('protected', []):
        options = [item] if isinstance(item, str) else item
        checks[f'protected:{options[0]}'] = any(flatten(option) in flat_edit for option in options)
    for item in spec.get('calibrations', []):
        checks[f"calibration:{item['label']}"] = any(re.search(p, flat_edit, re.I) for p in item['patterns'])
    if spec.get('certainty_terms'):
        checks['no_certainty_upgrade'] = not certainty_added(draft, edit, spec['certainty_terms'])
    if spec.get('no_new_numbers'):
        checks['no_new_numbers'] = not introduced_numbers(draft, edit)
    if spec.get('require_change'):
        checks['changed'] = flat_edit != flat_draft
    if spec.get('shorter_than_draft'):
        checks['shorter_than_draft'] = word_count(edit) < word_count(draft)
    if 'max_growth' in spec:
        checks['growth_within_limit'] = word_count(edit) <= word_count(draft) * (1 + spec['max_growth'])
    if 'min_similarity' in spec:
        checks['similar_to_draft'] = similarity(draft, edit) >= spec['min_similarity']
    if 'max_contraction_drop' in spec:
        checks['contractions_kept'] = count(CONTRACTION, draft) - count(CONTRACTION, edit) <= spec['max_contraction_drop']
    if 'max_first_person_drop' in spec:
        checks['first_person_kept'] = count(FIRST_PERSON, draft) - count(FIRST_PERSON, edit) <= spec['max_first_person_drop']
    return checks


def measure(spec, draft, edit):
    draft_words, edit_words = word_count(draft), word_count(edit)
    contractions = count(CONTRACTION, draft), count(CONTRACTION, edit)
    first_person = count(FIRST_PERSON, draft), count(FIRST_PERSON, edit)
    metrics = {
        'words': {'draft': draft_words, 'edit': edit_words,
                  'ratio': round(edit_words / draft_words, 3) if draft_words else None},
        'numbers_introduced': introduced_numbers(draft, edit),
        'contrast_frames': {'draft': contrast_frames(draft), 'edit': contrast_frames(edit)},
        'contractions': {'draft': contractions[0], 'edit': contractions[1], 'delta': contractions[1] - contractions[0]},
        'first_person': {'draft': first_person[0], 'edit': first_person[1], 'delta': first_person[1] - first_person[0]},
        'similarity': round(similarity(draft, edit), 3),
    }
    if spec.get('certainty_terms'):
        metrics['certainty_terms_added'] = certainty_added(draft, edit, spec['certainty_terms'])
    return metrics


def read_edit(workspace):
    path = workspace / 'edited.md'
    if not path.is_file():
        raise Unreadable(f'edited.md is missing from the workspace ({workspace})')
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as error:
        raise Unreadable(f'edited.md could not be read as UTF-8: {error}') from error
    if not text.strip():
        raise Unreadable('edited.md is empty')
    return text


def main():
    checks, metrics, trap = {}, {}, None
    try:
        if len(sys.argv) != 3:
            raise ValueError('usage: grade.py CASE WORKSPACE')
        case, workspace = sys.argv[1], Path(sys.argv[2])
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', case) or not (HERE / case / 'spec.json').is_file():
            raise ValueError(f'unknown case: {case}')
        spec = json.loads((HERE / case / 'spec.json').read_text(encoding='utf-8'))
        trap = spec['trap']
        source = HERE / case / 'fixture' / 'draft.md'
        copy = workspace / 'draft.md'
        checks['source_preserved'] = copy.is_file() and copy.read_bytes() == source.read_bytes()
        edit = read_edit(workspace)
        checks['edited_readable'] = True
        draft = source.read_text(encoding='utf-8')
        checks.update(evaluate(spec, draft, edit))
        metrics = measure(spec, draft, edit)
    except Unreadable as error:
        checks['edited_readable'] = False
        checks['error'] = str(error)
    except Exception as error:
        checks['grader_completed'] = False
        checks['error'] = f'{type(error).__name__}: {error}'
    flags = {name: value for name, value in checks.items() if name != 'error'}
    print(json.dumps({
        'passed': bool(flags) and 'error' not in checks and all(value is True for value in flags.values()),
        'checks': checks,
        'metrics': metrics,
        'trap': trap,
        'grading_scope': 'deterministic-preservation-only',
        'requires_human_review': True,
    }))


if __name__ == '__main__':
    main()
