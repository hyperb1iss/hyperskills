---
name: orchestrate
description: Use this skill when coordinating independent agents with explicit ownership, dependencies, integration, and verification. Activates on mentions of swarm, parallel agents, multi-agent, orchestrate, fan-out, wave dispatch, research army, unleash, dispatch agents, or parallel work.
---

# Multi-Agent Orchestration

The coordinator owns integration and the final claim of completion.

The user's instructions take precedence over this skill; delegation, tools, and external actions remain subject to current host instructions and authorization, and this skill grants a worker no authority the coordinator lacks.

## Check Capabilities Before Dispatch

Inspect the actual tools and current schemas instead of inferring capabilities from a product name. An external CLI reviewer is still delegation, not an escape hatch.

## Choose the Shape by Dependency

| Work shape                              | Coordination pattern                                      |
| --------------------------------------- | --------------------------------------------------------- |
| Independent research questions          | Parallel investigators, evidence-based synthesis          |
| Disjoint features, stable interfaces    | Parallel builders, designated integration owner           |
| One change repeated across modules      | Scoped transform or partitioned workers, combined checks  |
| Dependent edits or shared mutable state | One owner for the dependency, parallel work around it     |
| Consequential review                    | Independent read-only reviewers with distinct risk lenses |
| Small, tightly coupled change           | Direct execution                                          |

Agent count follows named useful lanes, not historical fleet sizes. Check the critical path: a branch waiting on one shared interface gains nothing from more agents. Delegate when the work splits across independent surfaces and keep working while workers run; do not use a worker to double-check a small change you can verify yourself in a handful of tool calls.

## Establish Ownership and Integration

Map shared resources as well as files: generated artifacts, schemas, lockfiles, fixtures, ports, build outputs, and caches collide across otherwise disjoint modules.

| Isolation                   | Appropriate use                     | Required coordination                                  |
| --------------------------- | ----------------------------------- | ------------------------------------------------------ |
| Shared tree, disjoint paths | Small changes with clear ownership  | One owner for contended files and the Git index        |
| Separate worktrees          | Independent branches or build state | Known base, branch, merge order, and integration owner |
| Read-only revision          | Review or research                  | Fixed revision or diff plus permitted scratch outputs  |

Worktrees isolate tracked files and the index, not ports or databases. Never overwrite a human's or sibling's edits to clear a conflict. In a shared tree, workers report patches while one coordinator stages and commits. Investigate a lock's actual owner before removing it.

Before dispatch, define how partial progress becomes integrated progress: the artifact each consumer expects and when it is ready.

## Write Briefs

Give each worker the original request plus facts absent from their checkout, such as user corrections and untracked decisions.

| Brief element     | Purpose                                                               |
| ----------------- | --------------------------------------------------------------------- |
| Outcome and scope | Result needed, owned surfaces, exclusions                             |
| Current evidence  | Code, versions, interfaces, verified premises                         |
| Dependencies      | What is ready, what is promised, who owns it                          |
| Authority         | Permitted mutations, commit rights, external actions                  |
| Verification      | Checks and acceptance conditions                                      |
| Return            | Changed artifacts or findings, evidence, limits, justified deviations |

Let workers challenge a premise. A first independent review gets the raw change without coaching; a follow-up verification gets the finding and the fix claim so it can test closure. Templates are in `references/dispatch-briefs.md`.

## Supervise

Harvest dependency-ready results as they arrive. Silence alone does not prove an agent is stuck; check its artifacts before interrupting. Polling must respect the host's limits. When requirements change, tell the affected workers.

A watcher needs a completion condition, failure detection, an expiry, and a stale-state check, with its signal tested on a known state. Cancel only processes this run owns.

## Harvest, Integrate, Verify

A worker's summary is a claim; inspect the actual diffs. Integrate at a stable checkpoint and run checks covering the combined behavior.

The implementer cannot certify an independent PASS. Tie each verdict to a revision or recorded snapshot.

| Verdict    | Meaning                                                         |
| ---------- | --------------------------------------------------------------- |
| PASS       | Declared scope completed, no unresolved blocking findings       |
| FAIL       | A supported defect violates the requested outcome or contract   |
| INCOMPLETE | Review or a required check did not finish; list uncovered scope |

An interrupted review cannot grant a full PASS. Agreement does not establish severity; impact does. Do not reuse a PASS for changed runtime code.

## Finish With an Honest State

Report integrated outcomes, the checks run and their revision, unresolved limits, and any blocked gate with the action it needs. Capture durable coordination failures in project memory: the contended resource, mechanism, fix, and conditions.

## Evidence

Reviewed 2026-09-04 and 2026-10-27; sources and their limits are in `references/evidence.md`.

## Anti-Patterns

| Anti-pattern                                        | Better move                                            |
| --------------------------------------------------- | ------------------------------------------------------ |
| Choose a fleet size before finding independent work | Name useful lanes and their integration path           |
| Assume different files imply isolation              | Inspect shared runtime resources and generated outputs |
| Let all shared-tree workers commit concurrently     | Assign ownership of the index and commit operation     |
| Vote-count findings                                 | Verify mechanism and impact                            |
| Reduce review automatically over time               | Match checks to current risk and changed evidence      |

## References

Read `references/dispatch-briefs.md` when composing worker, research, verification, or watcher instructions.

## What This Skill is NOT

- Permission to ignore host delegation rules or user ownership.
- A fixed pipeline, agent quota, or requirement to use multiple agents.
- A substitute for integrated verification or the coordinator's judgment.
