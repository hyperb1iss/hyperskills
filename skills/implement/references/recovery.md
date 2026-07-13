# Recovery Protocols

Deep-dive companions to the Error Recovery and Verification Cadence sections of SKILL.md. Distilled from the Apr–Jul 2026 transcript corpus (~600 sessions across Claude Code and Codex hosts).

## CI Triage Protocol

CI red gets a taxonomy before any edit. Misclassification is where thrash starts; each class gets a different response.

| Failure class            | Tell                                                        | Response                                                        |
| ------------------------ | ----------------------------------------------------------- | --------------------------------------------------------------- |
| Infra noise              | LFS budget exceeded, checkout death, runner lost comms      | Rerun or report; the checks never reached lint/tests            |
| Install/env              | First gate fails on package install, missing workspace link | Fix the environment; don't touch code                           |
| Runner/shell syntax      | Error points at the invocation, not the diff                | Fix the command; the patch was never exercised                  |
| Stale artifact           | "Missing" symbols that exist in source; old `dist`/`.d.ts`  | Rebuild, cache-bust, confirm the running thing is your build    |
| Self-induced race        | Parallel jobs building the same output                      | Rerun sequentially once; don't serialize permanently            |
| Base drift / pre-existing | Same failure on main at your base commit                   | Exonerate by absence, then rebase — don't "fix" it in-branch    |
| Downstream cascade       | Jobs failing because an upstream image/step never produced  | Collapse to the root; ignore the echoes                         |
| Actual code              | None of the above                                           | Hypothesis → targeted fix → verify with the judging invocation  |

### Log handling

Download the raw job log to a file with its exit code, then mine the file. Grepping the live firehose catches filename noise instead of the failure — "That grep caught filename noise, not the failure" is a real observed miss. Collapse a red wall to its root failure before responding to any individual line.

### Reproduce with the judging gate's semantics

Local proof counts only when the invocation matches the gate that judges the work: the literal CI command, CI's coverage flags, `CI=true`, the same env gates, the same base ref (`GITHUB_BASE_REF=main` — bare local diff-against-HEAD~1 proves nothing). Known traps: package scripts that swallow file args and widen the suite; local defaults diverging from check defaults; env-gated suites that silently skip. Approximations have missed real bugs — twice. When local and CI gates diverge, promote the missing CI check to a standing local step.

### Exoneration by absence

Proving a red check isn't yours takes three legs, and the empty result is the receipt:

1. Grep the failing logs for your change's failure signature — find none.
2. Show the base commit (or main) red in the same places, matching failure signatures.
3. Rebase rather than patch a non-bug, and name the failure pre-existing in your report.

### Suspect your own instrument

When the probe says dead but state says perfect, audit the probe before the system: timeouts shorter than cold-start, regexes that match everything, stale auth, env pollution. Judge liveness by work progress, not one indirect signal. Test watchers like production code — an awk "not-ready" counter that matched every line reported a phantom outage for hours.

## Flake Evidence Standard

"Flaky" is a verdict, not a shrug. It requires independent legs:

- The failure trace doesn't intersect the diff (exonerating grep comes back empty — keep the empty result as the receipt).
- The same failure appears on main or a sibling/stacked PR carrying the same code. Stacked PRs give a free control group: a superset can't be greener than its base unless the base's extra reds are noise.
- The exact CI-shaped invocation passes locally.
- Infra annotations corroborate (runner lost communication, API 5xx).

Flake status is revocable: recurrence reopens the verdict, no matter who applied the label — a user-declared "flake" has turned out to be a deterministic collision the branch itself seeded. A rerun that fails again is too hot to call a flake.

## Incident Mode

Production on fire changes the grammar. The arc that repeatedly worked:

1. **Freeze.** Stop mutations, go read-only. "Breathe — stop pruning anything else right now" precedes every clean recovery. Look at what actually happened before touching anything.
2. **Park.** Stash or branch uncommitted in-flight work so the fix diff stays pure and mergeable.
3. **Two tracks.** Hotfix pinned to the exact deployed revision for the unblock, plus a separate clean main-based PR for the durable fix. Label the temporary track explicitly and own its removal; execute relax → act → verify → restore in the same motion.
4. **Scars become guards.** Before closing, convert every live snag into a durable artifact: a preflight check, a regression test, an alert, a runbook line. The autopsy becomes the forward procedure.
5. **Sibling sweep.** Run the same-trap check across sibling environments and clusters — the same expired credential has been live in six other places.

Rules that hold mid-incident: mutation gates still apply (the pitch compresses to the exact command, not zero review); mission-scope re-litigation is banned — never ask whether the burning system should exist; and the completeness bar doesn't drop because it's an emergency.
