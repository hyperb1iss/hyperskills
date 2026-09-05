---
name: orchestrate
description: Use this skill when coordinating independent agents with explicit ownership, dependencies, integration, and verification. Activates on mentions of swarm, parallel agents, multi-agent, orchestrate, fan-out, wave dispatch, research army, unleash, dispatch agents, or parallel work.
---

# Multi-Agent Orchestration

Use independent agents to add useful capacity while keeping one coherent result. Partition by the questions, artifacts, and resources that can progress independently. The coordinator owns integration and the final claim of completion.

The user's instructions take precedence over this skill's guidelines. Delegation, tools, and external actions remain subject to current host instructions and authorization. This skill does not grant a worker broader authority than the coordinator has.

## Check Capabilities Before Dispatch

Inspect the available tools and their current schemas. Hosts differ in agent lifecycle, inherited context, filesystem sharing, worktree isolation, asynchronous results, and permissions. Discover those properties instead of inferring them from a product name or copying stale arguments.

Use the host's supported delegation tools when permitted. An external CLI reviewer still consumes resources and remains subject to delegation and permission rules; it is not an escape hatch around a restriction. Without a suitable delegation surface, execute directly or prepare tasks for authorized external workers. A task queue alone does not launch an agent.

## Choose the Shape by Dependency

| Work shape                                        | Coordination pattern                                                     |
| ------------------------------------------------- | ------------------------------------------------------------------------ |
| Independent research questions                    | Parallel investigators, evidence-based synthesis                         |
| Disjoint feature ownership with stable interfaces | Parallel builders, designated integration owner                          |
| One change repeated across modules                | Scoped automated transform or partitioned workers, combined verification |
| Dependent edits or shared mutable state           | One owner for the dependency, parallelize work around it                 |
| Consequential review                              | Independent read-only reviewers with useful risk lenses                  |
| Small, tightly coupled change                     | Direct execution                                                         |

Agent count follows named useful lanes, available capacity, and integration cost. More agents are worthwhile when they add distinct evidence or shorten independent work. Do not use historical fleet sizes as defaults. Check the critical path: accelerating a branch that is already waiting on one shared interface may add no throughput.

## Establish Ownership and Integration

Before launching builders, inspect repository status and existing worktrees. Map shared resources as well as files: generated artifacts, schemas, lockfiles, database fixtures, ports, build outputs, and package caches can collide across otherwise disjoint modules.

Choose isolation based on the work:

| Isolation                   | Appropriate use                                  | Required coordination                                       |
| --------------------------- | ------------------------------------------------ | ----------------------------------------------------------- |
| Shared tree, disjoint paths | Small independent changes with clear ownership   | Single owner for contended files and Git index operations   |
| Separate worktrees          | Workers need independent branches or build state | Known base, branch/path, merge order, and integration owner |
| Read-only revision          | Review or research                               | Fixed revision/diff plus permitted scratch outputs          |

Worktrees isolate tracked files and the index; they do not automatically isolate ports, databases, or external services. Follow the project's worktree layout. Never overwrite a human's or sibling's edits to clear a conflict.

For shared trees, let workers report patches and checks while one coordinator stages and commits scoped changes, unless another explicit ownership scheme is agreed. Avoid broad staging and repository-wide autofixes during concurrent editing. Inspect hook side effects before accepting a commit. For lock contention, investigate the actual owner; an inconclusive process listing does not establish that a lock is safe to remove. Consult `git` for recovery.

Define how partial progress becomes integrated progress before dispatch. Name the artifact each consumer expects and the condition under which it is ready. Do not leave completed branches without an owner to inspect and combine them.

## Write Briefs That Transfer the Necessary Context

Give each worker the original relevant request and a bounded assignment. Include facts that are expensive to rediscover or absent from their checkout, especially user corrections and untracked decisions. Use absolute paths and exact revisions when location matters.

| Brief element     | Purpose                                                                    |
| ----------------- | -------------------------------------------------------------------------- |
| Outcome and scope | The result needed, owned surfaces, and exclusions                          |
| Current evidence  | Relevant code, versions, interfaces, and verified premises                 |
| Dependencies      | What is ready, what is promised, and who owns it                           |
| Authority         | Permitted mutations, commit rights, external actions                       |
| Verification      | Checks and acceptance conditions for this contribution                     |
| Return            | Changed artifacts or findings, evidence, limitations, justified deviations |

Allow workers to challenge a premise and report necessary scope expansion. Their brief should constrain the task, not force a known-bad mechanism. Keep mandatory templates short; detailed examples live in `references/dispatch-briefs.md`.

For an independent first review, provide the original request and raw change without coaching toward the implementer's desired conclusion. For follow-up verification, include the finding and fix claim so the reviewer can test closure. These are different review jobs.

## Supervise Without Becoming the Bottleneck

Launch independent work together and continue useful local work. Harvest dependency-ready results as they arrive rather than waiting for an arbitrary wave to finish. Use waves when there is a real shared checkpoint or a method needs calibration before wider dispatch.

Monitor results, tool status, artifact progress, and reported obstacles. Silence alone does not prove an agent is stuck. When progress stops, ask a discriminating question or inspect the relevant resource before interrupting. Keep user steering responsive; polling and waits must respect the host's actual limits.

When requirements change, notify affected workers and update the shared contract. Preserve completed valid work. Stop obsolete actions at a safe point, and cancel only processes or watchers this run owns. Report abandoned work and any side effects already taken.

A watcher needs a checkable completion condition, a way to detect failure, an expiry or escalation condition, and a stale-state check before any authorized action. Test its signal on a known state. Detailed watcher guidance is in `references/dispatch-briefs.md`.

## Harvest, Integrate, Verify

Read deviations and limitations alongside the result. Inspect actual diffs and open consequential sources; a worker's summary is a claim, not evidence. An incomplete contribution may contain usable work, but acceptance depends on inspecting it against the task, not its length or the worker's confidence.

Integrate at a stable checkpoint, then run checks that cover the combined behavior. Separate worker tests can miss incompatible assumptions between interfaces. Confirm the accumulated diff still serves the user's outcome and explicit constraints.

For non-trivial changes where the project requires independent verification, obtain it before completion. The implementer can report its checks but cannot certify an independent PASS. Additional reviewers should cover distinct risks or provide a deliberately independent assessment; no finding count is a target.

Tie review evidence to a revision or recorded working-tree snapshot and environment. Use these verdicts:

| Verdict    | Meaning                                                                  |
| ---------- | ------------------------------------------------------------------------ |
| PASS       | The declared review scope completed with no unresolved blocking findings |
| FAIL       | A supported defect violates the requested outcome or applicable contract |
| INCOMPLETE | Review or a required check did not finish; list uncovered scope          |

An interrupted review cannot grant a full PASS. Agreement does not establish severity; impact and exploitability do. Adjudicate disagreements through the code, specification, or a reproducer. A reproduced base failure can distinguish regression from pre-existing behavior, but neither label substitutes for analyzing the changed path.

After changes, reassess which reviewed claims are invalidated and re-verify affected behavior plus relevant integration. Do not reuse a PASS for changed runtime code. A documentation-only change need not trigger unrelated runtime checks unless project policy requires them.

## Finish With an Honest State

Report integrated outcomes, actual checks and their revision, unresolved limits, and the location of remaining artifacts. When an external gate is unavailable, complete independent authorized work and name the exact blocker and action needed. Follow the host's rules for recording task/goal status; do not claim completion for unverified required work.

Capture durable coordination failures through configured project memory: the contended resource, failure mechanism, fix, and conditions. Keep ephemeral logs and worker chatter out of permanent guidance.

## Evidence and Limits

Reviewed 2026-09-04. Anthropic's [multi-agent research case study](https://www.anthropic.com/engineering/multi-agent-research-system) supports explicit scope and parallel independent investigations, while warning about coordination and token overhead. Research results do not establish a best coding-agent count.

The [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) recommends making delegation expectations explicit. Apply that within the actual host contract; API capabilities do not prove a particular CLI exposes them.

## Anti-Patterns

| Anti-pattern                                        | Better move                                            |
| --------------------------------------------------- | ------------------------------------------------------ |
| Choose a fleet size before finding independent work | Name useful lanes and their integration path           |
| Assume different files imply isolation              | Inspect shared runtime resources and generated outputs |
| Treat an external reviewer as a policy bypass       | Apply the same authority and permission boundaries     |
| Give partial review a forced binary verdict         | Report INCOMPLETE with the missing coverage            |
| Vote-count findings                                 | Verify mechanism and impact                            |
| Let all shared-tree workers commit concurrently     | Assign ownership of the index and commit operation     |
| Reduce review automatically over time               | Match checks to current risk and changed evidence      |

## References

Read `references/dispatch-briefs.md` when composing worker, research, verification, or watcher instructions.

## What This Skill is NOT

- Permission to ignore host delegation rules or user ownership.
- A fixed pipeline, agent quota, or requirement to use multiple agents.
- A substitute for integrated verification or the coordinator's judgment.
