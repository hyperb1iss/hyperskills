# Fix replay

Replay turns real fix commits from a target repository into evaluation cases. The agent receives the tree as it stood before the fix and a description of the bug. The grader runs the tests the fix commit itself shipped. The cases are real in size and shape, and the repository's own tests do the grading.

The suite in `suite.json` targets [Sibyl](https://github.com/hyperb1iss/sibyl), a public Python monorepo. Only commit identities, test names, and task prompts live here. Source trees are exported from a local clone into an ignored directory.

## How a case is built

A commit qualifies when it is a `fix` that touches only Python, changes at most three source files and 80 source lines, and ships at least one test. `build.py validate` then runs the commit's test files twice inside the pinned image with networking disabled: once on the parent tree with the fix's tests laid over it, and once on the fix. Tests that go from not passing to passing are the case's `fail_to_pass` set. Tests that pass both times are `pass_to_pass`. A commit with no test that changes state, or with a test that is not green after the fix, is rejected.

Of 63 candidates from a 120-day window, 54 validated. The ten cases here were chosen by hand from those, preferring tests that check behavior through existing entry points. A test that names a symbol the fix introduced would fail any correct fix that chose another name.

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

A trial passes when every `fail_to_pass` and `pass_to_pass` test is green on the submitted tree with the fix commit's test files laid over it. The grader also reports `submission_changed_tests`: the test files the submission added or edited. That field is an observation and does not affect the verdict.

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

## Limits

- The prompts were written from the fix commits' messages, so they hand over the diagnosis. A report that gave only the symptom would be harder and might leave correctness headroom.
- `pass_to_pass` covers only the test files the fix touched. A regression elsewhere in the project goes unseen.
- The test-writing count says a test file changed. It does not say the test fails without the fix.
- No catalog-arm trial opened the skill file, so its test-writing counts are not a skill effect.
- The ten cases were picked by hand from one repository. The other 44 validated commits are unused and can serve as holdouts.
- The Fable column is one repeat per case.
