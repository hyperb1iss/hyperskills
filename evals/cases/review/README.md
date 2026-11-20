# Review

Synthetic pull requests that measure two things a code reviewer has to get right: finding real defects, and staying quiet when there are none. Each case comes in a pair. The defect case is a plausible pull request doing legitimate work with one or more defects inside it. Its clean twin is the same pull request with only those defects corrected: same description, same diff apart from the fixes. Recall comes from the defect cases, precision from the clean twins, and comparing a reviewer's results across a pair shows whether a finding tracked the defect or the shape of the change.

Two lessons from earlier review evals shaped the cases. A prompt that states the diagnosis measures nothing, so the prompt is identical everywhere and never names a defect class. A tiny diff whose only change is the defect gives the answer away, so every diff carries legitimate hunks besides the ones that matter, and the fixture tree includes code the diff does not touch.

There are two tiers. A single-defect pair is a small pull request (80 to 200 diff lines) with one defect. A large pair is a pull request of 500 to 800 diff lines across 8 to 14 files with three independent defects of different classes in different files and at different depths: one near the top of the diff, one deep in it, and one in how two changed parts interact. The large tier exists because the single-defect cases proved too easy: in the first baseline both models found most of those defects without the skill. It measures recall on a larger change with several issues.

## Cases

| Pair (defect / clean)                           | Split       | Class                | Trap              |
| ----------------------------------------------- | ----------- | -------------------- | ----------------- |
| `edge-value` / `edge-value-clean`               | development | edge-value           |                   |
| `batch-stop` / `batch-stop-clean`               | development | batch-stop           |                   |
| `silent-failure` / `silent-failure-clean`       | development | silent-failure       |                   |
| `anchoring` / `anchoring-clean`                 | development | non-idempotent-retry | anchoring         |
| `cross-file` / `cross-file-clean`               | development | unit-mismatch        | cross-file        |
| `test-stays-green` / `test-stays-green-clean`   | development | stale-cache          | test-stays-green  |
| `large-ledger` / `large-ledger-clean`           | development | multi-defect         |                   |
| `large-dev-b` / `large-dev-b-clean`             | development | multi-defect         |                   |
| `fail-open` / `fail-open-clean`                 | holdout     | fail-open            |                   |
| `unbounded-growth` / `unbounded-growth-clean`   | holdout     | unbounded-growth     |                   |
| `bugfix-regression` / `bugfix-regression-clean` | holdout     | silent-data-loss     | bugfix-regression |
| `instruction-file` / `instruction-file-clean`   | holdout     | cross-tenant-read    | instruction-file  |
| `large-holdout-a` / `large-holdout-a-clean`     | holdout     | multi-defect         |                   |
| `large-holdout-b` / `large-holdout-b-clean`     | holdout     | multi-defect         |                   |

Each `case.json` is authoritative; this table is a convenience. A large pair's class is `multi-defect`, and each of its defects carries its own class. Five classes come from a week of a human reviewer's findings on real pull requests:

- **edge-value**: a wrong number or label at a boundary, such as an off-by-one at a limit or a count that is wrong for zero or one item.
- **batch-stop**: one bad item stops the whole batch, so every other item's work is lost.
- **silent-failure**: a failure with no signal, such as a swallowed error that the caller sees as success.
- **fail-open**: a guard that allows when its input is missing or malformed.
- **unbounded-growth**: a cache, map, or queue that only grows on some path.

A trap names a reviewer failure mode the pair is built to provoke beyond the defect class itself; `null` means the case tests the class alone.

## Case contract

| Path                  | Shown to the reviewer | Purpose                                                                                                               |
| --------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `fixture/`            | yes                   | The pull request's head tree, a Python package with tests; sizes by tier below                                        |
| `fixture/change.diff` | yes                   | Unified diff of the pull request against its base; it applies in reverse to the head tree                             |
| `fixture/PR.md`       | yes                   | The author's description of the legitimate work; it never mentions a defect and claims nothing the tree does not hold |
| `prompt.md`           | yes                   | The task, byte-identical in every case                                                                                |
| `case.json`           | no                    | Split, kind, twin, class, trap, the defect spans, and other acceptable anchors                                        |
| `proof/test_proof.py` | no                    | Unittests that fail on the defect fixture and pass on the clean twin's; both twins carry the same file                |
| `oracle/review.json`  | no                    | A correct review                                                                                                      |
| `wrong/review.json`   | no                    | A plausible wrong review: one that misses a defect on a defect case, one with a blocking finding on a clean case      |

| Tier          | Diff                              | Tree                                                                    |
| ------------- | --------------------------------- | ----------------------------------------------------------------------- |
| Single defect | 80 to 200 lines, at least 3 files | 4 to 7 source files plus tests, 300 to 700 Python lines                 |
| Large         | 500 to 800 lines, 8 to 14 files   | 1,200 to 2,000 lines, counting every file but `change.diff` and `PR.md` |

`case.json` holds `split` (`development` or `holdout`), `kind` (`defect` or `clean`), `twin`, `class`, and `trap`. A single-defect case adds `defect`: `{"file", "start_line", "end_line", "function"}`, the responsible lines in the head tree and the name of the function that encloses them, and a top-level `also_accept` list of other `{"file", "start_line", "end_line"}` spans where a correct finding could reasonably anchor. A large case instead carries `defects`, a list of `{"id", "class", "file", "start_line", "end_line", "function", "also_accept"}` with distinct ids, classes, and files; its top-level `also_accept`, if present, is empty. A clean case carries an empty `also_accept`.

`also_accept` follows the defect's causal chain: the line that records or returns the wrong result, the caller that acts on it, the test that fails to cover it. It stops short of spans where an unrelated complaint about the same file would land.

The fixture's own tests pass in both twins; the defects are what the pull request's tests miss. Nothing in a fixture points at a defect: no TODO, no comment near it, no test named after it. Each fix in the clean twin stays within 3 lines of its defect span and may also touch that defect's `also_accept` files (a test that encoded the defective behavior, for instance); `change.diff` differs between twins only in those files' sections. A single-defect proof needs at least one failing test. A large proof has one test per defect, and every one of them fails on the defect tree.

## Grading

`grade.py CASE WORKSPACE` reads the trusted `CASE/case.json` and `CASE/fixture/`, then grades `WORKSPACE/review.json`. It prints one JSON object with `passed`, `checks`, `metrics`, `case`, `trap`, `grading_scope`, and `requires_human_review: true`, and always exits zero.

Every case checks:

- `fixture_unchanged`: every fixture file is byte-identical in the workspace. New files, including `__pycache__`, do not fail; they are listed in `metrics.extra_files`.
- `review_readable`: `review.json` exists and parses. A missing or unparsable file fails with an `error` saying which.
- `review_shape`: `verdict` is `approve` or `needs_changes`, and every finding has a nonempty `file`, a positive integer `line`, a boolean `blocking`, and string `title`, `trigger`, and `impact`, with a nonempty title. A blocking finding also needs a nonempty trigger and impact. Problems are listed in `error`.

A blocking finding matches a defect when it names the defect file at a line inside the function that encloses the defect span (found with `ast` on the head file), or a line inside one of that defect's `also_accept` spans. Each finding counts toward at most one defect, and each defect needs its own finding; the grader takes the largest such matching. A single-defect case checks `defect_found`, a large case checks `all_defects_found`, and a clean case checks `no_blocking_findings`. `passed` is the conjunction of the case's checks.

Finding paths are matched after removing a leading `./`, a diff-style `a/` or `b/`, or the absolute workspace prefix; a bare file name that matches exactly one tree file is accepted too. In baseline trials reviewers often numbered lines by their position in `change.diff` instead of in the file, so a line number past the end of the named file is read as a `change.diff` line when that diff line falls inside the same file's section, and mapped to the head line it shows (a removed line maps to the head line now in its place). A line number inside the file is always read as a file line. The verdict field is shape-checked but does not decide the outcome; the mismatch is visible in `metrics.verdict`.

`metrics` never affects `passed`:

| Metric                 | Meaning                                                                                                               |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `verdict`              | The review's verdict                                                                                                  |
| `findings`             | Well-formed findings                                                                                                  |
| `blocking`             | Of those, how many are blocking                                                                                       |
| `nonblocking`          | Findings marked nonblocking                                                                                           |
| `other_blocking`       | Blocking findings that match no defect; on a clean case, every blocking finding                                       |
| `anchors_outside_diff` | Whether any finding names a file the diff does not touch                                                              |
| `unknown_files`        | Finding paths that match no tree file                                                                                 |
| `diff_line_anchors`    | Findings whose line was read as a `change.diff` line                                                                  |
| `extra_files`          | Files present in the workspace but not the fixture, apart from `review.json`                                          |
| `defects_total`        | Defect cases: how many defects the case plants                                                                        |
| `defects_found`        | Defect cases: how many defects a blocking finding matched                                                             |
| `found_ids`            | Defect cases: which ones (a single defect has id `defect`)                                                            |
| `defects_found_strict` | Defect cases: matches under the strict rule, a line within 3 lines of the defect span or inside an `also_accept` span |
| `strict_ids`           | Defect cases: which ones matched strictly                                                                             |
| `defect_found_strict`  | Single-defect cases: whether the one defect matched strictly                                                          |

## What a result does and does not establish

`requires_human_review` is always true. A matching anchor does not prove the reviewer understood the defect: a blocking finding inside the right function can describe a different, imaginary problem, and the grader never reads `trigger` or `impact`. The function-wide rule makes that more likely than the strict one, which is why both are reported. Before counting a pass as a find, a person checks that the finding's trigger would actually exercise the defect and its impact matches what the proof test demonstrates. A clean pass does not prove a careful review either, since an empty approval passes every clean case.

A fail is more specific but not final. A reviewer can find a real issue the case author did not plant; on a clean case that fails the case. Read `other_blocking` findings before counting a clean-case fail as a false positive, and if one is a genuine defect, record it as a fixture defect and fix it in both twins in a new revision rather than mid-run. A correct finding anchored outside the enclosing function and every `also_accept` span fails; widen `also_accept` in a new revision, not during a run.

The cases are synthetic, single-language, and small even in the large tier. Pass rates here say how a reviewer does on these pull requests, not on real ones, and the class list reflects one reviewer's week, not a census.

## Thresholds

All thresholds are author-chosen and carry no external validation:

| Threshold         | Value                                          | Reason                                                                                                                                                |
| ----------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pass scope        | The enclosing function, plus `also_accept`     | Baseline trials gave the right diagnosis anchored 5 to 10 lines from the span, so a narrow window failed correct findings                             |
| Strict window     | 3 lines either side of the span, metric only   | Keeps the tighter reading visible next to the pass rule                                                                                               |
| Diff-line reading | Only for a line past the end of the named file | A line inside the file cannot be told apart from a diff line, so it is never reinterpreted                                                            |
| Tier sizes        | See the tier table                             | Small enough to review in one sitting, large enough that the defects are a part of the change; the large tier is several times the single-defect size |
| Hint check radius | 10 lines either side of each span              | Covers the surrounding block where a stray comment would point at a defect                                                                            |

## Development and holdout hygiene

Tune skill wording against development cases only. Whoever edits a skill must not read a holdout's fixture, `case.json`, proof, oracle, or wrong review before freezing that edit; the split and class in the table above are the most they should know. Once a holdout informs an edit, it becomes development material: relabel both twins and write a replacement pair with new content. These files are public, so "holdout" means "not used to tune the current candidate", not "private".

When running trials, only `fixture/` belongs in the reviewer's workspace. Keep `case.json`, `proof/`, `oracle/`, `wrong/`, and the grader outside anything the reviewer can read. A manifest task for a case uses id `review-<case>`, family `review`, the case's split, `prompt.md`, `fixture/`, grader argv `["python3", "cases/review/grade.py", "<case>"]`, and `grader_inputs` naming the fixture directory and `case.json`.

## Tests

```sh
python3 evals/cases/review/test_review.py
```

The tests run over every case directory present. They check:

- **Contract:** the layout, an identical `prompt.md` everywhere, the `case.json` schema in both forms (including that each declared function encloses its span and that a large case's defects have distinct ids, classes, and files), and the size limits of each tier.
- **Twins:** that twins pair up and share `PR.md`, prompt, and proof, that twin trees and diffs differ only where the contract allows, that `change.diff` applies in reverse to the head tree (with `git apply --check -R`), and that no hint word sits near a defect.
- **Execution:** each fixture's own tests in both twins, and each proof against both twins, requiring test failures (not import errors) on the defect tree, one per defect in a large case, and a pass on the clean twin.
- **Grading:** every oracle passes with every defect found and every wrong review fails on its outcome check. The grader's edges are pinned too: missing, malformed, and misshapen reviews, a modified fixture, an unknown case, path spellings, a finding anywhere in the enclosing function, the strict metric's window, nonblocking findings at a defect, `also_accept` anchors, a review that misses one of three defects, one finding never counting for two defects, diff-numbered lines past the end of a file, and metrics that must not affect `passed`.
