---
name: codex-review
description: Use this skill for code reviews using the Codex CLI from a Claude-hosted session. Activates on mentions of codex review, code review with codex, codex check, gpt review, codex exec review, run codex, review my code, review this PR, review changes, peer review, or second opinion.
---

# Cross-Model Code Review with Codex CLI

Cross-model validation using the `codex` binary directly. Claude writes code, Codex reviews it. Different architecture, different training distribution, no self-approval bias.

**Core insight:** Single-model self-review is systematically biased. Cross-model review catches different bug classes because the reviewer has fundamentally different blind spots than the author.

**Scope the independence claim honestly:** a different model breaks self-review bias — nothing else. It does not catch shared-training staleness (version, SOTA, and ecosystem claims need live primary sources no matter how many models agreed) or intent misreads inherited from the brief (carry the user's verbatim ask into the prompt and ask the reviewer to challenge the interpretation).

**How to read this skill:** the patterns and decision tables below are guidelines. Pick what fits, blend when needed. The rules marked ⚠️ are different: they're real `codex` CLI behaviors, not procedural ceremony. Skipping the scope flag genuinely hangs the call; piping to `tail` genuinely loses output. Treat ⚠️ rules as facts about the tool, not opinions about workflow.

**Prerequisite:** The `codex` CLI must be installed and authenticated. Verify with `codex --version`. User defaults live in `~/.codex/config.toml`; respect them.

**On Pi:** when the pi-nova xreview extension is installed, prefer `/xreview` — it wraps external `codex exec --sandbox read-only` with stdin closed and returns structured Verdict/Findings/Fix Queue. Manual bash calls from Pi follow the same ⚠️ rules below.

**Direction:** Claude → Codex only. For the bidirectional skill (also handles Codex → Claude with the `claude -p` gotchas around `yield_time_ms` and variadic flags), use `/hyperskills:cross-model-review` instead.

---

## ⚠️ Non-Negotiable Rule: Always pass a scope flag to `codex review`

A bare `codex review` (no scope) is the #1 cause of failures: it hangs or produces 100KB+ blob output. **Always specify exactly one scope flag:**

| Want to review          | Command                       |
| ----------------------- | ----------------------------- |
| Branch since main       | `codex review --base main`    |
| Single commit           | `codex review --commit <SHA>` |
| Working tree (unstaged) | `codex review --uncommitted`  |

Scoped `codex review` also accepts custom instructions as a trailing `[PROMPT]` argument (as of Jul 2026: `codex review --base main "focus on error handling"`), so a focused pass keeps structured review behavior. Reach for `codex exec "PROMPT"` when the artifact isn't a diff at all — spec docs, single files outside version control, freeform investigations — never bare `codex review`.

If `codex review` output exceeds ~100KB, the diff is too large for one pass. Split per commit, or use `codex exec` with a narrower prompt ("Review error handling only"). Large `codex exec` transcripts are a different animal — see When the Review Hangs.

**Pin the surface, freeze the target.** On a dirty or multi-workstream branch, give an explicit file list or pipe the exact diff into `codex exec` — an unpinned reviewer wanders into diff tourism. Don't edit the reviewed code while the review runs; fill the wait with work that's read-only relative to the reviewed diff. Any edit after the verdict voids it: re-review exactly the delta, so the blocker is closed rather than hand-waved.

---

## ⚠️ Capture Output to a File: Don't Pipe to `tail`

Never pipe a review to `| tail -N`. Three failure modes:

1. **The pipe buffers until EOF.** `tail` reads the whole stream before producing output, so the agent gets nothing until codex exits or times out, no progress signal mid-review.
2. **Reviews put the verdict near the top, not the bottom.** Findings sort by severity (BLOCKER first), so `tail -300` cuts exactly the part you want.
3. **A file lets a human watch progress live.** `tail -f /tmp/review.txt` in another terminal streams the review in real time, completely independent of the agent's call.

**Right pattern:** pick a non-colliding filename, redirect, then read it back.

```bash
# mktemp so parallel/repeat reviews don't clobber each other.
# Bake the scope into the slug so it's self-describing under tail -f.
out=$(mktemp -t codex-review-pre-pr.XXXXXX) && echo "$out"

codex review --base main > "$out" 2>&1
codex exec --sandbox read-only "PROMPT" > "$out" 2>&1
```

If `mktemp` isn't handy: `out=/tmp/codex-review-$$-$(date +%s).txt`. Echo the path before the redirect so a human running `tail -f` knows where to look. After exit, `Read` (or `cat`) the file. It persists across turns, re-read instead of re-running.

Adjacent tool fact: under `--sandbox read-only`, Codex silently can't write a report file the prompt asks for. Capture via redirect or `--output-last-message`, never "write your report to X".

---

## When the Review Hangs

Even correctly-scoped reviews hang — it's the top operational failure in the field. The output file is the liveness instrument: judge by growth and process state, never elapsed time. Slow with growing output is often a quality signal — a fast rubber stamp on a big surface is suspicious.

| Signal                         | Move                                                                                                                                                        |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Output file growing            | Keep waiting; it's working                                                                                                                                  |
| Empty file, process tree alive | Wait one more window, then isolate variables (as of Jul 2026, wedged MCP servers and startup hooks are the usual culprits)                                  |
| Empty file, process wedged     | Kill only that process tree; retry once with fewer degrees of freedom — exact diff on stdin, narrower file list, lower effort. Same question, less payload |
| Retry also sticks              | Pre-declare the give-up, record the failed review honestly                                                                                                  |

Never spawn a duplicate alongside a live reviewer — reap the one you have. And size alone is not the failure signal: a 1MB+ `codex exec` transcript can be a successful deep exploration with the verdict at the tail — grep for verdict and severity markers instead of dumping the trace. The real failure shape is no output growth, or growth with no convergence toward a verdict.

---

## Two Ways to Invoke Codex

| Mode           | Command                                                     | Best For                                                    |
| -------------- | ----------------------------------------------------------- | ----------------------------------------------------------- |
| `codex review` | Structured diff review with prioritized findings            | Pre-PR reviews, commit reviews, WIP checks                  |
| `codex exec`   | Freeform non-interactive deep-dive with full prompt control | Security audits, architecture, focused investigation, specs |

### Scope flags (`codex review` only)

| Flag              | Purpose                     |
| ----------------- | --------------------------- |
| `--base <BRANCH>` | Diff against base branch    |
| `--commit <SHA>`  | Review a specific commit    |
| `--uncommitted`   | Review working tree changes |

### Sandbox & ergonomics flags (both modes)

| Flag                                         | When                                                           |
| -------------------------------------------- | -------------------------------------------------------------- |
| `--sandbox read-only`                        | Default for review work, no writes                             |
| `--sandbox workspace-write`                  | Review + apply suggested fixes                                 |
| `--full-auto`                                | Alias for `--ask-for-approval never --sandbox workspace-write` |
| `--dangerously-bypass-approvals-and-sandbox` | Last resort; explicit user request only                        |
| `-C <DIR>` / `--cd <DIR>`                    | Run in another worktree without `cd`                           |
| `--skip-git-repo-check`                      | Running from `/tmp` or any non-repo dir (trips the git trust check) |
| `--add-dir <DIR>`                            | Extend read access to another path                             |
| `--ephemeral`                                | One-shot session, no persistence                               |
| `--json` / `--output-last-message <FILE>`    | Capture structured output to a file                            |
| `-c model_reasoning_effort="xhigh"`          | Spec/RFC review only (see Effort Policy)                       |

### Effort override policy

| Reviewing                       | Effort flag                               |
| ------------------------------- | ----------------------------------------- |
| Code (commit / diff / PR / WIP) | **None**, defer to `~/.codex/config.toml` |
| Spec / RFC / design doc         | `-c model_reasoning_effort="xhigh"`       |

Specs are higher-stakes than diffs, a subtle architectural mistake compounds across the eventual implementation. Code diffs are smaller scope and the user's configured effort is fine.

**Scope before effort.** Effort amplifies whatever the scope is; the xhigh override applies to an already-scoped spec review. An unscoped "verify everything" prompt at xhigh diverges instead of deepening (observed: 80k lines of transcript, no verdict). When a review must converge, narrow the scope — and consider lower effort, not higher — with an explicit convergence budget in the prompt ("be surgical, converge to a verdict").

**Never** specify `--model`, `-m`, or `-c model=` to override the model itself. User config is authoritative. The gate's value is the full agentic Codex with repo access — not a one-shot API call.

---

## Review Patterns

### Pattern 1: Pre-PR Full Review (default)

The standard review before opening a PR. Use for any non-trivial change.

```
Step 1, structured review (catches correctness + general issues):
  codex review --base main

Step 2, security deep-dive (if code touches auth, input handling, or APIs):
  codex exec "<security prompt from references/prompts.md>"

Step 3, fix findings, then re-review carrying the ledger (see Pattern 5):
  codex review --base main
```

The same shape works per-commit (`codex review --commit <SHA>`) and mid-development on the working tree (`codex review --uncommitted`).

### Pattern 2: Focused Investigation

Surgical deep-dive on a specific concern (error handling, concurrency, data flow).

```bash
codex exec --sandbox read-only \
  "You are a senior <DOMAIN> engineer. Analyze <CONCERN> in the changes
   between main and HEAD. For each issue: cite file and line, explain the
   risk, suggest a concrete fix. Confidence threshold: 0.7."
```

### Pattern 3: Spec / RFC Review

Reviewing prose (markdown design docs) before code is written.

```bash
codex exec -c model_reasoning_effort="xhigh" --sandbox read-only \
  "You are a senior staff engineer doing a candid pre-implementation review of
   <PATH>. The author wants sharp, unsentimental analysis. For each finding:
   severity (BLOCKER / HIGH / MEDIUM / LOW), confidence (>= 0.7 only), location
   (file path + section heading), the issue, a concrete fix.
   End with a one-paragraph go/no-go verdict."
```

### Pattern 4: Single-File / Focused-Path Review

Review one file or directory rather than a full diff.

```bash
codex exec --sandbox read-only \
  "Review only <PATH> for <CONCERN>. Skip style and ergonomics.
   Return PASS if no real issues; otherwise concise FAIL findings with
   file:line evidence."
```

### Pattern 5: Ralph Loop (Implement → Review → Fix)

Iterative quality enforcement. Round 1 is broad and hostile. Every later round carries the ledger: enumerate the prior round's findings verbatim plus the fixes claimed, and ask the reviewer to (a) verify each fix with receipts, (b) hunt bugs the fixes introduced, (c) not re-litigate settled trade-offs. Scope decays per round: broad → blockers-only → convergence check with a one-line contract ("PASS / NEEDS_CHANGES: \<one sentence>"). For specs, log rounds in a Review History section of the artifact — the loop's state lives in the artifact, not chat exhaust. Re-review templates are in `references/prompts.md`.

**The budget is convergence, not a count.** Keep iterating while each round yields a new confirmed finding or verifies a fix; stop when rounds oscillate or re-litigate. Three rounds is the default expectation, not a wall — a fifth round that catches real bugs is fine, while a third round re-arguing round one is already over budget. This budget governs the loop you drive; inbound bot or human feedback streams get fresh re-triage every round and are never capped.

**The fix loop is a scope ratchet.** Before touching code after a round: triage blockers vs follow-ups, pre-declare a file budget ("three files unless tests force otherwise"), and treat document-why-not as a legitimate response to absence findings. Blockers require changed-line causality; suggestions may cover nearby risk; pre-existing debt becomes follow-up tasks, not in-loop fixes. Unbounded review-response is how a loop ends up editing 120 files.

---

## Multi-Pass Strategy

Thorough reviews benefit from multiple focused passes rather than one vague pass. Single passes dilute attention across dimensions and produce shallow findings on each. Each pass gets a specific persona and concern domain.

| Pass             | Focus                                       | Mode                                  |
| ---------------- | ------------------------------------------- | ------------------------------------- |
| **Correctness**  | Bugs, logic, edge cases, race conditions    | `codex review`                        |
| **Security**     | OWASP Top 10:2025, injection, auth, secrets | `codex exec` with security prompt     |
| **Architecture** | Coupling, abstractions, API consistency     | `codex exec` with architecture prompt |
| **Performance**  | O(n²), N+1 queries, memory leaks            | `codex exec` with performance prompt  |

Run passes sequentially — fixing critical findings between passes — when the diff is changing under review. On a frozen artifact, parallel lens-locked passes (one concern each, explicit non-goals) produce additive non-overlapping findings and finish faster.

Line counts are rough guides; scale passes to risk and surface, not arithmetic:

| Change size                                 | Strategy                       |
| ------------------------------------------- | ------------------------------ |
| < 50 lines, single concern                  | Single `codex review`          |
| 50-300 lines, feature work                  | `codex review` + security pass |
| 300+ lines or architecture change           | Full 4-pass                    |
| Security-sensitive (auth, payments, crypto) | Always include security pass   |

---

## Consuming the Findings

Reviewer output is input, not orders. Re-verify each finding against ground truth — code, git history, live data — before any edit. Three dispositions, always reported: fix now / intentional-keep with named rationale / can't-verify, flagged to the human. "Verified, no code change" is a legitimate outcome; one session disproved 3 of 4 findings and changed nothing. Argue wrong findings down with receipts, never silently drop them. Two independently-briefed reviewers converging on the same bug upgrades it to confirmed.

Codex's characteristic misses to check first:

| Failure mode        | Check                                                    |
| ------------------- | -------------------------------------------------------- |
| Temporal scope      | Did it review the commit state the finding claims?       |
| Near-name confusion | Is the cited artifact the one actually changed?          |
| Invented flags/APIs | Does the suggested flag or function exist? Run `--help`  |
| Stale-at-fix-time   | Was the complaint valid at review time but now resolved? |

Close the loop both directions: when a defect class is fixed, fold it into the repo's standing review prompt or CI gate so the next reviewer inherits it. When a reviewer keeps hallucinating the same ghost, fix what reviewers ingest — scrub the stale doc it keeps importing. And seed the next review with prior gotchas from memory; they make a sharp hypothesis list.

---

## Prompt Engineering Heuristics

The non-obvious levers that reliably improve review signal quality:

1. **Specify what to skip.** "Skip formatting, naming style, minor docs gaps" prevents bikeshedding
2. **Require confidence scores** and act only on findings ≥ 0.7
3. **One domain per pass.** Security-only, architecture-only
4. **Demand a verdict.** "Verdict: patch is correct / incorrect" or "go / no-go"

The full brief anatomy (verbatim ask, keystone claim, assumed-passed receipts, anti-sycophancy, no-memory line) and ready-to-use templates are in `references/prompts.md`.

---

## Anti-Patterns

| Anti-Pattern                                   | Why It Fails                                                 | Fix                                                                      |
| ---------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------ |
| Bare `codex review` (no scope flag)            | Hangs or produces blob output                                | Exactly one scope flag — see the ⚠️ scope rule                           |
| Piping review output to `tail -N`              | Buffers until EOF; cuts the verdict                          | Redirect to a file — see the ⚠️ capture rule                             |
| `timeout 30 codex review`                      | Reviews legitimately take 30s–5min                           | No timeout, or `timeout 300` minimum                                     |
| Treating transcript size as the failure signal | A 1MB+ `codex exec` transcript can be a successful deep dive | Judge by growth and convergence to a verdict (When the Review Hangs)     |
| "Review this code" (no specifics)              | Vague, produces bikeshedding                                 | Specific domain prompts with persona                                     |
| Single pass for everything                     | Context dilution, shallow on every dimension                 | Multi-pass with one concern per pass                                     |
| Self-review (Claude reviews Claude's code)     | Systematic bias, models approve their own patterns           | Cross-model: Claude writes, Codex reviews                                |
| No confidence threshold                        | Noise floods signal, 0.3 confidence wastes time              | Only act on ≥ 0.7 confidence                                             |
| Style comments in review                       | LLMs default to bikeshedding                                 | "Skip: formatting, naming, minor docs"                                   |
| Re-litigating settled findings across rounds   | Over budget regardless of round count                        | Budget is convergence — stop when rounds oscillate, not at a number      |
| Review without project context                 | Generic advice disconnected from codebase                    | Run from repo root                                                       |
| Recurring reviewer hallucination               | The ghost usually lives in a doc reviewers ingest            | Scrub the stale doc; don't re-argue it every round                       |
| MCP wrapper around `codex`                     | Unnecessary indirection over a CLI binary                    | Call `codex` directly via Bash                                           |
| Hardcoding `--model` / `-m` / `-c model=`      | Overrides user config; stale model names                     | Defer to `~/.codex/config.toml`                                          |
| Effort override on routine code review         | Wastes tokens, ignores user defaults                         | `-c model_reasoning_effort="xhigh"` is for spec review only              |
| `--full-auto` for pure review                  | Grants write access the review doesn't need                  | `--sandbox read-only` for review; `--full-auto` only when applying fixes |

---

## When Codex Can't Run

The gate is non-fungible. When it can't run (quota, CLI wedge, MCP failure), fall down the ladder with the weaker guarantee named: fresh-context same-model review is the floor, different-family is the premium. Disclose the substitution in the wrap and the PR body, and let the human decide whether to proceed. A blocked review channel never produces a PASS.

---

## What This Skill is NOT

- **Not a replacement for human review.** Cross-model review catches bugs but can't evaluate product direction or UX.
- **Not a linter.** Don't use Codex review for formatting or style.
- **Not a staleness check.** Version and SOTA claims need live primary sources regardless of how many models agreed.
- **Not infallible.** 5–15% false positive rate is normal. Triage findings (see Consuming the Findings).
- **Not for self-approval.** The whole point is cross-model validation. Don't use Claude to review Claude's code.

## References

For ready-to-use prompt templates, see `references/prompts.md`.
