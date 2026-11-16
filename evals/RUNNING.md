# Running skill evaluations

Start with the [experimental protocol](PROTOCOL.md).
For shell execution, action traces, scripted turns, and subtraction experiments, see [EXTENDING.md](EXTENDING.md). The bundled pilot is a synthetic plumbing test, not an efficacy benchmark. Its oracle supplies known answers without calling a model.

## Verify the runner

From the repository root:

```sh
python3 scripts/skill_eval.py validate evals/pilot.json
mkdir -p evals/runs
python3 scripts/skill_eval.py plan evals/pilot.json \
  --output evals/runs/smoke-plan.json --repeats 1 --seed 42
python3 scripts/skill_eval.py run evals/runs/smoke-plan.json \
  --output evals/runs/smoke
python3 scripts/skill_eval.py report evals/runs/smoke
```

Plans and run directories must be new. Use a new name for another attempt. The runner checks input hashes before and after each trial and invalidates a trial if inputs changed. Keep source files frozen during execution; this detects changes but is not an immutable filesystem snapshot. Private runs are ignored by Git. A run contains the frozen plan, per-trial request, workspace, stdout/stderr, metrics when supplied, and result. Missing cost stays unknown.

Run `make test` for runner, adapter, grader, and existing repository regressions. The [seed case notes](cases/README.md) explain exactly what each grader establishes.

## Configure an experiment

Copy the suite manifest into a private experiment directory and resolve its fixture, prompt, skill, adapter, and grader paths relative to that manifest. Use absolute paths when moving a manifest out of `evals/`. Each task declares its family, development or holdout split, relevant skills, raw prompt, fixture directory, and grader argv. Declare helper files imported by a grader in `grader_inputs` so their content is frozen too. Each configuration declares its model, harness, adapter argv, and settings. Declare imported adapter helpers in `adapter_inputs` so changing them invalidates a frozen plan. Commands are argument arrays, never shell templates.

The runner calls an adapter with an absolute request JSON path appended to its argv. The request identifies the workspace, private HOME, prompt file, exposed skill directory, arm, configuration, and optional metrics output path. The adapter owns session isolation, provider configuration, and enforcement of the declared tools. It writes artifacts into the workspace. A nonzero adapter exit remains an invalid infrastructure attempt with logs, excluded from outcome differences and counted separately.

The grader receives the workspace path as its final argument and emits JSON with a boolean `passed` and individual `checks`. Grader failure remains visible. Structural checks do not settle semantic quality: inspect `requires_human_review` before interpreting success.

Metrics may contain `cost_usd`, `tokens`, and `skills_loaded`. Leave unavailable measurements absent. A self-reported read is weaker evidence than an observed tool event.

For real runs, replace the synthetic adapter with an audited provider adapter. The included `scripts/eval_claude.py` supports controlled file tasks; `scripts/eval_container.py` adds shell execution in a pinned Docker image. Consult the extension guide for configuration. Its custom discovery catalog does not reproduce native plugin discovery. Freeze the chosen CLI version and model with the run. Execute untrusted model output and its graders in a disposable environment.

## Improve a skill

Retain an incumbent run before editing the skill. Describe the failure mechanism and predicted outcome, edit the relevant skill, and create a new candidate plan. Reuse task identities, fixtures, graders, configuration, and repeats. Compare candidate and incumbent, inspect changed outcomes, and confirm worthwhile improvements on fresh holdouts. The report is descriptive; promotion follows the protocol's predeclared effect, cost, and preservation criteria.

The public seeds are development material. Supplying `--split holdout` does not turn familiar tasks into untouched evidence. Add genuinely new tasks before confirmation. No automatic skill rewrite, commit, or publication occurs during evaluation.

## Extension contracts

Add tasks by supplying a raw prompt, fixture directory, independent grader, family, split, and relevant skill names. No runner change is needed. Add providers by implementing the request-file adapter contract; keep provider flags and response parsing inside the adapter. Graders may use any language that can emit the result JSON contract. The runner uses only Python's standard library.

Manifest and request schemas carry version 1. An incompatible schema change should introduce a new version and migration, with a recorded fixture from the previous version proving how old evidence is handled. Keep old runs immutable; never silently reinterpret their metrics. Test new adapters against fake provider output before spending on a calibration run. Confirm exposure and grader isolation in the actual execution environment before measuring efficacy.

Compare two recorded revisions with:

```sh
python3 scripts/skill_eval.py compare \
  evals/runs/incumbent evals/runs/candidate
```

The comparison rejects changes to non-skill inputs and reports candidate-minus-incumbent outcomes, missing pairs, and resource totals. An identical configuration label is not evidence that a provider served an identical model: inspect recorded CLI versions and served model IDs as part of acceptance.

For the controlled Claude adapter, replace the synthetic configuration with:

```json
{
  "id": "claude-file-tools",
  "model": "<pinned model id>",
  "harness": "Claude Code <pinned version>; controlled-file-tools-catalog",
  "adapter": ["python3", "../scripts/eval_claude.py"],
  "adapter_inputs": ["../scripts/eval_trace.py"],
  "settings": {
    "effort": "high",
    "claude_version": "<exact claude --version output>",
    "expected_served_models": ["<served model id>"],
    "claude_bin": "/absolute/path/to/claude"
  }
}
```

Adapter paths in that example assume a manifest under `evals/`. Authentication must work in the isolated trial environment; the runner does not copy personal credentials into trial homes. The model and binary placeholders must be replaced before execution.
