# Failure-class screen

Eight small coding cases, one per failure class a careful reviewer raises first: a failing item stopping a batch, a dropped record leaving no trace, a mistyped config value disabling a protection, a regression test that stays green without the fix, a retention set that grows without bound, two labels wrong at an edge, and a choice the request never covered going unreported.

Each fixture holds a sibling function that shows the convention. The prompt asks for the feature and stays silent about the class. `grade.py` reports `feature_passed` and `class_passed` separately, so a run shows whether the model built the thing and whether it avoided the failure.

`test_screen.py` checks the graders in both directions: each `oracle/` solution passes every check, and each untouched fixture fails. Keep `oracle/` and the graders out of the agent's workspace.

## What the first run established

On 2026-11-11, Claude Fable 5.2 and Claude Sonnet 5.5 each ran the eight cases three times in each arm (no skill, `implement` preloaded, discovery catalog) through the controlled file-tools adapter at high effort, Claude Code 2.1.322. All 144 trials passed every feature and class check, with no invalid trials. Loading `implement` roughly doubled the cost of a trial and changed no outcome.

Read that narrowly. With the convention one file away in a repository of three files, neither model makes these mistakes, so these cases cannot show whether a skill helps. They are saturated: use them as regression checks on the harness and graders, not as evidence about a skill. The reviewer findings these classes come from were raised on pull requests in a large repository after long sessions, which this screen does not reproduce. Three repeats, one effort level, file tools only.
