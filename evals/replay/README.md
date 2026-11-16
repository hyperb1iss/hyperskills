# Fix replay

Replay turns real fix commits from a target repository into evaluation cases. The agent receives the tree as it stood before the fix and a description of the bug. The grader runs the tests the fix commit itself shipped. The cases are real in size and shape, and the repository's own tests do the grading.

The suite in `suite.json` targets [Sibyl](https://github.com/hyperb1iss/sibyl), a public Python monorepo. Only commit identities, test names, and task prompts live here. Source trees are exported from a local clone into an ignored directory.

## How a case is built

A commit qualifies when it is a `fix` that touches only Python, changes at most three source files and 80 source lines, and ships at least one test. `build.py validate` then runs the commit's test files twice inside the pinned image with networking disabled: once on the parent tree with the fix's tests laid over it, and once on the fix. Tests that go from not passing to passing are the case's `fail_to_pass` set. Tests that pass both times are `pass_to_pass`. A commit with no test that changes state, or with a test that is not green after the fix, is rejected.

Of 63 candidates from a 120-day window, 54 validated. The ten development cases and ten holdout cases here were chosen by hand from those, preferring tests that check behavior through existing entry points. A test that names a symbol the fix introduced would fail any correct fix that chose another name.

Each prompt in `prompts/` describes the symptom and the required behavior. It does not name the file or function.

## Run it

Export the dependency base and build the image, then materialize cases and run:

```sh
mkdir -p evals/runs/replay-image/tree
git -C ~/dev/sibyl archive <dependency_base> apps/api apps/cli packages/python \
  pyproject.toml uv.lock .python-version VERSION \
  | tar -x -C evals/runs/replay-image/tree
docker build --build-arg CLAUDE_VERSION=<version> -t hyperskills-replay:local \
  -f evals/replay/Dockerfile evals/runs/replay-image
docker image inspect --format '{{.Id}}' hyperskills-replay:local

python3 evals/replay/build.py --repo ~/dev/sibyl materialize \
  --output evals/runs/replay-pilot --configurations <configurations.json>
python3 scripts/skill_eval.py plan evals/runs/replay-pilot/manifest.json \
  --output evals/runs/replay-plan.json --repeats 3
python3 scripts/skill_eval.py run evals/runs/replay-plan.json \
  --output evals/runs/replay-run
```

The configurations file is a JSON list in the shape [EXTENDING.md](../EXTENDING.md) gives for the container adapter, with absolute adapter paths. The image is about 2.8 GB. Its virtual environment holds the dependencies locked at `dependency_base`, so a commit whose code needs a since-removed dependency fails validation and never becomes a case.

To add cases, run `build.py validate --image <id> --output <file> <sha>...` and copy the `tests`, `fail_to_pass`, and `pass_to_pass` of an accepted commit into `suite.json` beside a new prompt.

## What the grader reports

A trial passes when every `fail_to_pass` and `pass_to_pass` test is green on the submitted tree with the fix commit's test files laid over it. The grader also reports two observations that do not affect the verdict:

- `submission_changed_tests` lists the test files the submission added or edited.
- `ships_regression_test` says whether any of those tests is a regression test for the fix. The grader runs the submission's test files on the submitted tree, then on the pre-fix tree with only the submission's test files laid over it. A test that fails before and passes after counts. `own_tests` carries the detail, including tests that could not be collected before the fix, which are kept apart because an import error is weaker evidence than a failed assertion.

## Pilot, 2026-11-13

Claude Code 2.1.323, shell adapter, low effort, ten cases. Sonnet 5.5 ran three repeats per arm and Fable 5.2 ran one.

| Model      | Arm                 | Passed   | Wrote or changed a test |
| ---------- | ------------------- | -------- | ----------------------- |
| Sonnet 5.5 | no skill            | 30 of 30 | 1 of 30                 |
| Sonnet 5.5 | implement preloaded | 30 of 30 | 9 of 30                 |
| Sonnet 5.5 | catalog             | 29 of 30 | 4 of 30                 |
| Fable 5.2  | no skill            | 10 of 10 | 7 of 10                 |
| Fable 5.2  | implement preloaded | 10 of 10 | 10 of 10                |
| Fable 5.2  | catalog             | 10 of 10 | 9 of 10                 |

No trial was invalid. The Sonnet run cost $5.33 and the Fable run $17.26.

Correctness is saturated for both models, so these cases cannot show a skill making a fix more often right. The arms differ in whether a test ships with the fix. Every source commit shipped one. Without a skill Sonnet almost never did, and preloading implement raised that to about a third. Fable usually wrote one unprompted.

## Holdout comparison, 2026-11-15

The pilot suggested one edit to `implement`: say plainly that a bug fix ships a regression test. The edit was written before any holdout case ran. Ten holdout cases then compared the skill as it stood against the edited copy, on the arm that preloads the skill, with Sonnet 5.5 at low effort.

| Arm                         | Passed   | Shipped a regression test |
| --------------------------- | -------- | ------------------------- |
| no skill (one repeat)       | 10 of 10 | 1 of 10                   |
| implement as it stood       | 19 of 20 | 5 of 20                   |
| implement with the new line | 20 of 20 | 14 of 20                  |

"Shipped a regression test" is the stronger check: a test of the submission's own that fails on the pre-fix tree and passes on the fix. With the new line, seven of the ten cases shipped one in both repeats and three shipped none in either. In those three the final report said no test was added. The three runs cost $0.64, $1.71, and $1.77, so the line did not raise cost.

Regrading the pilot's saved trials with the same check found a real regression test in 39 of the 40 trials that had changed a test file. The exception was the single no-skill Sonnet trial, so that row of the pilot table is 0 of 30 under the stronger check.

To compare two revisions of a skill, materialize once, copy the manifest with only `skills_root` changed, plan both with `--split holdout --arms explicit`, and run `skill_eval.py compare` on the two run directories.

## Limits

- The prompts were written from the fix commits' messages, so they hand over the diagnosis. A report that gave only the symptom would be harder and might leave correctness headroom.
- `pass_to_pass` covers only the test files the fix touched. A regression elsewhere in the project goes unseen.
- The pilot table counts changed test files. The holdout table uses the stronger check, which sees only tests under the case's own project.
- The holdout comparison is two repeats per case on one model. Fable 5.2 was not run on the holdouts.
- No catalog-arm trial opened the skill file, so its test-writing counts are not a skill effect.
- All twenty cases were picked by hand from one repository. The other 34 validated commits are unused.
- The Fable column is one repeat per case.
