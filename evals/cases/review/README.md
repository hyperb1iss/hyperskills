# Review

Synthetic pull requests that measure two things a code reviewer has to get right: finding a real defect, and staying quiet when there is none. Each case comes in a pair. The defect case is a plausible pull request doing legitimate work with one defect inside it. Its clean twin is the same pull request with only that defect corrected: same description, same diff apart from the fix. Recall comes from the defect cases, precision from the clean twins, and comparing a reviewer's results across a pair shows whether a finding tracked the defect or the shape of the change.

Two lessons from earlier review evals shaped the cases. A prompt that states the diagnosis measures nothing, so the prompt is identical everywhere and never names a defect class. A tiny diff whose only change is the defect gives the answer away, so every diff is 80 to 200 lines across at least three files, with at least two legitimate hunks besides the one that matters, and the fixture tree includes code the diff does not touch.

## Cases

| Pair (defect / clean)                           | Split       | Class                | Trap              |
| ----------------------------------------------- | ----------- | -------------------- | ----------------- |
| `edge-value` / `edge-value-clean`               | development | edge-value           |                   |
| `batch-stop` / `batch-stop-clean`               | development | batch-stop           |                   |
| `silent-failure` / `silent-failure-clean`       | development | silent-failure       |                   |
| `anchoring` / `anchoring-clean`                 | development | non-idempotent-retry | anchoring         |
| `cross-file` / `cross-file-clean`               | development | unit-mismatch        | cross-file        |
| `test-stays-green` / `test-stays-green-clean`   | development | stale-cache          | test-stays-green  |
| `fail-open` / `fail-open-clean`                 | holdout     | fail-open            |                   |
| `unbounded-growth` / `unbounded-growth-clean`   | holdout     | unbounded-growth     |                   |
| `bugfix-regression` / `bugfix-regression-clean` | holdout     | silent-data-loss     | bugfix-regression |
| `instruction-file` / `instruction-file-clean`   | holdout     | cross-tenant-read    | instruction-file  |

Each `case.json` is authoritative; this table is a convenience. The five classes without a trap come from a week of a human reviewer's findings on real pull requests:

- **edge-value**: a wrong number or label at a boundary, such as an off-by-one at a limit or a count that is wrong for zero or one item.
- **batch-stop**: one bad item stops the whole batch, so every other item's work is lost.
- **silent-failure**: a failure with no signal, such as a swallowed error that the caller sees as success.
- **fail-open**: a guard that allows when its input is missing or malformed.
- **unbounded-growth**: a cache, map, or queue that only grows on some path.

A trap names a reviewer failure mode the pair is built to provoke beyond the defect class itself; `null` means the case tests the class alone.

## Case contract

| Path                  | Shown to the reviewer | Purpose                                                                                                            |
| --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `fixture/`            | yes                   | The pull request's head tree: a small Python package of 4 to 7 source files plus tests, 300 to 700 lines           |
| `fixture/change.diff` | yes                   | Unified diff of the pull request against its base; it applies in reverse to the head tree                          |
| `fixture/PR.md`       | yes                   | The author's description of the legitimate work; it never mentions the defect                                      |
| `prompt.md`           | yes                   | The task, byte-identical in every case                                                                             |
| `case.json`           | no                    | Split, kind, twin, class, trap, the defect span, and other acceptable anchors                                      |
| `proof/test_proof.py` | no                    | A unittest that fails on the defect fixture and passes on the clean twin's; both twins carry the same file         |
| `oracle/review.json`  | no                    | A correct review                                                                                                   |
| `wrong/review.json`   | no                    | A plausible wrong review: an approval or an irrelevant finding on a defect case, a blocking finding on a clean one |

`case.json` holds `split` (`development` or `holdout`), `kind` (`defect` or `clean`), `twin`, `class`, `trap`, and `also_accept`. A defect case adds `defect`: `{"file", "start_line", "end_line", "function"}`, the responsible lines in the head tree and the name of the function that encloses them. `also_accept` lists other `{"file", "start_line", "end_line"}` spans where a correct finding could reasonably anchor, such as the call site that triggers the defect or the test that fails to cover it. It may be empty, and it is always empty on a clean case.

The fixture's own tests pass in both twins; the defect is the part the pull request's tests miss. Nothing in a fixture points at the defect: no TODO, no comment near it, no test named after it. The clean twin changes only the defect lines, plus an `also_accept` file when the fix needs it (a test that encoded the defective behavior, for instance), and its `change.diff` differs from the defect case's only in those files' sections.

## Grading

`grade.py CASE WORKSPACE` reads the trusted `CASE/case.json` and `CASE/fixture/`, then grades `WORKSPACE/review.json`. It prints one JSON object with `passed`, `checks`, `metrics`, `case`, `trap`, `grading_scope`, and `requires_human_review: true`, and always exits zero.

Every case checks:

- `fixture_unchanged`: every fixture file is byte-identical in the workspace. New files, including `__pycache__`, do not fail; they are listed in `metrics.extra_files`.
- `review_readable`: `review.json` exists and parses. A missing or unparsable file fails with an `error` saying which.
- `review_shape`: `verdict` is `approve` or `needs_changes`, and every finding has a nonempty `file`, a positive integer `line`, a boolean `blocking`, and string `title`, `trigger`, and `impact`, with a nonempty title. A blocking finding also needs a nonempty trigger and impact. Problems are listed in `error`.

A defect case then checks `defect_found_strict`: some blocking finding names the defect file with a line within 3 lines of the defect span, or names a line inside an `also_accept` span. A clean case checks `no_blocking_findings`. `passed` is the conjunction of the case's checks.

Finding paths are matched after removing a leading `./`, a diff-style `a/` or `b/`, or the absolute workspace prefix; a bare file name that matches exactly one tree file is accepted too. The verdict field is shape-checked but does not decide the outcome; a defect case that approves with the right blocking finding still passes, and the mismatch is visible in `metrics.verdict`.

`metrics` never affects `passed`:

| Metric                 | Meaning                                                                                                                                   |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `verdict`              | The review's verdict                                                                                                                      |
| `findings`             | Well-formed findings                                                                                                                      |
| `blocking`             | Of those, how many are blocking                                                                                                           |
| `other_blocking`       | Blocking findings that match neither the defect window nor an `also_accept` span; every blocking finding on a clean case                  |
| `nonblocking`          | Findings marked nonblocking                                                                                                               |
| `anchors_outside_diff` | Whether any finding names a file the diff does not touch                                                                                  |
| `unknown_files`        | Finding paths that match no tree file                                                                                                     |
| `defect_found_loose`   | Defect cases only: a blocking finding anywhere inside the enclosing function (found with `ast` on the head file) or an `also_accept` span |
| `extra_files`          | Files present in the workspace but not the fixture, apart from `review.json`                                                              |

## What a result does and does not establish

`requires_human_review` is always true. A matching anchor does not prove the reviewer understood the defect: a blocking finding on the right line can describe a different, imaginary problem, and the grader never reads `trigger` or `impact`. Before counting a strict pass as a find, a person checks that the finding's trigger would actually exercise the defect and its impact matches what the proof test demonstrates. A clean pass does not prove a careful review either, since an empty approval passes every clean case.

A fail is more specific but not final. A reviewer can find a real issue the case author did not plant; on a clean case that fails the case. Read `other_blocking` findings before counting a clean-case fail as a false positive, and if one is a genuine defect, record it as a fixture defect and replace the case rather than editing it mid-run. A correct finding anchored outside the window and outside every `also_accept` span fails strict and usually shows up in `defect_found_loose`; widen `also_accept` in a new revision, not during a run.

The cases are synthetic, small, single-language, and have one planted defect each. Pass rates here say how a reviewer does on these pull requests, not on real ones, and the class list reflects one reviewer's week, not a census.

## Thresholds

All thresholds are author-chosen and carry no external validation:

| Threshold         | Value                                 | Reason                                                                                                                                   |
| ----------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Strict window     | 3 lines either side of the span       | Reviewers anchor the condition, the statement it guards, or the line after; 3 covers that without reaching unrelated code in these files |
| Loose scope       | The enclosing function                | Separates "found the right function, wrong line" from a miss, for diagnosis only                                                         |
| Fixture size      | 4 to 7 source files, 300 to 700 lines | Enough code that the defect is one part of a real change, small enough to review in one sitting                                          |
| Diff size         | 80 to 200 lines, at least 3 files     | Keeps the defect from being the whole diff                                                                                               |
| Hint check radius | 10 lines either side of the span      | Covers the surrounding block where a stray comment would point at the defect                                                             |

## Development and holdout hygiene

Tune skill wording against development cases only. Whoever edits a skill must not read a holdout's fixture, `case.json`, proof, oracle, or wrong review before freezing that edit; the split and class in the table above are the most they should know. Once a holdout informs an edit, it becomes development material: relabel both twins and write a replacement pair with new content. These files are public, so "holdout" means "not used to tune the current candidate", not "private".

When running trials, only `fixture/` belongs in the reviewer's workspace. Keep `case.json`, `proof/`, `oracle/`, `wrong/`, and the grader outside anything the reviewer can read. A manifest task for a case uses id `review-<case>`, family `review`, the case's split, `prompt.md`, `fixture/`, grader argv `["python3", "cases/review/grade.py", "<case>"]`, and `grader_inputs` naming the fixture directory and `case.json`.

## Tests

```sh
python3 evals/cases/review/test_review.py
```

The tests run over every case directory present. They check the layout, that `prompt.md` is identical everywhere, the `case.json` schema and that the declared function encloses the defect span, the fixture and diff size limits, that twins pair up and share `PR.md`, prompt, and proof, that twin trees and diffs differ only where the contract allows, that `change.diff` applies in reverse to the head tree (with `git apply --check -R`), and that no hint word sits near the defect. They run each fixture's own tests in both twins and each proof against both, requiring a test failure (not an import error) on the defect and a pass on the clean twin. They check that every oracle passes and every wrong review fails on its outcome check, and pin the grader's edges: missing, malformed, and misshapen reviews, a modified fixture, an unknown case, path spellings, the strict window boundaries, the loose function scope, nonblocking findings at the defect, `also_accept` anchors, and metrics that must not affect `passed`.
