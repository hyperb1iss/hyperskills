---
name: plan
description: Use this skill when decomposing complex work into verifiable tasks and dependencies before or during implementation. Activates on mentions of write a plan, create a plan, break this down, task decomposition, implementation plan, what are the steps, plan the work, spec this out, or decompose this feature.
---

# Structured Planning

The user's instructions take precedence over this skill; carry existing authorization forward and do not add approval gates. If the user requested only a plan, deliver the plan without starting implementation.

## Size the Plan by Uncertainty

| Work shape                                      | Planning depth                                                     |
| ----------------------------------------------- | ------------------------------------------------------------------ |
| Clear, reversible change with a direct check    | Execute with a brief inline plan                                   |
| Several dependent behaviors with known patterns | Record tasks, interfaces, and acceptance checks                    |
| Uncertain architecture or migration             | Resolve decisive unknowns and plan a representative vertical slice |
| Work spanning agents, sessions, or environments | Preserve ownership, state, dependencies, and resumption steps      |

File count is a poor proxy for risk: a one-line authorization change can need more analysis than a mechanical rename across many files.

## Establish the Actual Starting Point

Inspect repository status and relevant diffs, and locate the real verification commands in scripts, hooks, or CI. Record the facts that constrain execution:

- The observable user or system outcome.
- The baseline revision or environment inspected.
- Affected interfaces, ownership, and compatibility obligations.
- Uncertainty that could invalidate the work.
- Explicit constraints, non-goals, and user corrections.

Treat an inherited plan as a hypothesis: recheck consequential claims against the current tree before executing them. When a premise fails, update the plan itself, because a detached comment leaves the executor on stale instructions.

## Choose a Useful Slice

Prefer a vertical slice that carries a real input through the uncertain boundary to the consumer that needs it. Sequence migrations by compatibility and deployment; source-file order does not determine safe rollout order.

Keep implementation and its behavioral verification in the same accountable task. A title containing "and" is not evidence that the task should split; split at independently reviewable outcomes, distinct owners, or real dependency boundaries.

## Give Each Task an Executable Contract

Use only the fields the task needs:

| Field               | Content                                                                  |
| ------------------- | ------------------------------------------------------------------------ |
| Outcome             | Behavior or artifact delivered                                           |
| Scope               | Known files/modules and permitted expansion rules                        |
| Dependencies        | Required inputs or interfaces, with their producer                       |
| Verification        | Exact runnable check plus the behavior it proves                         |
| Completion evidence | Expected artifact, assertion, observation, or report                     |
| Risk and recovery   | Compatibility, rollback, or unresolved external dependency when material |

```markdown
### Task: Reject expired sessions at the request boundary

Outcome: An expired session receives the established unauthorized response.
Scope: The session validator and its request-level tests.
Depends on: The existing clock injection interface, confirmed in the repo.
Verify: [repository's exact focused test command].
Cases: Expired, valid, and boundary-time sessions preserve expected behavior.
Completion: Tests exercise the request path and report executed cases.
```

A copyable command still needs an assertion: "renders" does not prove that the generated policy matches the intended resources.

## Map Dependencies and Ownership

File separation does not prove independence: two modules can share a schema, generated file, test database, port, or output directory. Name those shared resources and their owners. Designate an integration owner who verifies combined behavior after branches or patches meet.

## Make the Plan Resumable

Select one authoritative plan and link it from the project's tracker rather than duplicating it across chat, repository files, and memory. Do not create or commit planning documents merely because work spans sessions.

A checkpoint records the current revision, completed outcomes and evidence, active ownership, pending decisions, and the exact next step. On resumption, re-read the checkpoint and inspect live state; notes describe a past state.

## Replan Without Losing the Goal

When implementation exposes a new constraint, carry the correction through tables and acceptance criteria, not just the edited paragraph. At integration boundaries, compare the accumulated diff with the intended outcome; tests can pass while scope drifts.

Report an unavailable external gate separately from completed local checks, with its blocker and next action.

## Evidence

Reviewed 2026-09-04 and 2026-10-27; sources and their limits are in `references/evidence.md`.

## Anti-Patterns

| Anti-pattern                               | Better move                                    |
| ------------------------------------------ | ---------------------------------------------- |
| Exact edit predictions before reading code | Specify verified boundaries, mark uncertainty  |
| Separate every feature from its tests      | Keep one owner accountable for the behavior    |
| Parallelize based only on filenames        | Inspect shared interfaces and runtime state    |
| Ease review because the task is late       | Match review to current risk and evidence      |
| Keep decomposing after success is covered  | Execute; replan when evidence changes the work |

## What This Skill is NOT

- A requirement for trivial work or a fixed file-count threshold.
- Permission to execute a plan-only request.
- A promise that an initial architecture, schedule, or task list cannot change.
