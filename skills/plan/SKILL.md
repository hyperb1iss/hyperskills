---
name: plan
description: Use this skill when decomposing complex work into verifiable tasks and dependencies before or during implementation. Activates on mentions of write a plan, create a plan, break this down, task decomposition, implementation plan, what are the steps, plan the work, spec this out, or decompose this feature.
---

# Structured Planning

Build a plan that another session can execute and verify without rediscovering the decision. Specify outcomes and dependencies tightly enough to prevent drift while leaving implementation choices to the code and evidence encountered during execution.

The user's instructions take precedence over this skill's guidelines. Planning does not add an approval requirement. If execution is already authorized, continue after the plan is ready; if the user requested only a plan, deliver the plan without starting implementation.

## Size the Plan by Uncertainty

| Work shape                                      | Planning depth                                                       |
| ----------------------------------------------- | -------------------------------------------------------------------- |
| Clear, reversible change with a direct check    | Execute with a brief mental or inline plan                           |
| Several dependent behaviors with known patterns | Record tasks, interfaces, and acceptance checks                      |
| Uncertain architecture or migration             | Resolve decisive unknowns and plan a representative vertical slice   |
| Work spanning agents, sessions, or environments | Preserve ownership, state, dependencies, and resumption instructions |

File count is a poor proxy for risk. A one-line authorization change can need more analysis than a mechanical rename across many files. Plan enough to expose the uncertain or irreversible parts, not enough to predict every edit.

## Establish the Actual Starting Point

Inspect repository status, relevant diffs, and the code path under discussion. Locate an existing implementation pattern and the real verification commands in scripts, hooks, or CI. Read relevant project memory through the installed Sibyl skill when configured.

Record the facts that constrain execution:

- The observable user or system outcome.
- The current baseline and revision or environment being inspected.
- The interfaces, ownership, and compatibility obligations affected.
- The uncertainty that could invalidate the proposed work.
- The explicit constraints, non-goals, and user corrections.

Treat an inherited plan as a hypothesis. Recheck consequential claims against the current tree before executing them. Distinguish verified facts, assumptions awaiting a check, and obsolete premises. Update the plan itself when a premise fails; a detached comment leaves the executor following stale instructions.

## Choose a Useful Slice

Look for existing capabilities that can satisfy the request before decomposing a new mechanism. Simplification must preserve the requested result. Do not replace a difficult product goal with a convenient demonstration of plumbing.

Prefer a vertical slice through the uncertain boundary when it can prove feasibility early: a real input passing through the changed logic to the consumer that needs it. Plan migrations around compatibility and deployment order. Source-file order does not determine safe rollout order.

Keep implementation and its behavioral verification in the same accountable task. A title containing "and" is not evidence that the task should split. Separate tasks when they have independently reviewable outcomes, distinct owners, or real dependency boundaries. A test-infrastructure prerequisite may be separate; feature tests should not become an orphaned follow-up.

## Give Each Task an Executable Contract

Use only the fields the task needs:

| Field               | Content                                                                  |
| ------------------- | ------------------------------------------------------------------------ |
| Outcome             | The behavior or artifact delivered                                       |
| Scope               | Known files/modules and permitted expansion rules                        |
| Dependencies        | Required inputs or interfaces, with their producer                       |
| Verification        | Exact runnable check plus the behavior it proves                         |
| Completion evidence | Expected artifact, assertion, observation, or report                     |
| Risk and recovery   | Compatibility, rollback, or unresolved external dependency when material |

Example:

```markdown
### Task: Reject expired sessions at the request boundary

Outcome: An expired session receives the established unauthorized response.
Scope: The session validator and its request-level tests.
Depends on: The existing clock injection interface, confirmed in the repo.
Verify: [repository's exact focused test command].
Cases: Expired, valid, and boundary-time sessions preserve expected behavior.
Completion: Tests exercise the request path and report executed cases.
```

Prefer real file paths where known; label proposed paths instead of pretending exploration is complete. A copyable command still needs an assertion: "renders" does not prove that the generated policy matches the intended resources.

## Map Dependencies and Ownership

Parallelize independent outcomes. File separation helps avoid collisions but does not prove independence: two modules can share a schema, generated file, test database, port, or output directory. Name those shared resources and their owners.

Choose dependency-ready work rather than forcing every task into synchronized waves. A wave is useful when tasks share a meaningful integration checkpoint. Designate an integration owner and verify combined behavior after branches or patches meet. Consult `orchestrate` when delegation adds useful capacity and current instructions permit it.

Review the plan for missing consumers, incompatible rollout states, and unnecessary scope. For consequential architecture or policy, seek independent critique when required or justified. Keep the review aimed at unresolved decisions. More rounds are useful only when new evidence or concrete defects improve the plan; disagreement alone does not justify endless revision.

## Make the Plan Resumable

Use the project's canonical tracker or agreed artifact location. With Sibyl, use its installed skill for current task and memory commands. Avoid duplicating the full plan in chat, repository files, and memory; select one authoritative plan and link to it from the tracker.

Do not create or commit planning documents merely because work spans sessions. Follow repository rules about scratch files and planning artifacts. If a document is required, place it where future agents can actually access it, and include untracked context in delegated briefs when their checkouts will not contain it.

A useful checkpoint records the current revision, completed outcomes and evidence, active ownership, pending decisions, and exact next step. Preserve user corrections that would otherwise be lost during compaction. Re-read the checkpoint and inspect live state on resumption; notes describe a past state, not a guarantee of the current one.

## Replan Without Losing the Goal

When implementation exposes a new constraint, change the affected tasks and explain its impact on the outcome, dependencies, or risk. Carry corrections through tables and acceptance criteria, not just the edited paragraph. Preserve rejected alternatives only when their rationale helps future decisions.

At integration boundaries, compare the accumulated diff with the intended outcome. Tests can pass while scope drifts. Review intensity follows changed risk and coverage, not task number or how many earlier tasks passed. Mandatory project verification still applies to late work.

Mark completed work only when the required evidence exists. Report an unavailable external gate separately from completed local checks, with its exact blocker and next action. Follow the host's task-state rules when recording blocked status; this skill does not redefine them.

## Evidence and Limits

Reviewed 2026-09-04. Anthropic's [March 2026 harness report](https://www.anthropic.com/engineering/harness-design-long-running-apps) describes outcome-oriented specifications and negotiated verification criteria, while observing that repeated evaluation can also increase implementation complexity. It is an engineering case study, not proof that every project needs a planner-generator-evaluator pipeline.

The procedures here use that distinction: preserve a testable contract and adapt the execution path. Evaluate planning changes through resulting work and correction cost, not the size of the plan.

## Anti-Patterns

| Anti-pattern                                 | Better move                                       |
| -------------------------------------------- | ------------------------------------------------- |
| Exact edit predictions before reading code   | Specify verified boundaries and uncertain details |
| Separate every feature from its tests        | Keep one owner accountable for delivered behavior |
| Parallelize based only on filenames          | Inspect shared interfaces and runtime resources   |
| Demand approval after authorization to build | Continue within the existing scope                |
| Ease review because the task is late         | Match review to current risk and evidence         |
| Maintain several competing progress ledgers  | Keep one authoritative plan with linked receipts  |
| Keep decomposing after success is covered    | Execute; replan when evidence changes the work    |

## What This Skill is NOT

- A requirement for trivial work or a fixed file-count threshold.
- Permission to execute a plan-only request.
- A promise that an initial architecture, schedule, or task list cannot change.
