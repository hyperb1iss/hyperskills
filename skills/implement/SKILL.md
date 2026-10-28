---
name: implement
description: Use this skill when writing code, building features, fixing bugs, refactoring, or performing multi-step implementation work. Activates on mentions of implement, build this, code this, start coding, fix this bug, refactor, make changes, develop this feature, coding task, write the code, or start building.
---

# Implementation

The user's instructions take precedence over this skill; carry existing authorization forward, finish the work within scope, and do not add approval gates.

## Orient to the Change

Before editing, inspect status and existing diffs on touched files; the checkout is shared space, so never run autofix across other agents' work. Trace behavior through actual callers and consumers. Find the nearest existing instance of the pattern in the repository, and any prior work in project memory, before building new structure; name it. Search by syntax for structure and by text for names. Recheck volatile API and dependency claims against current primary evidence. "Why does this happen?" calls for a confirmed cause first, then a check that distinguishes broken from intended behavior.

## Select a Verifiable Slice

| Situation                                       | Next move                                                      |
| ----------------------------------------------- | -------------------------------------------------------------- |
| Clear, low-impact edit                          | Edit, then run the relevant structural or behavioral check     |
| Bug with an observable failure                  | Reproduce it, isolate the cause, then verify the correction    |
| New behavior across boundaries                  | Implement a representative end-to-end slice with its tests     |
| Shared interface or schema change               | Trace consumers and compatibility before changing the contract |
| Large uncertain change                          | Use `plan` for dependencies and acceptance criteria            |
| Independent work with a useful integration path | Use authorized delegation and explicit ownership               |

Keep implementation and verification together. File count and edit count are not cadence rules. Run the cheapest check that can expose the next likely failure before building on it.

## Keep the Design Accountable

| Pressure                                                                 | Decision                                                                                                                                                        |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New modes or configuration appear                                        | Tie each to a requested behavior or demonstrated variation                                                                                                      |
| The same decision repeats across callers                                 | Give that decision one owner                                                                                                                                    |
| A wrapper only forwards calls                                            | Check whether it enforces an API, policy, or test boundary before removing it                                                                                   |
| A cast conceals incompatible data                                        | Fix or validate the contract at its actual boundary                                                                                                             |
| A fallback hides an error                                                | Preserve the failure cause and make the intended recovery explicit                                                                                              |
| Compatibility code grows                                                 | Check shipped consumers and rollout requirements before keeping or deleting it                                                                                  |
| A flag, legacy mode, fallback, or staged gate appears                    | Name the ship state (pre-launch, single consumer, production with users) and the exact failure it prevents; pre-launch and single-consumer code deletes instead |
| A value enumerates today's instances, or a tool knows its author's setup | Derive the value from a rule, or move it to configuration                                                                                                       |
| Complexity keeps increasing                                              | Re-examine ownership and data flow before adding another special case                                                                                           |

Judge the concepts and contracts, not line count: an abstraction can earn its place before a second caller when it enforces a real boundary. Remove imports and dead branches your own change creates. Route unrelated findings to the sidequest or issue workflow; do not absorb them silently.

For a scale problem, identify the contended resource and fix isolation, indexing, batching, ownership, or capacity at the cause. A temporary concurrency reduction must not quietly become permanent.

## Verify the Claim You Intend to Make

| Check                         | What it can establish                        | Common limit                                  |
| ----------------------------- | -------------------------------------------- | --------------------------------------------- |
| Type/static analysis          | Selected type and structural properties      | Does not execute runtime behavior             |
| Focused behavioral test       | The intended cases exercise the changed path | Mocks may bypass integration                  |
| Package or integration checks | Contracts between affected components hold   | May omit packaging or deployment differences  |
| Build/package validation      | The artifact can be produced                 | Does not prove it can be installed or used    |
| Consumer check                | The artifact serves its intended consumer    | Limited to the observed environment and cases |

Preserve exit codes and raw failure logs; a pipeline into `tail` can hide a failed command, and do not impose arbitrary timeouts on a check to make it finish. A filter selecting zero intended tests does not verify the change. Cached results are legitimate when their inputs match, but disclose them. A useful receipt names the command, revision or working-tree state, environment, exit status, and what actually ran.

### Check the Consumption Boundary

| Artifact                | Representative proof                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------ |
| Generated configuration | Inspect composed output for the motivating invariant                                       |
| Package                 | Install and invoke the built distribution without undeclared sibling dependencies          |
| UI                      | Exercise the changed interaction in the real surface, using `agent-browser` when available |
| CLI                     | Invoke the relevant command, including affected error/default paths                        |
| Database migration      | Apply against representative schema/data and check compatibility or rollback requirements  |
| Service                 | Confirm the running revision and exercise the changed request path                         |

Check the invariant, not merely that the command succeeded. A valid selector can match nothing, a package can build without files the importer needs, and a merged fix can leave the deployed artifact unchanged.

Detectors and guards need positive and negative evidence. Performance changes need a baseline, a representative workload, and the relevant resource measurements. For a surface you cannot observe or a live check you may not run, give the human a discriminating procedure and expected result; do not invent a screenshot or verdict.

## Recover by Updating the Hypothesis

Classify a failure before editing again (environment, stale artifact, invocation, shared-output race, runtime defect). Preserve the original error and find the first failing dependency instead of fixing downstream symptoms. Repeating variations without new evidence is the signal to reframe, regardless of attempt count. The same applies to review rounds: when findings keep landing in one class, restructure or cut the mechanism rather than patch it again, keep the larger head on a backup ref, and file the hardening separately.

A failure on the base can show that a symptom predates the change; missing changed filenames in a trace cannot. A successful rerun does not establish harmless flakiness. Detailed procedures live in `references/recovery.md`.

## Review and Commit Coherent Work

Follow the project's commit policy and commit verified logical chunks. Stage explicit owned paths or hunks and inspect the staged patch. At a commit checkpoint, compare the total diff to the task; green tests can coexist with unnecessary scope. Push and merge authority comes from the user, not this skill. The `git` skill covers shared-index handling.

Obtain independent verification when consequence or run length justifies it (shared or production state, an unattended run past a checkpoint, an acceptance check the implementer cannot alter) or when the project contract requires it. When none of those triggers applies, do not spawn a verifier to double-check a small change you can verify in a handful of tool calls. The verdict must arrive from a separate dispatch, because a model rarely corrects an error sitting in its own reasoning. Use `cross-model-review` when available; a different model exposes blind spots but does not eliminate correlated errors. Tie the verdict to the reviewed state, and report incomplete review as incomplete.

## Preserve the State and Finish

At handoff or compaction, preserve the original outcome, user corrections, changed paths, revision, checks run, unresolved findings, and next step. Sweep for processes this session started before reporting done. Reinspect status on resumption.

## Evidence and References

Read `references/benchmarks.md` when interpreting benchmark or workflow claims. Read `references/recovery.md` for CI triage, intermittent failures, and incident recovery.

Reviewed 2026-09-04 and 2026-10-27; sources and their limits are in `references/evidence.md`.

## Anti-Patterns

| Anti-pattern                                  | Better move                                                        |
| --------------------------------------------- | ------------------------------------------------------------------ |
| Verify after an arbitrary number of edits     | Verify before relying on a new uncertain contract                  |
| Run every suite for a small change            | Run required and relevant gates; expand for evidence-based reasons |
| Accept a green badge without coverage         | Inspect what ran and what assertion it supports                    |
| Call an issue pre-existing from an empty grep | Compare controlled executions and trace causality                  |
| Treat reviewer approval as consumer proof     | Test the changed behavior where its output is used                 |

## What This Skill is NOT

- A fixed sequence, edit budget, mandatory research phase, or agent quota.
- Permission to change adjacent code, bypass approvals, or claim unrun checks.
- A replacement for understanding the actual implementation and its consumers.
