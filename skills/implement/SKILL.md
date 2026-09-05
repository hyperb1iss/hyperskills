---
name: implement
description: Use this skill when writing code, building features, fixing bugs, refactoring, or performing multi-step implementation work. Activates on mentions of implement, build this, code this, start coding, fix this bug, refactor, make changes, develop this feature, coding task, write the code, or start building.
---

# Implementation

Deliver the requested behavior with evidence from the code path and the place where its output is consumed. Choose the smallest useful feedback loop for the change; increase verification when uncertainty, integration, or consequences increase.

The user's instructions take precedence over this skill's guidelines. Carry existing authorization forward and finish the work within scope. Resolve routine reversible choices with stated assumptions when useful. Ask only when missing information materially changes the result or an applicable boundary requires it; a skill workflow does not itself create a new approval gate.

## Orient to the Change

Inspect repository status before edits and read existing diffs on touched files. Treat the checkout as shared space. Preserve work you did not create and respect claimed ownership.

Trace the behavior through its actual callers and consumers. Locate the nearest relevant pattern, tests, and real gate commands. Search by syntax when the question concerns code structure; use text search for names and prose. Read enough to understand the change, without a minimum file-read count or a broad context dump.

Recall non-obvious prior decisions through the configured memory workflow. Recheck volatile API, dependency, and deployment claims against current primary evidence or the installed version. Load specialized tool guidance when the task needs it, rather than guessing unfamiliar flags.

Distinguish diagnosis from implementation. "Why does this happen?" calls for a confirmed cause first. Once fixing is authorized, define a check that can distinguish the broken and intended behaviors.

## Select a Verifiable Slice

| Situation                                       | Next move                                                         |
| ----------------------------------------------- | ----------------------------------------------------------------- |
| Clear, low-impact edit                          | Make the edit and use the relevant structural or behavioral check |
| Bug with an observable failure                  | Reproduce it, isolate the cause, then verify the correction       |
| New behavior across boundaries                  | Implement a representative end-to-end slice with its tests        |
| Shared interface or schema change               | Trace consumers and compatibility before changing the contract    |
| Large uncertain change                          | Use `plan` for dependencies and acceptance criteria               |
| Independent work with a useful integration path | Use authorized delegation and explicit ownership                  |

Keep implementation and its verification together. Do not defer all tests until the feature is complete when an earlier test can guide the design. Equally, do not create tests for a reversible text edit merely to satisfy ceremony.

Break work at coherent behavior or contract boundaries. File count and number of edits are not useful universal cadence rules. Run the cheapest check that can expose the next likely failure before building more work on a potentially false premise.

## Keep the Design Accountable

Follow local patterns unless a concrete problem justifies departing from them. Explain the reason, not a generic preference for a different style.

| Pressure                                 | Decision                                                                        |
| ---------------------------------------- | ------------------------------------------------------------------------------- |
| New modes or configuration appear        | Tie each to a requested behavior or demonstrated variation                      |
| The same decision repeats across callers | Give that decision one appropriate owner                                        |
| A wrapper only forwards calls            | Inspect whether it enforces an API, policy, or test boundary before removing it |
| A cast conceals incompatible data        | Fix or validate the contract at its actual boundary                             |
| A fallback hides an error                | Preserve the failure cause and handle the intended recovery explicitly          |
| Compatibility code grows                 | Check shipped consumers and rollout requirements before keeping or deleting it  |
| Complexity keeps increasing              | Re-examine ownership and data flow before adding another special case           |

An abstraction can be valuable before a second caller when it enforces a real boundary. A shorter implementation can be worse when it obscures error behavior or compatibility. Judge the concepts and contracts, not line count alone.

Keep edits within the requested scope. Remove imports, stale labels, and dead branches your own change creates. Route unrelated findings to the project's sidequest or issue workflow when required; do not absorb them silently into the implementation.

When a scale problem appears, identify the contended resource. Fix isolation, indexing, batching, ownership, or capacity at the cause. A temporary concurrency reduction may help a controlled diagnosis or an authorized incident mitigation; it must not quietly become the permanent solution.

## Verify the Claim You Intend to Make

Choose checks from the actual repository and affected behavior:

| Check                         | What it can establish                        | Common limit                                  |
| ----------------------------- | -------------------------------------------- | --------------------------------------------- |
| Type/static analysis          | Selected type and structural properties      | Does not execute runtime behavior             |
| Focused behavioral test       | The intended cases exercise the changed path | Mocks may bypass integration                  |
| Package or integration checks | Contracts between affected components hold   | May omit packaging or deployment differences  |
| Build/package validation      | The artifact can be produced                 | Does not prove it can be installed or used    |
| Consumer check                | The artifact serves its intended consumer    | Limited to the observed environment and cases |

Use scoped checks for the inner loop and run required repository gates before the relevant commit or delivery boundary. Broaden testing when shared dependencies, failures, or residual risk justify it. Once appropriate checks pass, continue to completion instead of repeatedly running unrelated suites.

Preserve command exit codes and raw failure logs. A pipeline into `tail` can hide a failed command unless pipeline status is handled. Summarize verbose logs after capturing them. Do not impose arbitrary timeouts or run autofix across other agents' work. Discover the actual test framework's selection semantics before relying on a filtered run.

A useful receipt names the command, revision or working-tree state, environment when relevant, exit status, and what actually ran. A filter selecting zero intended tests does not verify the change. Cached results can be legitimate when their inputs match; disclose them rather than describing them as fresh execution. Wall-clock duration alone neither proves work nor proves a defective gate.

### Check the Consumption Boundary

| Artifact                | Representative proof                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------ |
| Generated configuration | Inspect composed output for the motivating invariant                                       |
| Package                 | Install and invoke the built distribution without undeclared sibling dependencies          |
| UI                      | Exercise the changed interaction in the real surface, using `agent-browser` when available |
| CLI                     | Invoke the relevant command, including affected error/default paths                        |
| Database migration      | Apply against representative schema/data and check compatibility or rollback requirements  |
| Service                 | Confirm the running revision and exercise the changed request path                         |

Check the invariant, not merely "the command succeeded." A syntactically valid selector can match nothing. A package can build while omitting files the importer needs. A merged fix can leave the deployed artifact unchanged.

Production apply or other externally consequential checks still require the applicable authorization. Complete all available local evidence and report the remaining limit without implying the live check passed.

New detectors and guards need positive and negative evidence: induce the failure they should catch and verify normal behavior remains accepted. Performance changes need a baseline, representative workload, and relevant resource measurements. For a surface you cannot observe, give the human a discriminating procedure and expected result; do not invent a screenshot or hardware verdict.

## Recover by Updating the Hypothesis

Classify a failure before editing again. Environment faults, stale artifacts, invocation mistakes, shared-output races, and runtime defects require different responses. Preserve the original error and identify the first failing dependency instead of fixing every downstream symptom.

When a fix fails, state what the result disproves and choose a check that distinguishes the remaining explanations. Repeating variations without new evidence is the signal to reframe, regardless of attempt count. Avoid an adjacent refactor as a substitute for diagnosis.

A failure on the base can show that a symptom predates the change; missing changed filenames in a trace cannot. A successful rerun does not establish harmless flakiness. Compare the same command, inputs, revision, and environment before attributing a failure. Detailed CI and incident procedures live in `references/recovery.md`.

## Review and Commit Coherent Work

Follow the project's commit policy. Where atomic commits are expected, commit verified logical chunks rather than accumulating unrelated work. Keep a behavior change with the tests needed to understand it. Separate mechanical moves when doing so makes review clearer and preserves valid intermediate states.

Before staging, inspect status and the diff. Stage explicit owned paths or hunks, inspect the staged patch, and avoid including someone else's index changes. Follow current project message and attribution rules; use `git` for shared-index handling, worktrees, rebases, or conflict recovery. Push, merge, and release authority comes from the user and project contract, not this skill.

Compare the total diff to the task at a commit or integration checkpoint. Green tests can coexist with unnecessary scope. Review findings need a demonstrated mechanism and impact; triage blockers against optional improvements rather than treating every suggestion as a new requirement.

Obtain independent adversarial verification for non-trivial changes when the project requires it, and for consequential risk when justified. Use `cross-model-review` when available and applicable. A different model can expose blind spots but does not eliminate correlated errors. Verify central findings against evidence and tie the verdict to the reviewed state. Report incomplete review as incomplete.

## Preserve the State and Finish

At handoff or compaction, preserve the original outcome, user corrections, changed paths, revision, checks already run, unresolved findings, and next step. Reinspect current status on resumption before continuing; another agent may have changed the tree.

Capture durable causes and fixes in configured memory when they would prevent rediscovery. Report what changed, why, what proves it, and any material unverified boundary. Continue authorized necessary work until that outcome is handled.

## Evidence and References

Reviewed 2026-09-04. The [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) explicitly notes over-testing on small tasks and unnecessary blocking from conflicting instructions. The proportional checks and user precedence here address those risks.

Read `references/benchmarks.md` when evaluating workflow effectiveness or interpreting benchmark claims. Read `references/recovery.md` for CI triage, intermittent failures, and incident recovery. Neither reference establishes universal edit ratios or model-independent performance guarantees.

## Anti-Patterns

| Anti-pattern                                  | Better move                                                        |
| --------------------------------------------- | ------------------------------------------------------------------ |
| Verify after an arbitrary number of edits     | Verify before relying on a new uncertain contract                  |
| Run every suite for a small change            | Run required and relevant gates; expand for evidence-based reasons |
| Accept a green badge without coverage         | Inspect what ran and what assertion it supports                    |
| Call an issue pre-existing from an empty grep | Compare controlled executions and trace causality                  |
| Delete compatibility because it looks old     | Check consumers and rollout obligations                            |
| Request permission for each routine choice    | Carry existing authorization through execution                     |
| Treat reviewer approval as consumer proof     | Test the changed behavior where its output is used                 |

## What This Skill is NOT

- A fixed sequence, edit budget, mandatory research phase, or agent quota.
- Permission to change adjacent code, bypass approvals, or claim unrun checks.
- A replacement for understanding the actual implementation and its consumers.
