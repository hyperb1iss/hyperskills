# Prose preserve

Eight synthetic editing cases that measure what a prose-editing pass must not break. Published studies of model revision report the same handful of damages: content deleted to satisfy a style target (including a repeated sentence removed together with its citations), an author's voice flattened under light-edit requests, hedged claims made confident, specifics invented, and new contrast framings added. Each case sets one of those traps inside an ordinary editing request and grades the result mechanically.

The prompt names the reader and asks for an edit into `edited.md`, with facts preserved and `draft.md` untouched. It never names the trap.

## Cases

| Case                         | Split       | Trap          | Surface                      |
| ---------------------------- | ----------- | ------------- | ---------------------------- |
| `padded-slop-status-update`  | development | padded-slop   | internal status update       |
| `padded-slop-help-article`   | holdout     | padded-slop   | customer help article        |
| `citation-trap-related-work` | development | citation-trap | paper related-work section   |
| `citation-trap-proposal`     | holdout     | citation-trap | grant proposal section       |
| `voice-trap-chat-message`    | development | voice-trap    | team chat message            |
| `voice-trap-volunteer-email` | holdout     | voice-trap    | personal email to a group    |
| `hedge-trap-postmortem`      | development | hedge-trap    | incident postmortem section  |
| `hedge-trap-field-study`     | holdout     | hedge-trap    | scientific results paragraph |

Each case directory holds `prompt.md`, `fixture/draft.md` (the only file the agent sees), `spec.json` (protected strings, calibration patterns, thresholds), `oracle/edited.md` (a good edit that passes), and `wrong/edited.md` (a plausible edit that springs the trap). The spec's `wrong_must_fail` list names the checks the wrong edit is built to fail; the tests hold it to that.

The two padded-slop drafts contain em dashes and curly quotes on purpose, because that typography is part of the style being edited away. Do not normalize them. Every other file here is plain ASCII.

## What each trap measures

**Padded-slop.** An older chatbot-style draft (filler openers, "it's important to note", "delve", puffery, rule-of-three flourishes, an upbeat close, a sign-off offering more help) wrapped around real facts: numbers with units, a command, a direct quotation, and an estimate explicitly marked as not a guarantee. A pass keeps every protected string, keeps the hedge words attached to the estimate, comes out shorter than the draft, and contains no number the draft lacks. The trap is the cleanup itself: cutting the padding invites cutting the hedge and "helpfully" adding a derived figure.

**Citation-trap.** A paragraph with a sentence that reads as a restatement of an earlier one but carries the only mention of several citations and a table. The prompt says the paragraph repeats itself. A pass keeps every citation key, figure or table reference, and number, and differs from the draft.

**Voice-trap.** An informal, first-person message that already works: contractions, a deliberate fragment, one honest contrast, mild profanity, and one mildly formulaic line. The prompt asks to clean it up before sending. A pass stays close to the source in wording, loses at most one contraction and one first-person pronoun, grows by no more than 10 percent, and keeps the protected facts. Sending the draft unchanged passes, which is the point: the right edit to a good message is small or none.

**Hedge-trap.** A postmortem or results paragraph whose claims are deliberately calibrated ("associated with", "may", "we did not measure", a sample scope) plus some padding. A pass keeps each calibration phrase or an equivalent from a short per-phrase list, adds no certainty word from a listed set (causes, proves, confirms, demonstrates, always, definitively, and similar) beyond what the draft already had, keeps the facts, and differs from the draft.

## The grader

`grade.py CASE WORKSPACE` reads `CASE/spec.json` and the trusted `CASE/fixture/draft.md`, then grades `WORKSPACE/edited.md`. It prints one JSON object with `passed`, `checks`, `metrics`, `trap`, `grading_scope`, and `requires_human_review: true`. Every case also checks that `draft.md` is byte-identical to the fixture. A missing, empty, or undecodable `edited.md` fails with `edited_readable: false` and an `error` saying which.

Matching runs after typographic normalization (curly quotes to straight, en and em dashes and the minus sign to a hyphen, non-breaking space to space) and whitespace collapse, so rewrapping or retyping punctuation does not fail a protected string. Protected strings are case-sensitive substrings; a list entry accepts any of its spellings. Calibrations are case-insensitive regular expressions. Certainty words are counted per word form against the draft; an occurrence within three words after a negator ("not", "didn't", "without", and similar) does not count, so "this does not prove" stays legal.

`metrics` is reported for every case and never affects `passed`:

| Metric                         | Meaning                                                                                                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `words`                        | Word counts for draft and edit, and their ratio                                                                                                               |
| `numbers_introduced`           | Numbers in the edit absent from the draft, after normalizing thousands separators, trailing decimal zeros, and number words; ordered-list markers are ignored |
| `contrast_frames`              | Counts in draft and edit of "not just/only/merely/simply ... but", plain "not X but Y", "rather than", ", not a/an/the", and "isn't X; it's Y" forms          |
| `contractions`, `first_person` | Counts in draft and edit, and the delta                                                                                                                       |
| `similarity`                   | `difflib` ratio over lowercase word tokens                                                                                                                    |
| `certainty_terms_added`        | Hedge-trap only: certainty words the edit added                                                                                                               |

## What a pass does and does not establish

A pass means the checks in the spec held: the listed strings survived, the listed hedges or an allowed equivalent survived, and the length, number, and voice limits held. It does not establish that the edit is better writing, that unlisted facts survived, that a surviving hedge still attaches to the right claim, or that the edit is coherent. Word salad that contains every protected string passes the citation-trap. Pair these results with blind human preference before claiming a skill improves prose, as the [protocol](../../../PROTOCOL.md) requires.

A fail is more specific than a pass, but allowed-equivalent lists are finite. A correct edit can phrase a hedge in a way the list does not anticipate. Before counting such a fail, read the diff; if the grader is wrong, record it as a grader defect and widen the list in a new revision rather than mid-run.

## Thresholds and why

All thresholds are author-chosen. They sit between edits the author judged acceptable and edits the author judged damaging, measured on these drafts, and they carry no external validation.

| Threshold                          | Value                   | Evidence                                                                                                                                                                                                                                                                                                               |
| ---------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Voice similarity                   | at least 0.80           | Oracles score 0.96 to 0.97, recasing included, because comparison is lowercase. A light pass rephrasing three clauses scored 0.85 and 0.93. A moderate pass rewriting two or more sentences scored 0.68 and 0.79. A neutral rewrite that kept contractions scored 0.58. The corporate wrong edits score 0.38 and 0.50. |
| Contraction and first-person drop  | at most 1 each          | Removing the one formulaic line can cost one of each: the chat oracle loses a "me", the email oracle loses an "it's". The wrong edits drop 8 and 10 contractions.                                                                                                                                                      |
| Voice growth                       | at most 10 percent      | A cleanup of a message that already works has no reason to grow; the corporate chat rewrite grows 23 percent.                                                                                                                                                                                                          |
| Padded-slop length                 | strictly shorter        | The oracles keep 44 and 50 percent of the draft's words, so this catches only a pass that cut nothing.                                                                                                                                                                                                                 |
| Changed (citation and hedge traps) | edit differs from draft | Added beyond the four trap definitions so a no-op cannot pass a case whose prompt asked for tightening.                                                                                                                                                                                                                |

## Development and holdout hygiene

Each trap has one development case and one holdout case with different content and surface. Tune skill wording against development cases only. Whoever edits a skill must not read a holdout's draft, spec, oracle, or wrong edit before freezing that edit; the case table above (trap and surface) is the most they should know. Once a holdout informs an edit, it becomes development material: relabel it and write a replacement with new content.

These files are public, so the holdout label means "not used to tune the current candidate", not "private". The [running guide](../../../RUNNING.md) covers the same limit.

When running trials, only `fixture/` belongs in the agent's workspace. Keep `spec.json`, `oracle/`, `wrong/`, and the grader outside anything the agent can read.

## Tests

```sh
python3 evals/cases/prose/preserve/test_preserve.py
```

The tests check that every oracle passes, every wrong edit fails on the checks named in its `wrong_must_fail`, an unchanged copy passes the voice-trap cases and fails the padded-slop cases, every spec string and pattern matches its own draft, a modified `draft.md` fails, and missing, empty, or unknown inputs fail with a readable error. They also pin the metric patterns on small examples.
