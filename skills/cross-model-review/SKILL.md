---
name: cross-model-review
description: Use this skill for cross-model code reviews where a different AI model reviews code written by the current model, and for cross-model fact-checks, diagnosis checks, and design consults. Activates on mentions of cross-model review, peer review, second opinion, review my code, review this PR, review changes, independent review, unbiased review, different model review, cross-check code, code review, confer with codex, fact-check this doc, or check my conclusion.
---

# Cross-Model Code Review

Cross-model validation: the authoring model writes code, a different model reviews it.

**Core insight:** Single-model self-review is systematically biased. The same blind spots that let bugs through during writing let them through during review. A different model breaks self-review bias — that bias specifically, not every bias. Reviewer and author share training-data staleness, and the reviewer inherits whatever the brief mis-states; see What This Skill is NOT for what the gate does not catch.

**How to read this skill:** patterns and decision trees below are guidelines. Pick what fits, blend when needed. The rules marked ⚠️ are different: they're real CLI behaviors (`yield_time_ms`, the `--` separator, scope flags), not procedural ceremony. A Jun 2026 audit across 4k+ Claude/Codex JSONL conversations found `claude -p` failures clustering around these mechanics, plus zsh wrapper mistakes. Treat them as facts about the tool, not opinions about workflow.

## Direction & Pre-Flight

Identify the host first. The host runs the _other_ model's CLI as a subprocess.

| Current host      | You invoke                      | Direction                     |
| ----------------- | ------------------------------- | ----------------------------- |
| Claude Code       | `codex` CLI                     | Claude writes → Codex reviews |
| Codex             | `claude` CLI                    | Codex writes → Claude reviews |
| Pi (pi-nova pack) | `/xreview` (wraps `codex exec`) | Pi writes → Codex reviews     |

Confirm the reviewer is reachable before the real call:

| Host   | Verify command                                                                                                                       | Notes                             |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------- |
| Claude | `codex --version`                                                                                                                    | One-shot, no special flags        |
| Codex  | `printf 'say ok\n' \| env -u ANTHROPIC_API_KEY claude -p --output-format text --no-session-persistence` with `yield_time_ms: 300000` | Sanity ping only, see Rules 1 & 4 |
| Pi     | `codex --version`                                                                                                                    | Same binary as Claude host        |

**On Pi:** prefer `/xreview` when the xreview extension is installed — it shells out to `codex exec --sandbox read-only` with stdin closed and injects Verdict, Findings, and Fix Queue back into the session. Scope explicitly: `/xreview` reviews the working tree, `/xreview main` reviews since a base ref; put any focused concern in the prompt before running it. Manual bash fallback follows the Claude-host rules below. Treat PASS as evidence only for the reviewed scope.

**On Codex hosts,** the no-subagents-unless-asked delegation gate does not block this path: contract-mandated verification runs through the external reviewer CLI this skill dispatches.

**User defaults are authoritative.** Both CLIs read configured defaults (`~/.codex/config.toml`, `~/.claude/settings.json`). Never specify `--model`, `-m`, or `-c model=`. The only sanctioned override is reasoning effort, and only for spec review (see Effort Override Policy below).

---

## ⚠️ Codex → Claude: Four Non-Negotiable Rules

Rules 1–3 cause the overwhelming majority of cross-model review failures. They're not workflow preferences; they're how the `claude -p` shell tool behaves under Codex. Rule 4 doesn't break the review; it silently bills it to the wrong account. Get all four right on the first call.

### Rule 1: `yield_time_ms: 300000` on EVERY call

Codex's shell tool yields output back to the model after `yield_time_ms` elapses (default `1000` = 1 second). A real `claude -p` review takes 30 seconds to 5+ minutes. The default yields empty output + `Process running with session ID NNNN` before Claude has even started, and the model misreads this as failure.

**The rule:** every `claude -p` call uses `yield_time_ms: 300000` (5 minutes). Initial call, every reaping call, every sanity ping beyond a one-line `say ok`. No exceptions.

```json
{ "cmd": "claude -p --allowedTools \"Read,Glob,Grep,Bash(git *)\" -- \"PROMPT\"", "yield_time_ms": 300000 }
```

**Common cognitive trap:** "My prompt is short, I only need 30s." Wrong. Claude session setup, network, and model compute dominate; prompt length barely factors in. Always 300000.

**Consistency rule:** once you're at 300000, stay at 300000. Reverting to 1000 between calls in the same session creates a fresh wave of orphans on top of any still running.

### Rule 2: `Process running with session ID NNNN` is NOT an error: REAP, never retry

When Codex returns `Process running with session ID NNNN`, the process is alive and computing in the background. The yield fired before completion. **This is normal output, not failure.**

**Wrong** (each retry spawns a fresh process; original keeps running):

```json
{"cmd": "claude -p --allowedTools '...' -- 'PROMPT'", "yield_time_ms": 300000}
→ "Process running with session ID 84814"
{"cmd": "claude -p --allowedTools '...' -- 'PROMPT'", "yield_time_ms": 300000}
→ "Process running with session ID 84815"   // 84814 still alive, orphaned
{"cmd": "claude -p --allowedTools '...' -- 'PROMPT'", "yield_time_ms": 300000}
→ "Process running with session ID 84816"   // 84814 + 84815 both still alive
... 8 more retries ... 11+ orphans, ~7 minutes wall time
```

**Right** (reap the existing session by ID until exit):

```json
{"cmd": "claude -p --allowedTools '...' -- 'PROMPT'", "yield_time_ms": 300000}
→ "Process running with session ID 84814"
{"session_id": 84814, "yield_time_ms": 300000}        // reap, do NOT re-invoke claude -p
→ "Process running with session ID 84814"             // still computing
{"session_id": 84814, "yield_time_ms": 300000}        // keep reaping
→ "Process exited with code 0"                        // done, parse the output
```

**Reaping rules:**

- Do NOT re-invoke `claude -p` (creates a new process)
- Do NOT change flags, prompts, or tools (reaping is a different operation entirely)
- DO call `{"session_id": NNNN, "yield_time_ms": 300000}` repeatedly
- Stop only when `Process exited with code X` appears

### Rule 3: Variadic flags require the `--` separator

The `claude` CLI has flags that take `<value...>` and greedily consume every following argument until the next flag. If your prompt follows one of these without a `--` separator, the prompt gets swallowed as a flag value and Claude errors with `Input must be provided either through stdin or as a prompt argument when using --print` or hangs waiting on stdin.

**Variadic flags:** `--allowedTools` / `--allowed-tools`, `--disallowedTools` / `--disallowed-tools`, `--tools`, `--add-dir`, `--betas`, `--file`, `--mcp-config`, `--plugin-dir`.

**Required form** (default to this, works regardless of flag order):

```bash
claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT"
```

**Two fallbacks** if `--` won't work in your context: put the prompt before the flags (`claude -p "PROMPT" --allowedTools "..."`), or pipe it via stdin (`echo "PROMPT" | claude -p --allowedTools "..."`).

The `codex` CLI does not have this issue, its flags are non-variadic.

### Rule 4: Strip `ANTHROPIC_API_KEY` so the review bills to your subscription

Codex — and most shells that touch the Anthropic API — export `ANTHROPIC_API_KEY` into the environment. Child `claude -p` calls inherit it, and Claude Code's auth precedence ranks the API key **above** your Pro/Max subscription OAuth. Interactive `claude` prompts once before using a stray key and remembers your choice; `-p` (non-interactive) mode uses the key **silently, on every call**. The review still works — it just bills per-token against the API instead of drawing from your plan.

**The rule:** prefix every spawning `claude -p` call with `env -u ANTHROPIC_API_KEY`. That strips the variable for just that call, so Claude falls through to the subscription credentials stored by `/login`.

```json
{
  "cmd": "env -u ANTHROPIC_API_KEY claude -p --allowedTools \"Read,Glob,Grep,Bash(git *)\" -- \"PROMPT\"",
  "yield_time_ms": 300000
}
```

The prefix goes on the **spawning** call only — reaping calls (Rule 2) are bare `session_id` polls with no command, so there is nothing to strip.

**Precedence trap:** `CLAUDE_CODE_OAUTH_TOKEN` ranks _below_ `ANTHROPIC_API_KEY`, so exporting an OAuth token does **not** rescue you while the key is present — stripping is mandatory either way. The fallback only lands on the plan if a prior interactive `/login` (Pro/Max) wrote `~/.claude/.credentials.json`; without those creds, `claude -p` has nothing to fall through to.

### Codex → Claude Gold Path

Use this launch shape unless the review scope forces a different one. It bakes in the four rules, captures output to a file, and avoids the zsh `status` variable trap found in failed sessions.

```bash
prompt=$(mktemp -t claude-review-prompt.XXXXXX.md)
out=$(mktemp -t claude-review-output.XXXXXX.txt)
cat > "$prompt" <<'PROMPT'
You are an independent senior code reviewer.

Review the current branch for correctness, security, and maintainability.
Cite file:line for each finding, include confidence, and skip style nits.
Verdict: PASS or FAIL.
PROMPT
printf 'prompt_file=%s\nreview_output=%s\n' "$prompt" "$out"
if env -u ANTHROPIC_API_KEY claude -p --output-format text \
  --allowedTools "Read,Glob,Grep,Bash(git *),Bash(rg *)" \
  -- "$(cat "$prompt")" > "$out" 2>&1; then
  rc=0
else
  rc=$?
fi
printf 'claude_exit=%s\nreview_output=%s\n' "$rc" "$out"
exit "$rc"
```

Run that shell command through Codex with `yield_time_ms: 300000` and a normal output budget such as `max_output_tokens: 20000`.

**Why this shape survives real failures:** the temp files preserve the prompt and full output across turns; `env -u ANTHROPIC_API_KEY` guards billing (Rule 4); `--` guards the prompt (Rule 3); `rc` dodges zsh's read-only `status` variable; `> "$out" 2>&1` keeps megabyte reviews out of the agent context; the 300000 yield lets the call complete or hand back a reapable session (Rule 1).

If this yields `Process running`, reap per Rule 2; the output already printed `review_output=...`, so read that file after exit.

---

## ⚠️ Claude → Codex: One Non-Negotiable Rule

### Always pass a scope flag to `codex review`

A bare `codex review` (no scope) is the #1 cause of Claude → Codex failures: it hangs or produces 100KB+ blob output. **Always specify exactly one scope flag:**

| Want to review          | Command                       |
| ----------------------- | ----------------------------- |
| Branch since main       | `codex review --base main`    |
| Single commit           | `codex review --commit <SHA>` |
| Working tree (unstaged) | `codex review --uncommitted`  |

For anything outside this trio (spec docs, single files, custom scopes, personas), use `codex exec "PROMPT"` with explicit scope in the prompt, never bare `codex review`.

If `codex review` output exceeds ~100KB, the diff is too large for one pass. Split: `codex review --commit <SHA1>`, `codex review --commit <SHA2>`, or use `codex exec` with a narrowed prompt ("Review error handling only").

---

## ⚠️ Both Directions: Capture Output to a File

**Never** pipe a review to `| tail -N` or `| head -N`. Three reasons it fails:

1. **The pipe buffers until EOF.** `tail` (and `head`) read the entire upstream stream before producing output. The agent gets _nothing_ until the review process exits or times out, no progress signal, no early verdict, no way to tell if the call is alive.
2. **Reviews don't put the verdict at the end.** Findings are typically ordered by severity (BLOCKER first), with the summary/verdict near the top. `tail -300` discards exactly the part you need.
3. **A file lets a human watch progress live.** `tail -f /tmp/review.txt` in another terminal shows the review streaming in real time, completely independent of the agent's call.

**Right pattern:** pick a non-colliding filename, redirect to it, then read it back.

```bash
# mktemp: parallel reviews don't clobber; scope in the slug makes tail -f self-describing.
out=$(mktemp -t codex-review-pre-pr.XXXXXX) && echo "$out"

# Claude → Codex
codex review --base main > "$out" 2>&1
codex exec --sandbox read-only "PROMPT" > "$out" 2>&1

# Codex → Claude (yield_time_ms: 300000 + env -u ANTHROPIC_API_KEY still required — Rules 1 & 4)
env -u ANTHROPIC_API_KEY claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT" > "$out" 2>&1
git diff main...HEAD | env -u ANTHROPIC_API_KEY claude -p "PROMPT" > "$out" 2>&1
```

Echo the path before the redirect so the agent (and a human running `tail -f`) knows where to look. After exit, read the file — it persists across turns; re-read instead of re-running.

---

## Failure Recovery

When a review errors or hangs, classify before changing tactics — most failures are wrapper mechanics, not model quality. The full symptom → recovery table and the hang ladder are in `references/failure-recovery.md`. Headline rules:

- `Process running with session ID NNNN` is not an error — reap it (Rule 2).
- Silence is not failure: output-file growth plus process state is the discriminator, never elapsed time. Slow can be a quality signal — a fast rubber stamp on a large surface would be suspicious.
- No shell `timeout` around a review by default — short timeouts produced false exit-124 failures on reviews that legitimately run minutes.
- Kill only a confirmed-stuck process tree, never respawn blind, and disclose a failed review in the wrap.

---

## Degradation Ladder

When the preferred reviewer is unreachable, each rung down trades away a named guarantee. Label the rung in the verdict, disclose it in the wrap and PR body, and let the human decide whether a degraded gate suffices — a degraded PASS is never presented as the full gate.

| Rung                                          | Guarantee retained                                          |
| --------------------------------------------- | ----------------------------------------------------------- |
| Different-family reviewer, full agentic setup | Model diversity + repo context (the premium)                |
| Different-family, diff-only                   | Model diversity, no surrounding context                     |
| Same-model, fresh context                     | Context independence only — the floor; still catches real bugs |
| Alternate CLI, smoke-tested first             | A gate exists at all                                        |
| Honest failure recorded                       | Nothing — but the record is true                            |

Watch for silent same-family collapse: on a Codex host, "cross-model review" can quietly become GPT reviewing GPT. Verify the reviewer's family.

---

## Review Modes Matrix

Match the row to what you're actually reviewing.

The Codex → Claude cells below show scope shape only — for actual execution, wrap the chosen scope in the gold-path launcher above so all four rules stay intact.

| Mode                        | Scope                                                | Claude → Codex                                                                 | Codex → Claude                                                          |
| --------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| **Pre-PR full**             | `main...HEAD` (all commits on branch)                | `codex review --base main`                                                     | `git diff main...HEAD \| claude -p "PROMPT"`                            |
| **Single commit**           | One SHA                                              | `codex review --commit <SHA>`                                                  | `git show <SHA> \| claude -p "PROMPT"`                                  |
| **Commit range**            | `<base>..HEAD` (multi-commit slice, not all of main) | `codex review --base <base>`                                                   | `git diff <base>..HEAD \| claude -p "PROMPT"`                           |
| **Branch-vs-branch**        | feat-a vs feat-b (stacked PRs)                       | `codex review --base feat-a`                                                   | `git diff feat-a...HEAD \| claude -p "PROMPT"`                          |
| **Staged only**             | About-to-commit                                      | `git diff --staged \| codex exec "PROMPT"`                                     | `git diff --staged \| claude -p "PROMPT"`                               |
| **Unstaged WIP**            | Working tree                                         | `codex review --uncommitted`                                                   | `git diff \| claude -p "PROMPT"`                                        |
| **Mixed state**             | Staged + unstaged + untracked                        | `git status; codex exec "Review all current uncommitted work"`                 | `git status; git diff HEAD \| claude -p "PROMPT"`                       |
| **Single file / path**      | One file or directory                                | `codex exec --sandbox read-only "Review only <path> for ..."`                  | `git diff <path> \| claude -p "PROMPT"` (or tool-access for cross-file) |
| **Spec / RFC / design doc** | Markdown prose                                       | `codex exec -c model_reasoning_effort="xhigh" "Review docs/design/RFC.md ..."` | `cat docs/design/RFC.md \| claude -p "PROMPT"` (max effort, see policy) |
| **Focused investigation**   | Custom (security, perf)                              | `codex exec "You are a senior <DOMAIN> engineer. Analyze <CONCERN> ..."`       | `claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT"`     |
| **Fact-check**              | Human-facing doc (spec, deck, digest)                | `codex exec --sandbox read-only "Per-claim verdicts ..."`                      | `claude -p --allowedTools "Read,Glob,Grep" -- "PROMPT"`                 |
| **Diagnosis check**         | Root-cause conclusion, before fix mode               | `codex exec "Attack this conclusion, not the code: ..."`                       | `claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT"`     |
| **Consult**                 | Undecided design question                            | `codex exec "Read docs/design.md. <open question>"`                            | `cat docs/design.md \| claude -p "QUESTION"`                            |
| **Ralph loop**              | Implement → review → fix                             | Repeat until convergence — see The Review Loop                | Repeat until convergence — see The Review Loop         |

**Billing:** every `claude -p` cell assumes the `env -u ANTHROPIC_API_KEY` prefix from Rule 4, omitted for width — drop it and the review silently meters to the API.

**The non-verdict modes:** fact-check returns per-claim verdicts (CONFIRMED / STALE / WRONG / NOT-FOUND, file:line evidence, corrected fact) as a counted scorecard — give the fact-checker repo access to the fact sources; its best catches are invented infrastructure, not prose problems. Consult has no verdict, confidence floor, or iteration cap: set a deadline and a degraded fallback so it never blocks the decision, and treat convergence between models as the confidence signal. The consulted model critiques; it does not author.

**Common scope mistakes:**

- Using `--base main` when you only want one commit (review noise from unrelated commits) → use `--commit <SHA>`
- Using `git diff` when you meant `git diff --staged` → reviewer sees WIP and produces noisy findings on incomplete code
- Using piped diff for architecture review → diff lacks surrounding context; use `--allowedTools` tool-access mode instead

**Scope & freshness:**

- Enforce scope mechanically — stdin the exact diff, commit the slice and review the commit, or pin a file list. An unscoped reviewer on a dirty branch degrades into diff tourism.
- Freeze the target while the reviewer runs; fill the wait with reads, memory capture, or other lanes — never edits to the reviewed code.
- Verdicts are perishable: a PASS is keyed to the SHA it reviewed. Any post-review edit voids it; re-review exactly the delta so the blocker is actually closed, not hand-waved.

---

## The Review Loop

Reviews iterate. Each round's brief carries the loop state so the reviewer verifies instead of re-discovering:

| Round | Brief carries                                        | Reviewer's job                                                                                  |
| ----- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| 1     | Original ask verbatim + exact scope (SHA, file list) | Broad, hostile                                                                                   |
| 2+    | Prior findings verbatim + claimed fixes + fix SHA    | Verify each fix landed with receipts; hunt new bugs the fixes introduced; don't re-litigate settled trade-offs |
| Final | Convergence check                                    | One-line contract: `PASS` / `NEEDS_CHANGES: <one sentence>`                                      |

Track convergence numerically (8 → 5 → 3 → 0 findings) and log rounds in the artifact's own Review History section, not chat. Warm-resuming the same reviewer speeds FAIL → fix convergence; a fresh reviewer for final certification is also practiced.

**Iteration budget:** the cap bounds re-litigation, not rounds. Three rounds is the default budget for code review — keep going while each round surfaces a new confirmed defect or verifies a fix; stop on oscillation or re-litigation of the same finding. Spec/plan review exits on convergence ("iterate until we love it"), with scope narrowing each round. Inbound bot/human PR feedback streams are never capped; re-triage each round fresh.

---

## Consuming Findings

Findings are claims, not orders. Re-verify each in code, git history, or live data before any edit — reviewers hallucinate flags, review the wrong commit state, and raise findings that were true at review time but stale at HEAD. "Verified, no code change" is a legitimate outcome; one audited session disproved 3 of 4 findings and changed nothing.

| Disposition      | When                                | Action                                                              |
| ---------------- | ----------------------------------- | ------------------------------------------------------------------- |
| Fix now          | Verified true, in blast radius      | Fix; blockers require changed-line causality                        |
| Intentional keep | Verified, but the code is right     | Name the rationale; argue wrong findings down with receipts, never silently drop |
| Can't verify     | Needs live data or human judgment   | Flag to the human                                                    |

Report the disposition ledger ("took 4, declined 3 with reasons, flagged 2") — on the PR when humans are watching. Scorecard the reviewer ("4 right, 3 wrong, 2 nits") to calibrate trust. Two independently-briefed reviewers converging on the same bug upgrades it to confirmed.

**Scope membrane for fix passes:** review-fix loops are a monotonic scope ratchet — pointed at a PR and told to iterate until clean, a reviewer will eventually touch 100 files. Pre-declare a file budget before the fix pass. Blockers need changed-line causality; suggestions may cover nearby risk; everything else is a follow-up. Cheap nits on a PASS still get adopted. Give push-triggered reviewers a named stop condition: green with only non-blocking suggestions = done.

---

## Sandbox & Permission Flags

Both CLIs scope what the reviewer can read, write, and execute. Default to the most restrictive that does the job.

### Codex sandbox modes

`codex exec` and `codex review` accept `--sandbox <mode>`:

| Mode                 | Read | Write    | Network | Use for                                 |
| -------------------- | ---- | -------- | ------- | --------------------------------------- |
| `read-only`          | ✓    | ✗        | ✗       | Pure review (default for review work)   |
| `workspace-write`    | ✓    | cwd only | ✗       | Review + apply suggested fixes          |
| `danger-full-access` | ✓    | ✓        | ✓       | Last resort; explicit user request only |

### Codex flags worth knowing (as of Jul 2026)

| Flag                                | When                                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------------------------ |
| `--skip-git-repo-check`             | Running from a non-repo directory                                                          |
| `--add-dir <DIR>`                   | Extend read access to another path                                                         |
| `--json` / `--output-last-message`  | Capture the verdict; read-only sandboxes silently fail to write a requested report file    |
| `-c model_reasoning_effort="xhigh"` | Spec/RFC review only (see Effort Override Policy)                                          |

Version-pinned CLI flags are the fastest-rotting content a skill can carry — a documented `--sandbox` form was already rejected by a newer codex build in the field. When the installed CLI disagrees with this table, the CLI wins; flag the skill for a patch.

### Claude permission flags (`claude -p`)

| Flag                                          | When                                            |
| --------------------------------------------- | ----------------------------------------------- |
| `--allowedTools "Read,Glob,Grep,Bash(git *)"` | Standard read-only review toolset (recommended) |
| `--add-dir <PATH>`                            | Read access outside cwd                         |
| `--no-session-persistence`                    | Sanity pings; one-shot calls                    |
| `--output-format text` / `json`               | Capture for parsing                             |
| `--dangerously-skip-permissions`              | Last resort; explicit user request only         |

The default toolset for Codex → Claude is `--allowedTools "Read,Glob,Grep,Bash(git *)"`. Add `Bash(rg:*)` if the reviewer needs grep across files. Resist write tools unless the review explicitly applies fixes. One guarded opt-in is field-proven: the brief may allow "do not modify files unless you find a real defect and can fix it surgically; if you do edit, list exact files changed" — real defect, surgical fix, disclosed in the verdict.

---

## Effort Override Policy

Code review defers to user config. Spec review overrides higher.

| What you're reviewing           | Codex effort                                 | Claude effort                  |
| ------------------------------- | -------------------------------------------- | ------------------------------ |
| Code (commit / diff / PR / WIP) | **No flag**, defer to `~/.codex/config.toml` | **No flag**, defer to settings |
| Spec / RFC / design doc         | `-c model_reasoning_effort="xhigh"`          | `max`                          |

**Why split:** specs are higher-stakes than diffs, a subtle architectural mistake compounds across the eventual implementation. Code diffs are smaller scope and the user's configured effort is fine.

**Scope before effort.** The override applies only to an already-scoped review: falsifiable claims, an explicit convergence budget ("be surgical — budget your exploration, converge to a verdict"), and clean verdict capture (`--output-last-message`). Effort amplifies scope: one unscoped xhigh review produced 80k lines of exploration transcript and no verdict; the relaunch that converged narrowed the scope and lowered effort. When a review must converge, narrow the scope — and consider lower effort, not higher.

---

## Piped Diff vs Tool Access (Codex → Claude)

For Codex-hosted sessions, choose based on depth:

| Approach        | Command shape                                                       | When                                                                                                         |
| --------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Piped diff**  | `git diff ... \| claude -p "PROMPT"`                                | Quick review; reviewer sees only the diff. Faster, cheaper.                                                  |
| **Tool access** | `claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT"` | Architecture/security/cross-file deep-dive. Reviewer can trace data flow across files the diff doesn't show. |

Tool access costs more tokens but catches bugs that need surrounding context (signatures defined elsewhere, downstream consumers, similar patterns). Both shapes take the `env -u ANTHROPIC_API_KEY` prefix (Rule 4).

---

## Multi-Pass Strategy

Thorough reviews use multiple focused passes rather than one vague pass — single passes dilute attention and produce shallow findings on every dimension. Each pass gets a persona and one concern domain.

| Pass             | Focus                                       | Approach                                                             |
| ---------------- | ------------------------------------------- | -------------------------------------------------------------------- |
| **Correctness**  | Bugs, logic, edge cases, race conditions    | Structured review (`codex review`) or piped diff with general prompt |
| **Security**     | OWASP Top 10:2025, injection, auth, secrets | Focused investigation with security persona                          |
| **Architecture** | Coupling, abstractions, API consistency     | Tool-access mode for full file context                               |
| **Performance**  | O(n²), N+1 queries, memory leaks            | Focused investigation with performance persona                       |

Ceremony scales with blast radius, not line count: security-sensitive changes (auth, payments, crypto) always get the security pass; the user can waive the loop for trivial diffs and demand more for big ones. Fix critical findings between passes to avoid noise compounding. Spec-level review and code-level verification are complements, not substitutes — they catch the same invariant at different altitudes.

---

## Prompt Engineering Heuristics

These apply to both directions; prompts are model-agnostic and reliably improve review signal:

1. **Assign a persona.** "Senior security engineer" beats "review for security"
2. **Specify what to skip.** "Skip formatting, naming style, minor docs gaps" prevents bikeshedding
3. **Require confidence scores** and act only on findings ≥ 0.7
4. **Demand file:line citations.** Vague findings without location aren't actionable
5. **Ask for concrete fixes.** "Suggest a specific fix"
6. **One domain per pass.** Security-only, architecture-only
7. **Demand a shaped verdict.** PASS carries the evidence list, residual risks, and the evidence tier actually reached (executed / static analysis / traced) — a blocked gate steps down the ladder and says so. FAIL carries blockers with file:line, what's verified-good, the smallest fix, and a repro
8. **Ask for one executable probe** beyond the existing suite — "Prove the code works, don't just confirm it exists"
9. **Recall before dispatch.** Prior gotchas for this lane become the review's attack plan; when memory comes back empty, say so and review from live repo evidence

When a review closes a defect class, fold it into the repo's standing review prompt or CI gate so the next reviewer inherits it. A recurring reviewer hallucination is a corpus bug — scrub the stale docs the reviewer ingests.

Ready-to-use prompt templates — security, architecture, performance, error handling, concurrency, plus the annotated dispatch brief, fix re-verification, fact-check, and consult templates — are in `references/prompts.md`.

---

## Anti-Patterns

| Anti-Pattern                                                            | Why It Fails                                                                                                                           | Fix                                                                                                                           |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Self-review (model reviews its own code)                                | Systematic bias, same blind spots                                                                                                      | Cross-model: author and reviewer are different models                                                                         |
| Re-litigating a settled finding round after round                       | Oscillation without new confirmed defects                                                                                              | Stop; the budget bounds re-litigation, not converging rounds (see The Review Loop)                                            |
| Hardcoding `--model` / `-m` / `-c model=`                               | Overrides user config; stale model names                                                                                               | Defer to user config; only `model_reasoning_effort` for spec review                                                           |
| `claude -p --allowedTools "..." "PROMPT"` (no `--`)                     | Variadic flag eats the prompt                                                                                                          | Always the `--` separator — see Rule 3                                                                                        |
| `yield_time_ms` under 300000, or reverting to 1000 mid-session          | Empty yields read as failure; orphans pile up                                                                                          | 300000 on every call — see Rule 1                                                                                             |
| Re-invoking `claude -p` after `Process running with session ID NNNN`    | Spawns a parallel claude; original still working                                                                                       | Reap the session — see Rule 2                                                                                                 |
| `claude -p` from Codex with `ANTHROPIC_API_KEY` in the env              | Review silently bills per-token to the API                                                                                             | `env -u ANTHROPIC_API_KEY` on the spawning call — see Rule 4                                                                  |
| Bare `codex review` (no scope flag)                                     | Hangs or produces 100KB+ blob output                                                                                                   | Exactly one scope flag — see the Claude → Codex rule                                                                          |
| Shell `timeout` wrapped around a review                                 | Reviews legitimately take 30s–5min+; false exit-124 failures                                                                           | No shell timeout by default — see Failure Recovery                                                                              |
| Piping a review to `tail -300` / `head -300`                            | Pipe buffers until EOF; discards the verdict (usually near the top)                                                                    | Redirect to a file — see Capture Output to a File                                                                             |
| Printing `review_output=/tmp/...` but not redirecting Claude there      | The path exists but the output never lands there                                         | Always run `claude ... > "$out" 2>&1` after echoing the path                                                                  |
| Assigning `status=$?` in Codex shell snippets                           | zsh reserves `status` as read-only                                                                                                     | Use `rc=$?` — see the Gold Path                                                                                               |
| `<<'EOF'` heredoc when prompt references env vars                       | Single-quoted heredoc blocks expansion; vars stay literal                                                                              | Use `<<EOF` (unquoted) when interpolation is needed                                                                           |
| Trying `claude ultrareview` first                                       | Many orgs block ("Remote sessions are disabled by your organization's policy")                                                         | Local `claude -p` first; ultrareview is opt-in                                                                                |
| MCP wrapper around `codex` / `claude`                                   | Unnecessary indirection over a CLI binary                                                                                              | Call the reviewer CLI directly via Bash                                                                                       |
| Reviewing without repo context                                          | Generic advice disconnected from codebase                                                                                              | Run from repo root so project memory + source files are visible                                                               |

---

## What This Skill is NOT

- Not a replacement for human review, can't evaluate product direction or UX
- Not a linter, use linters for formatting and style
- Not infallible, 5–15% false positive rate is normal; triage findings
- Not for self-approval, the entire point is cross-model validation
- Not protection against shared-training staleness — version, SOTA, and ecosystem claims need a live primary source (registry, release page, official docs) no matter how many models agreed
- Not protection against a mis-stated brief — a reviewer briefed with your paraphrase validates the wrong intent; carry the user's verbatim ask and invite the reviewer to challenge the interpretation
- Not automatically cross-family — verify the reviewer is genuinely a different model family (see Degradation Ladder)
- Not execution — a multi-model PASS on declarative artifacts (migrations, manifests) is still review eyes; apply them for real before trusting them

## References

- `references/prompts.md` — prompt templates: security, architecture, performance, error handling, concurrency, plus the annotated dispatch brief, fix re-verification, fact-check, and consult templates.
- `references/failure-recovery.md` — the full symptom → recovery triage table and the reviewer hang ladder.
