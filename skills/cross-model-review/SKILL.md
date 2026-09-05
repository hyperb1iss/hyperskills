---
name: cross-model-review
description: Use this skill when requesting or consuming an independent review from another model, including code, specifications, diagnoses, and factual claims. Activates on mentions of cross-model review, second opinion, independent review, different model review, confer with Codex, fact-check this doc, or check my conclusion. Use hyper-pr-review when conducting the review yourself.
---

# Cross-Model Review

Use a fresh reviewer to challenge an artifact against the original request. A different model family can add useful diversity, but agreement is not proof. Preserve the user's configured model and effort unless the user explicitly requests a change. Skill guidance does not override the task's scope, existing authorization, or host permissions.

## Choose the Review Surface

| Situation                                     | Route                                                                                    |
| --------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Claude author, Codex available                | Scoped `codex review`, or `codex exec` for custom questions                              |
| Codex author, Claude available                | `claude -p` with a bounded brief and restricted tool access                              |
| Pi with the xreview extension                 | Use its installed `/xreview` interface after checking its scope semantics                |
| Native reviewer with a different model family | Use the exposed delegation tool when authorized; inspect its actual schema               |
| Different family unavailable                  | Fresh-context review can still help; disclose that it provides context independence only |

Run the chosen CLI's `--version` and relevant `--help` before relying on flags. Tool names, wait limits, permissions, and model availability belong to the current host. An external CLI is still delegation; it does not bypass a host prohibition.

For CLI details and a copyable launcher, read `references/cli-flags.md`. Use `references/prompts.md` for the requested review mode. Load `references/failure-recovery.md` only when a launch fails or stalls.

## Freeze a Reviewable Artifact

Capture the original request, repository path, review base, head SHA, and owned file list. For working-tree review, include staged, unstaged, and relevant untracked files. A SHA alone does not describe uncommitted work; retain the diff and file contents or a content digest. Keep unrelated work outside the packet.

| Scope                 | Evidence to capture                                                                   |
| --------------------- | ------------------------------------------------------------------------------------- |
| Branch                | Exact base/head plus `git diff <base>...<head>`                                       |
| Single commit         | Parent and commit, with `git show <sha>`                                              |
| Working tree          | `git status --short`, staged and unstaged diffs, contents of relevant untracked files |
| Document or diagnosis | Exact artifact version, claim list, and supporting source material                    |
| Fix verification      | Prior finding verbatim, claimed fix, new artifact, and regression cases               |

Freeze the reviewed files while the reviewer reads. Continue independent work elsewhere. If the artifact changes, identify the delta and re-review affected behavior. A metadata-only commit does not erase execution evidence for an identical tree, but an old review must never be described as examining a new SHA without a content comparison.

## Write a Brief That Can Disagree

Give the reviewer the user's actual request and the artifact before your interpretation. Include necessary constraints and relevant repository instructions. Label your proposed explanation as a hypothesis. For a first independent pass, avoid supplying the conclusion you want confirmed.

A useful brief names:

- The question and exact review scope.
- The important behavior, interfaces, or failure modes to check.
- Available evidence and the environment needed to reproduce it.
- Permitted actions and required output.

Existing test results are receipts, not an instruction to trust the author. Let the reviewer repeat a decisive check or choose an independent probe. Avoid numerical confidence cutoffs, mandatory finding counts, and prompts that assume a defect exists. Read-only review does not mean tests are harmless: untrusted code needs an isolated environment without credentials.

For code, request each finding's trigger, impact, location, and evidence. For a specification, request an unmet requirement or a concrete counterexample. For a fact-check, request a verdict per claim with a primary source. For a design consult, request a recommendation and the evidence that would change it; a consultation needs no PASS.

## Launch Once, Retain the Handle

For long Claude CLI reviews, use `scripts/run_claude_review.py` and inspect its saved status with `scripts/review_status.py`. Read `references/observable-reviews.md` for launch, authentication, scope, and recovery details. The helper retains events and stderr without requiring another reviewer process. Native host progress tools or a direct CLI capture remain suitable when they provide enough visibility.

Capture the full output to a unique file, and print that path before launch. Keep prompt content in a file or single-quoted heredoc. Do not interpolate untrusted text into shell code. A quoted `"$(cat "$review_prompt")"` reads a trusted prompt file as one argument; an unquoted heredoc can execute embedded shell syntax.

A running process or cell ID means the job is active. Poll that same handle with the host's supported wait operation. Wait duration controls when the host yields, not whether the reviewer succeeds. Use legal wait values and leave room for user updates; do not hardcode a five-minute initial wait into every harness.

Do not pipe a live review through `head` or `tail` as the sole capture. `head` can close the pipe early; `tail` commonly withholds output until EOF and discards earlier findings. Read the saved result after completion. Silence, transcript size, and elapsed time do not establish a verdict.

Authentication must follow the user's intended provider and billing route. For a subscription-backed Claude review, remove an inherited `ANTHROPIC_API_KEY` from that child process when it would select unintended API billing. Preserve it for an explicitly API-backed workflow. Never print credentials or change persistent auth configuration to make a review run.

## Adjudicate Findings

A finding is a claim until its cited path and trigger survive a disproof attempt. Inspect the exact artifact reviewed before changing code. A reviewer can identify the wrong similarly named file, invent a CLI flag, or flag behavior already fixed at HEAD.

| Disposition | Required evidence                                                                    |
| ----------- | ------------------------------------------------------------------------------------ |
| Fix         | A real defect within the authorized scope, with a reproducible or fully traced cause |
| Decline     | The counterexample, contract, or intentional tradeoff that refutes the finding       |
| Follow-up   | A verified issue outside the change's causal scope                                   |
| Unresolved  | The missing environment, fact, or decision and the check that would settle it        |

Two reviewers agreeing increases investigation priority; it does not promote a candidate to confirmed. A missing grep match does not establish absence. Compare base and head when claiming the change introduced a defect. Static tracing can confirm a deterministic error if the complete path is established; report the actual evidence tier without pretending execution occurred.

Fix verified issues and inspect the fix for new regressions. Preserve reviewer independence: switch explicitly from review to implementation when the user authorized both. Do not let a read-only reviewer silently edit the artifact it is judging.

## Converge on Evidence

Keep a compact findings ledger when several rounds are needed. Each entry has an identity, evidence, disposition, and verification status. Subsequent briefs carry the prior finding verbatim and the changed artifact so the reviewer checks closure rather than rediscovering the conversation.

Continue while rounds produce new confirmed defects or verify fixes. If the same objection returns without new evidence, settle the underlying contract or report the remaining disagreement. Avoid open-ended loops driven by a nonzero suggestion count. Nonblocking preferences do not expand an authorized fix into a redesign.

| Verdict       | Meaning                                                                                                   |
| ------------- | --------------------------------------------------------------------------------------------------------- |
| PASS          | The requested review finished, required checks ran, and no blocking finding remains in the reviewed scope |
| NEEDS_CHANGES | At least one supported blocking defect remains                                                            |
| INCONCLUSIVE  | Required coverage or evidence is unavailable; include useful partial findings                             |

An interrupted review cannot grant PASS over unread material. Process exit zero means the CLI completed; the substantive report determines the review verdict. Distinguish model review, static analysis, and executed checks in the receipt. None replaces the others.

## Evidence and Maintenance

As checked on 2026-09-04, [Claude's CLI reference](https://code.claude.com/docs/en/cli-reference) distinguishes available tools from preapproved tools. [OpenAI's non-interactive documentation](https://developers.openai.com/codex/noninteractive) documents captured execution outputs. Verify both against the installed versions before dispatch.

The recommendation to examine outcomes and traces separately follows [Anthropic's agent evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). Cross-family diversity is a useful review strategy, not a measured guarantee for this library. No universal false-positive rate or accuracy improvement is claimed here.

## Anti-Patterns

| Anti-pattern                                           | Correction                                                                  |
| ------------------------------------------------------ | --------------------------------------------------------------------------- |
| Treating `--allowedTools` as a sandbox                 | Restrict available tools and apply the host's actual isolation boundary     |
| Relaunching after a yield                              | Poll the existing handle; recover output before considering a retry         |
| Requiring a specific model or maximum effort           | Preserve user configuration; improve scope before changing resources        |
| Promoting consensus to confirmation                    | Run the disproof or trace the complete behavior                             |
| Passing a review with missing required checks          | Report INCONCLUSIVE with the remaining evidence gap                         |
| Treating every suggestion as mandatory                 | Fix supported defects within scope; record optional improvements separately |
| Replacing the user's request with the author's summary | Include the original request and invite interpretation challenges           |

## What This Skill is NOT

- Not permission to send source to an unapproved provider, publish a review, or modify someone else's branch.
- Not protection against shared stale knowledge or a misleading brief.
- Not a substitute for runtime verification, product judgment, or understanding the finding.
