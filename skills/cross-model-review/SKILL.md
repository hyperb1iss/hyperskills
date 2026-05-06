---
name: cross-model-review
description: Use this skill for cross-model code reviews where a different AI model reviews code written by the current model. Activates on mentions of cross-model review, peer review, second opinion, review my code, review this PR, review changes, independent review, unbiased review, different model review, cross-check code, or code review.
---

# Cross-Model Code Review

Cross-model validation: the authoring model writes code, a different model reviews it. Different architectures, different training distributions, no self-approval bias.

**Core insight:** Single-model self-review is systematically biased — the same blind spots that let bugs through during writing let them through during review. Cross-model review catches different bug classes because the reviewer has fundamentally different failure modes.

## Direction & Pre-Flight

Identify the host first. The host runs the *other* model's CLI as a subprocess.

| Current host | You invoke   | Direction                     |
| ------------ | ------------ | ----------------------------- |
| Claude Code  | `codex` CLI  | Claude writes → Codex reviews |
| Codex        | `claude` CLI | Codex writes → Claude reviews |

Confirm the reviewer is reachable before the real call:

| Host  | Verify command                                                                                                       | Notes                          |
| ----- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Claude | `codex --version`                                                                                                   | One-shot, no special flags     |
| Codex | `printf 'say ok\n' \| claude -p --output-format text --no-session-persistence` with `yield_time_ms: 30000`            | Sanity ping only — see Rule 1  |

**User defaults are authoritative.** Both CLIs read configured defaults (`~/.codex/config.toml`, `~/.claude/settings.json`). Never specify `--model`, `-m`, or `-c model=`. The only sanctioned override is reasoning effort, and only for spec review (see Effort Override Policy below).

---

## ⚠️ Codex → Claude: Three Non-Negotiable Rules

These three rules cause the overwhelming majority of cross-model review failures. Audited sessions show 366+ orphaned `claude -p` processes per session, ~7 minutes wasted per spiral. Get these right on the first call.

### Rule 1: `yield_time_ms: 300000` on EVERY call

Codex's shell tool yields output back to the model after `yield_time_ms` elapses (default `1000` = 1 second). A real `claude -p` review takes 30 seconds to 5+ minutes. The default yields empty output + `Process running with session ID NNNN` before Claude has even started, and the model misreads this as failure.

**The rule:** every `claude -p` call uses `yield_time_ms: 300000` (5 minutes). Initial call, every reaping call, every sanity ping beyond a one-line `say ok`. No exceptions.

```json
{"cmd": "claude -p --allowedTools \"Read,Glob,Grep,Bash(git *)\" -- \"PROMPT\"", "yield_time_ms": 300000}
```

**Common cognitive trap:** "My prompt is short, I only need 30s." Wrong — claude session setup, network, and model compute dominate; prompt length barely factors in. Always 300000.

**Consistency rule:** once you're at 300000, stay at 300000. Reverting to 1000 between calls in the same session creates a fresh wave of orphans on top of any still running.

### Rule 2: `Process running with session ID NNNN` is NOT an error — REAP, never retry

When Codex returns `Process running with session ID NNNN`, the process is alive and computing in the background. The yield fired before completion. **This is normal output, not failure.**

```dot
digraph reap {
    rankdir=TB;
    node [shape=box];

    "Initial call" [style=filled, fillcolor="#e8e8ff"];
    "Process running ID 84814" [style=filled, fillcolor="#fff8e0"];
    "WRONG: re-invoke claude -p" [style=filled, fillcolor="#ffe8e8"];
    "RIGHT: reap session_id 84814" [style=filled, fillcolor="#e8ffe8"];
    "Process exited code 0" [style=filled, fillcolor="#e8ffe8"];
    "New orphan ID 84815" [style=filled, fillcolor="#ffe8e8"];

    "Initial call" -> "Process running ID 84814";
    "Process running ID 84814" -> "WRONG: re-invoke claude -p" [label="retry"];
    "Process running ID 84814" -> "RIGHT: reap session_id 84814" [label="reap"];
    "WRONG: re-invoke claude -p" -> "New orphan ID 84815" [label="spawns new process"];
    "RIGHT: reap session_id 84814" -> "Process exited code 0" [label="loop until exit"];
}
```

**Wrong** (each retry spawns a fresh process; original keeps running):

```json
{"cmd": "claude -p --allowedTools '...' -- 'PROMPT'", "yield_time_ms": 300000}
→ "Process running with session ID 84814"
{"cmd": "claude -p --allowedTools '...' -- 'PROMPT'", "yield_time_ms": 300000}
→ "Process running with session ID 84815"   // 84814 still alive — orphaned
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
→ "Process exited with code 0"                        // done — parse the output
```

**Reaping rules:**

- Do NOT re-invoke `claude -p` (creates a new process)
- Do NOT change flags, prompts, or tools (reaping is a different operation entirely)
- DO call `{"session_id": NNNN, "yield_time_ms": 300000}` repeatedly
- Stop only when `Process exited with code X` appears

### Rule 3: Variadic flags require the `--` separator

The `claude` CLI has flags that take `<value...>` and greedily consume every following argument until the next flag. If your prompt follows one of these without a `--` separator, the prompt gets swallowed as a flag value, the prompt arg goes missing, and Claude errors with `Input must be provided either through stdin or as a prompt argument when using --print` or hangs waiting on stdin.

**Variadic flags:** `--allowedTools` / `--allowed-tools`, `--disallowedTools` / `--disallowed-tools`, `--tools`, `--add-dir`, `--betas`, `--file`, `--mcp-config`, `--plugin-dir`.

**Required form** (default to this — works regardless of flag order):

```bash
claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT"
```

**Two fallback shapes** (use only if `--` won't work in your context):

| Shape | Example |
| ----- | ------- |
| Prompt before flags | `claude -p "PROMPT" --allowedTools "Read,Bash(git *)"` |
| Stdin pipe | `echo "PROMPT" \| claude -p --allowedTools "Read,Bash(git *)"` |

The `codex` CLI does not have this issue — its flags are non-variadic.

---

## ⚠️ Claude → Codex: One Non-Negotiable Rule

### Always pass a scope flag to `codex review`

A bare `codex review` (no scope) is the #1 cause of Claude → Codex failures: it hangs or produces 100KB+ blob output. **Always specify exactly one scope flag:**

| Want to review | Command |
| -------------- | ------- |
| Branch since main | `codex review --base main` |
| Single commit | `codex review --commit <SHA>` |
| Working tree (unstaged) | `codex review --uncommitted` |

For anything outside this trio (spec docs, single files, custom scopes, personas), use `codex exec "PROMPT"` with explicit scope in the prompt — never bare `codex review`.

If `codex review` output exceeds ~100KB, the diff is too large for one pass. Split: `codex review --commit <SHA1>`, `codex review --commit <SHA2>`, or use `codex exec` with a narrowed prompt ("Review error handling only").

---

## ⚠️ Both Directions: Capture Output to a File

**Never** pipe a review to `| tail -N` or `| head -N`. Three reasons it fails:

1. **The pipe buffers until EOF.** `tail` (and `head`) read the entire upstream stream before producing output. The agent gets *nothing* until the review process exits or times out — no progress signal, no early verdict, no way to tell if the call is alive. With `claude -p`, this compounds the `yield_time_ms` problem: the wrapping shell call holds output until claude exits, then `tail` finally runs.
2. **Reviews don't put the verdict at the end.** Findings are typically ordered by severity (BLOCKER first), with the summary/verdict near the top. `tail -300` discards exactly the part you need.
3. **A file lets a human watch progress live.** `tail -f /tmp/review.txt` in another terminal shows the review streaming in real time, completely independent of the agent's call. The pipe pattern hides everything until exit.

**Right pattern:** pick a non-colliding filename, redirect to it, then read it back.

```bash
# Use mktemp so parallel/repeat reviews don't clobber each other.
# Bake the scope into the slug so the file is self-describing when you tail -f it.
out=$(mktemp -t codex-review-pre-pr.XXXXXX) && echo "$out"

# Claude → Codex
codex review --base main > "$out" 2>&1
codex exec --sandbox read-only "PROMPT" > "$out" 2>&1

# Codex → Claude (yield_time_ms: 300000 still required on the shell call)
claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT" > "$out" 2>&1
git diff main...HEAD | claude -p "PROMPT" > "$out" 2>&1
```

If `mktemp` isn't handy, use a PID + timestamp slug: `out=/tmp/codex-review-$$-$(date +%s).txt`.

Echo the path before the redirect so the agent (and a human running `tail -f`) knows where to look. After the command exits, `Read` (or `cat`) the file. It persists across turns — re-read instead of re-running.

---

## Review Modes Matrix

Match the row to what you're actually reviewing. The current skill historically documented 5 patterns; real usage covers many more.

| Mode | Scope | Claude → Codex | Codex → Claude |
| ---- | ----- | -------------- | -------------- |
| **Pre-PR full** | `main...HEAD` (all commits on branch) | `codex review --base main` | `git diff main...HEAD \| claude -p "PROMPT"` |
| **Single commit** | One SHA | `codex review --commit <SHA>` | `git show <SHA> \| claude -p "PROMPT"` |
| **Commit range** | `<base>..HEAD` (multi-commit slice, not all of main) | `codex review --base <base>` | `git diff <base>..HEAD \| claude -p "PROMPT"` |
| **Branch-vs-branch** | feat-a vs feat-b (stacked PRs) | `codex review --base feat-a` | `git diff feat-a...HEAD \| claude -p "PROMPT"` |
| **Staged only** | About-to-commit | `git diff --staged \| codex exec "PROMPT"` | `git diff --staged \| claude -p "PROMPT"` |
| **Unstaged WIP** | Working tree | `codex review --uncommitted` | `git diff \| claude -p "PROMPT"` |
| **Mixed state** | Staged + unstaged + untracked | `git status; codex exec "Review all current uncommitted work"` | `git status; git diff HEAD \| claude -p "PROMPT"` |
| **Single file / path** | One file or directory | `codex exec --sandbox read-only "Review only <path> for ..."` | `git diff <path> \| claude -p "PROMPT"` (or tool-access for cross-file) |
| **Spec / RFC / design doc** | Markdown prose | `codex exec -c model_reasoning_effort="xhigh" "Review docs/design/RFC.md ..."` | `cat docs/design/RFC.md \| claude -p "PROMPT"` (max effort, see policy) |
| **Focused investigation** | Custom (security, perf) | `codex exec "You are a senior <DOMAIN> engineer. Analyze <CONCERN> ..."` | `claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT"` |
| **Ralph loop** | Implement → review → fix | Repeat any of the above × 3 max | Repeat any of the above × 3 max |

**Common scope mistakes:**

- Using `--base main` when you only want one commit (review noise from unrelated commits) → use `--commit <SHA>`
- Using `git diff` when you meant `git diff --staged` → reviewer sees WIP and produces noisy findings on incomplete code
- Using piped diff for architecture review → diff lacks surrounding context; use `--allowedTools` tool-access mode instead

---

## Sandbox & Permission Flags

Both CLIs scope what the reviewer can read, write, and execute. Default to the most restrictive that does the job.

### Codex sandbox modes

`codex exec` and `codex review` accept `--sandbox <mode>`:

| Mode                             | Read | Write     | Network | Use for                                    |
| -------------------------------- | ---- | --------- | ------- | ------------------------------------------ |
| `read-only`                      | ✓    | ✗         | ✗       | Pure review (default for review work)      |
| `workspace-write`                | ✓    | cwd only  | ✗       | Review + apply suggested fixes             |
| `danger-full-access`             | ✓    | ✓         | ✓       | Last resort; explicit user request only    |
| `--full-auto` (alias)            | —    | —         | —       | `--ask-for-approval never --sandbox workspace-write` |
| `--dangerously-bypass-approvals-and-sandbox` | — | — | — | Last resort; full bypass               |

### Codex working-directory and ergonomics flags

| Flag                                | When                                              |
| ----------------------------------- | ------------------------------------------------- |
| `-C <DIR>` / `--cd <DIR>`           | Run in another worktree without `cd`              |
| `--skip-git-repo-check`             | Running from a non-repo directory                 |
| `--add-dir <DIR>`                   | Extend read access to another path                |
| `--ephemeral`                       | One-shot session, no persistence                  |
| `--ignore-user-config`              | Skip `~/.codex/config.toml` (unusual)             |
| `--json` / `--output-last-message`  | Capture structured output to a file               |
| `-c model_reasoning_effort="xhigh"` | Spec/RFC review only (see Effort Override Policy) |

### Claude permission flags (`claude -p`)

| Flag                                          | When                                              |
| --------------------------------------------- | ------------------------------------------------- |
| `--allowedTools "Read,Glob,Grep,Bash(git *)"` | Standard read-only review toolset (recommended)   |
| `--add-dir <PATH>`                            | Read access outside cwd                           |
| `--no-session-persistence`                    | Sanity pings; one-shot calls                      |
| `--output-format text` / `json`               | Capture for parsing                               |
| `--dangerously-skip-permissions`              | Last resort; explicit user request only           |

The default toolset for Codex → Claude is `--allowedTools "Read,Glob,Grep,Bash(git *)"`. Add `Bash(rg:*)` if the reviewer needs grep across files. Resist write tools unless the review explicitly applies fixes.

---

## Effort Override Policy

Code review defers to user config. Spec review overrides higher.

| What you're reviewing                | Codex effort                              | Claude effort |
| ------------------------------------ | ----------------------------------------- | ------------- |
| Code (commit / diff / PR / WIP)      | **No flag** — defer to `~/.codex/config.toml` | **No flag** — defer to settings |
| Spec / RFC / design doc              | `-c model_reasoning_effort="xhigh"`       | `max`         |

**Why split:** specs are higher-stakes than diffs — a subtle architectural mistake compounds across the eventual implementation. Code diffs are smaller scope and the user's configured effort is fine.

---

## Piped Diff vs Tool Access (Codex → Claude)

For Codex-hosted sessions, choose based on depth:

| Approach | Command shape | When |
| -------- | ------------- | ---- |
| **Piped diff** | `git diff ... \| claude -p "PROMPT"` | Quick review; reviewer sees only the diff. Faster, cheaper. |
| **Tool access** | `claude -p --allowedTools "Read,Glob,Grep,Bash(git *)" -- "PROMPT"` | Architecture/security/cross-file deep-dive. Reviewer can trace data flow across files the diff doesn't show. |

Tool access costs more tokens but catches bugs that need surrounding context (signatures defined elsewhere, downstream consumers, similar patterns).

---

## Multi-Pass Strategy

Run multiple focused passes for thorough reviews. Each pass gets a specific persona and concern domain.

| Pass             | Focus                                       | Approach                                                             |
| ---------------- | ------------------------------------------- | -------------------------------------------------------------------- |
| **Correctness**  | Bugs, logic, edge cases, race conditions    | Structured review (`codex review`) or piped diff with general prompt |
| **Security**     | OWASP Top 10:2025, injection, auth, secrets | Focused investigation with security persona                          |
| **Architecture** | Coupling, abstractions, API consistency     | Tool-access mode for full file context                               |
| **Performance** | O(n²), N+1 queries, memory leaks            | Focused investigation with performance persona                       |

| Change size                                 | Strategy                     |
| ------------------------------------------- | ---------------------------- |
| < 50 lines, single concern                  | Single review pass           |
| 50-300 lines, feature work                  | Review + security pass       |
| 300+ lines or architecture change           | Full 4-pass                  |
| Security-sensitive (auth, payments, crypto) | Always include security pass |

Run passes sequentially. Fix critical findings between passes to avoid noise compounding. Stop at 3 review iterations max.

---

## Prompt Engineering Rules

These apply to both directions — prompts are model-agnostic.

1. **Assign a persona** — "senior security engineer" beats "review for security"
2. **Specify what to skip** — "Skip formatting, naming style, minor docs gaps"
3. **Require confidence scores** — only act on findings ≥ 0.7
4. **Demand file:line citations** — vague findings aren't actionable
5. **Ask for concrete fixes** — "Suggest a specific fix"
6. **One domain per pass** — security-only, architecture-only
7. **Demand a verdict** — "Verdict: patch is correct / incorrect" or "go / no-go"

Ready-to-use prompt templates for security, architecture, performance, error handling, and concurrency are in `references/prompts.md`.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
| ------------ | ------------ | --- |
| Self-review (model reviews its own code) | Systematic bias — same blind spots | Cross-model: author and reviewer are different models |
| "Review this code" (no specifics) | Vague → bikeshedding | Domain prompt + persona + structured output |
| Single pass for everything | Context dilution | Multi-pass, one concern per pass |
| No confidence threshold | Noise floods signal | Only act on ≥ 0.7 |
| > 3 review iterations | Diminishing returns | Stop at 3, accept trade-offs |
| Hardcoding `--model` / `-m` / `-c model=` | Overrides user config; stale model names | Defer to user config; only `model_reasoning_effort` for spec review |
| `claude -p --allowedTools "..." "PROMPT"` (no `--`) | Variadic flag eats prompt → "Input must be provided" or hang | Always `--` separator: `claude -p --allowedTools "..." -- "PROMPT"` |
| `yield_time_ms: 1000` (or any value < 300000) on `claude -p` | Yields empty output before claude responds; model treats as failure and retries | `yield_time_ms: 300000` on EVERY call, no exceptions |
| Reverting `yield_time_ms` mid-session (300000 → 1000 between calls) | New orphans pile on top of existing ones | Pick 300000 once, keep it for every call |
| Re-invoking `claude -p` after `Process running with session ID NNNN` | Spawns a parallel claude; original still working | Reap with `{"session_id": NNNN, "yield_time_ms": 300000}` until exit code |
| Bare `codex review` (no scope flag) | Hangs or produces 100KB+ blob output | Always pass `--base <ref>`, `--commit <SHA>`, or `--uncommitted` |
| `codex review` output > 100KB | Diff too large for one pass | Split per commit, or use `codex exec` with narrower prompt |
| `timeout 30 codex review` or `timeout 30 claude -p` | Reviews legitimately take 30s–5min | No timeout, or `timeout 300` minimum |
| `codex exec "PROMPT" \| tail -300` or `claude -p "PROMPT" \| tail -300` | Pipe buffers until EOF (no progress signal); discards summary/verdict (usually near top); slurps full review into agent context window | Redirect to a file: `... > /tmp/review.txt 2>&1`. Then `head`, `rg severity`, `sed`-by-range. Human can `tail -f` separately. |
| `<<'EOF'` heredoc when prompt references env vars | Single-quoted heredoc blocks expansion; vars stay literal | Use `<<EOF` (unquoted) when interpolation is needed |
| Trying `claude ultrareview` first | Many orgs block ("Remote sessions are disabled by your organization's policy") | Local `claude -p` first; ultrareview is opt-in |
| Style/formatting comments in review | LLMs default to bikeshedding | Always include "Skip: formatting, naming, minor docs" |
| Piped diff for architecture review | Diff lacks surrounding context | Use tool-access mode (`--allowedTools`) |
| MCP wrapper around `codex` / `claude` | Unnecessary indirection over a CLI binary | Call the reviewer CLI directly via Bash |
| Reviewing without repo context | Generic advice disconnected from codebase | Run from repo root so project memory + source files are visible |
| Effort override on routine code review | Wastes tokens, ignores user defaults | Spec review only; code review = no effort flag |

---

## What This Skill is NOT

- Not a replacement for human review — can't evaluate product direction or UX
- Not a linter — use linters for formatting and style
- Not infallible — 5–15% false positive rate is normal; triage findings
- Not for self-approval — the entire point is cross-model validation

## References

For ready-to-use prompt templates (security, architecture, performance, error handling, concurrency), see `references/prompts.md`.
