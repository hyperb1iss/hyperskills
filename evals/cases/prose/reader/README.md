# Prose-reader cases

These cases measure whether an edited document works for a reader who lacks
the writer's working context. The targeted failure: a report written from
inside the work uses labels coined during it, working shorthand, undefined
abbreviations, and references to things the reader never saw ("the earlier
fix", "see Tue rollback"). The editor has the working notes. The reader gets
only the edited text.

Deterministic checks cannot see this failure, and preference judges are
unreliable for prose, so the outcome is a reader task. A model with no context
answers fixed multiple-choice questions from the edited text alone, and its
answers are scored against a key.

## Layout

Each case directory holds:

| Path               | Visible to the editor | Purpose                                                                                               |
| ------------------ | --------------------- | ----------------------------------------------------------------------------------------------------- |
| `fixture/notes.md` | yes                   | Working log where the labels were coined and the facts live                                           |
| `fixture/draft.md` | yes                   | The artifact to edit; it leans on `notes.md` for meaning                                              |
| `prompt.md`        | yes                   | Told variant: says the recipient has not seen `notes.md`                                              |
| `prompt-untold.md` | yes                   | Untold variant: a plain cleanup request naming the recipient, no hint about missing context           |
| `questions.json`   | no                    | Six to eight questions, four substantive options plus "The text does not say", key always substantive |
| `oracle/edited.md` | no                    | Reference edit that resolves every label using only facts from `notes.md`                             |
| `protected.json`   | no                    | Strings that must survive verbatim                                                                    |

| Case               | Split       | Surface                                                    |
| ------------------ | ----------- | ---------------------------------------------------------- |
| `handoff-report`   | development | Agent end-of-task handoff, dense and compressed            |
| `status-update`    | development | Team chat status update, padded in the older chatbot style |
| `review-reply`     | development | Reply to code review comments                              |
| `incident-summary` | development | Incident summary for someone outside the incident          |

Task ids in a manifest are `prose-reader-<case>`, family `prose-reader`.

Use `prompt-untold.md` to measure the targeted failure. The told prompt
tells the editor that the recipient lacks the working notes, which gives the
answer away: in a pilot, a no-skill baseline scored 1.00 reader accuracy on
both development cases with it. The untold prompt asks only for a cleanup
before the draft goes to a named person, so an editor has to notice for itself
that the reader lacks context. `notes.md` still sits in the workspace, and its
opening line identifies it as the author's notes for the same work. The told
prompt remains as a ceiling condition.

## Two stages

The grader, `grade.py CASE WORKSPACE`, is deterministic. It checks that
`draft.md` and `notes.md` are unchanged, that `edited.md` exists and differs
from the draft, and that every protected string is present. It also reports
descriptive `metrics` (word counts and ratio, median sentence length,
semicolons per 1,000 words) that never affect `passed`. It always sets
`requires_human_review: true`.

The reader stage, `scripts/eval_reader.py`, runs after the trials, because
graders have no network. It sends the reader only the text and the questions:
no tools, a fresh temporary HOME and config directory, an empty working
directory, safe mode, restricted mode, no MCP servers, and no session
persistence. Each repeat must return a JSON object mapping every question id
to an option index. A repeat that cannot be parsed, or that a different model
served, is recorded as invalid and excluded from accuracy, never counted as
wrong. The stage refuses to run when `claude --version` differs from the
pinned output. Reader accuracy stays separate from the grader's `passed`.

Score one text:

```sh
python3 scripts/eval_reader.py ask \
  --text evals/cases/prose/reader/handoff-report/oracle/edited.md \
  --questions evals/cases/prose/reader/handoff-report/questions.json \
  --model claude-haiku-5-5 --claude-version "2.1.329 (Claude Code)" \
  --repeats 3 --output /tmp/handoff-oracle.json
```

Score every prose-reader trial in a finished run:

```sh
python3 scripts/eval_reader.py score evals/runs/<run> \
  --cases evals/cases/prose/reader \
  --model claude-haiku-5-5 --claude-version "2.1.329 (Claude Code)" \
  --repeats 3 --output evals/runs/<run>-reader.json
```

`score` reads the run's `plan.json`, scores each trial whose task id starts
with `prose-reader-`, and writes one row per trial (configuration, task, arm,
repeat, accuracy, invalid repeats, the deterministic verdict) plus means per
configuration, task, and arm. It skips and counts trials whose status is not
`valid` and trials with no `edited.md`. Outputs are never overwritten. Add
`--claude-bin` for a specific binary and `--jobs` to change how many reader
calls run at once (default 4).

## Calibration

Checked 2026-11-20 with `claude-haiku-5-5` on Claude Code 2.1.329, three
repeats each, every repeat valid:

| Case               | Draft accuracy | Oracle accuracy |
| ------------------ | -------------- | --------------- |
| `handoff-report`   | 0.00           | 1.00            |
| `status-update`    | 0.00           | 1.00            |
| `review-reply`     | 0.00           | 1.00            |
| `incident-summary` | 0.00           | 1.00            |

On every draft the reader chose "The text does not say" for all questions.
Rewrites of the two development drafts that fixed style but kept the coined
labels also scored 0.00, so the measure tracks recovered context, not polish.
The 24 calibration calls plus 6 probe calls cost about 0.018 USD.

## What this cannot establish

- A model reader is a proxy for a human reader. It tolerates dense, compressed
  prose far better than a person does, so a high score shows that the facts
  asked about are recoverable, not that the text is easy to read. Blind human
  review still decides readability.
- Accuracy rewards completeness. An edit that pastes `notes.md` wholesale can
  score well; read accuracy together with the word ratio and human review.
- The questions sample what a cold reader needs; they do not cover every fact.
  An edit can answer all of them and still drop or distort something else.
- These are public, synthetic cases. "Holdout" here means not yet used to tune
  a skill, not private. Do not read or tune against the holdout cases before
  freezing a skill edit, and once a holdout informs an edit, retire it to
  development and write a replacement.
- The reader instructions ask for "The text does not say" when the text is
  silent. A different reader model or instruction changes the floor, so pin
  both and compare runs only under the same reader configuration.

The two holdout cases (`review-reply`, `incident-summary`) were used in the confirmation run of 2026-11-20 and now count as development cases. The manifest labels them `development`. Confirming any later skill edit needs new cases.
