# Failure-class screen

Nine small coding cases, one per failure class a careful reviewer raises first: a failing item stopping a batch, a dropped record leaving no trace, a mistyped config value disabling a protection, a regression test that stays green without the fix, a retention set that grows without bound, two labels wrong at an edge, and a choice the request never covered going unreported. The ninth, `discard-trace`, is a second instance of the dropped-record class in a different domain, marked `holdout`.

Each fixture holds a sibling function that shows the convention. The prompt asks for the feature and stays silent about the class. `grade.py` reports `feature_passed` and `class_passed` separately, so a run shows whether the model built the thing and whether it avoided the failure.

`test_screen.py` checks the graders in both directions: each `oracle/` solution passes every check, and each untouched fixture fails. Keep `oracle/` and the graders out of the agent's workspace.

## What the first run established

On 2026-11-11, Claude Fable 5.2 and Claude Sonnet 5.5 each ran the eight cases three times in each arm (no skill, `implement` preloaded, discovery catalog) through the controlled file-tools adapter at high effort, Claude Code 2.1.322. All 144 trials passed every feature and class check, with no invalid trials. Loading `implement` roughly doubled the cost of a trial and changed no outcome.

Read that narrowly. With the convention one file away in a repository of three files, neither model makes these mistakes, so these cases cannot show whether a skill helps. They are saturated: use them as regression checks on the harness and graders, not as evidence about a skill. The reviewer findings these classes come from were raised on pull requests in a large repository after long sessions, which this screen does not reproduce. Three repeats, one effort level, file tools only.

## Where headroom appeared

The same screen at low effort, same day, three repeats: Fable 5.2 again passed everything. Sonnet 5.5 failed two cases, and the traces show why: at low effort it never opened the sibling file, so it never saw the convention. Ten repeats per arm on those two cases:

| Sonnet 5.5, low effort | No skill | `implement` preloaded | Discovery |
| ---------------------- | -------- | --------------------- | --------- |
| `batch-isolation`      | 0 of 10  | 9 of 10               | 0 of 10   |
| `silent-drop`          | 0 of 10  | 0 of 10               | 0 of 10   |

The preloaded skill rescued the case its self-review row describes, without the model reading the sibling. It did not rescue `silent-drop`, where the request itself says malformed lines are skipped. The discovery arm never loaded the skill.

A candidate skill tree widened that row to cover a record skipped on purpose. With it preloaded, `silent-drop` passed 8 of 10 and `batch-isolation` 10 of 10. That is a development result: the wording was written against that case. The held-out `discard-trace` case could not confirm it, because it is saturated even at low effort (19 of 20 with no skill, 20 of 20 with either wording), run on Claude Code 2.1.323 after the CLI updated.

So the evidence for a skill effect is one class, one model, one effort level, on small fixtures. It shows the instrument can detect an effect when one exists, and that a skill only helps where it is loaded and its wording reaches the situation.
