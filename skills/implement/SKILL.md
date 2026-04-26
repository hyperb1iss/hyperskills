---
name: implement
description: Use this skill when writing code — building features, fixing bugs, refactoring, or any multi-step implementation work. Activates on mentions of implement, build this, code this, start coding, fix this bug, refactor, make changes, develop this feature, implementation plan, coding task, write the code, or start building.
---

# Implementation

Verification-driven coding with tight feedback loops. Distilled from 21,321 tracked operations across 64+ projects, 612 debugging sessions, and 2,476 conversation histories. These are the patterns that consistently ship working code.

**Core insight:** 2-3 edits then verify. 73% of fixes go unverified — that's the #1 quality gap. The difference between a clean session and a debugging spiral is verification cadence.

## The Sequence

Every implementation follows the same macro-sequence, regardless of scale:

```dot
digraph implement {
    rankdir=LR;
    node [shape=box];

    "ORIENT" [style=filled, fillcolor="#e8e8ff"];
    "PLAN" [style=filled, fillcolor="#fff8e0"];
    "IMPLEMENT" [style=filled, fillcolor="#ffe8e8"];
    "VERIFY" [style=filled, fillcolor="#e8ffe8"];
    "COMMIT" [style=filled, fillcolor="#e8e8ff"];

    "ORIENT" -> "PLAN";
    "PLAN" -> "IMPLEMENT";
    "IMPLEMENT" -> "VERIFY";
    "VERIFY" -> "IMPLEMENT" [label="fix", style=dashed];
    "VERIFY" -> "COMMIT" [label="pass"];
    "COMMIT" -> "IMPLEMENT" [label="next chunk", style=dashed];
}
```

**ORIENT** — Read existing code before touching anything. `Grep -> Read -> Read` is the dominant opening. Sessions that read 10+ files before the first edit require fewer fix iterations. Never start with blind changes.

**PLAN** — Scale-dependent (see below). Skip for trivial fixes, write a task list for features, run a research swarm for epics.

**IMPLEMENT** — Work in batches of 2-3 edits, then verify. Follow the dependency chain. Edit existing files 9:1 over creating new ones. Fix errors immediately — don't accumulate them.

**VERIFY** — Typecheck is the primary gate. Run it after every 2-3 edits. Run tests after feature-complete. Run the full suite before commit.

**COMMIT** — Atomic chunks, committed as you go. Verify, stage specific files, commit, then loop back to the next chunk. Many small commits per session is the norm. See **Commit Cadence** below for message anatomy.

---

## Code Discipline

Behavioral lens that governs every phase of the loop. Adapted from Karpathy's [observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls — models "make wrong assumptions on your behalf and just run along with them without checking ... they really like to overcomplicate code and APIs, bloat abstractions ... implement a bloated construction over 1000 lines when 100 would do."

These principles bias toward caution over speed. For trivial fixes, use judgment.

### Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

| Situation                                | Action                            |
| ---------------------------------------- | --------------------------------- |
| Multiple interpretations of the request  | Present them; don't pick silently |
| A simpler approach is plausible          | Say so; push back when warranted  |
| Something is unclear                     | Stop; name what's confusing; ask  |
| You hold a load-bearing assumption       | State it explicitly               |
| Inconsistency between request and code   | Surface it before proceeding      |

ORIENT (read the code) is the prerequisite. This principle is what to do with what you find: name the gaps, don't paper over them.

### Simplicity first

Minimum code that solves the problem. Nothing speculative.

| Don't                                            | Do                                            |
| ------------------------------------------------ | --------------------------------------------- |
| Add features beyond what was asked               | Solve exactly the stated problem              |
| Build abstractions for single-use code           | Inline first; abstract when reused            |
| Add "flexibility" or configurability not asked   | Hardcode now; parameterize on demand          |
| Handle errors for impossible scenarios           | Trust internal invariants; validate at edges  |
| Write 200 lines when 50 would do                 | Rewrite tighter                               |

The test: would a senior engineer call this overcomplicated? If yes, simplify.

### Surgical changes

Touch only what you must. Clean up only your own mess.

| Rule                                                  | Why                                              |
| ----------------------------------------------------- | ------------------------------------------------ |
| Don't "improve" adjacent code, comments, or formatting | Pollutes the diff; outside your scope           |
| Don't refactor code that isn't broken                 | Scope creep expands blast radius                 |
| Match existing style even if you'd do it differently  | Local consistency beats your preferences         |
| Notice unrelated dead code → mention, don't delete    | Other branches/agents may rely on it             |
| Remove imports/vars/funcs *your* changes orphaned     | Clean up after yourself                          |
| Leave pre-existing dead code alone                    | Outside your remit unless explicitly asked       |
| Don't touch comments you don't understand             | Karpathy: "side effects ... orthogonal to task"  |

The test: every changed line should trace directly to the user's request.

### Goal-driven execution

Define verifiable success. Loop until it passes.

| Vague task        | Verifiable goal                                       |
| ----------------- | ----------------------------------------------------- |
| "Add validation"  | Write tests for invalid inputs, then make them pass   |
| "Fix the bug"     | Write a test that reproduces it, then make it pass    |
| "Refactor X"      | Ensure the same tests pass before and after           |
| "Make it work"    | Reject — name the actual signal that proves it works  |

For multi-step work, state the plan with verification per step:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria require constant clarification.

---

## Scale Selection

Strategy changes dramatically based on scope. Pick the right weight class:

| Scale                      | Edits   | Strategy                                                 |
| -------------------------- | ------- | -------------------------------------------------------- |
| **Trivial** (config, typo) | 1-5     | Read -> Edit -> Verify -> Commit                         |
| **Small fix**              | 5-20    | Grep error -> Read -> Fix -> Test -> Commit              |
| **Feature**                | 50-200  | Plan -> Layer-by-layer impl -> Verify per layer          |
| **Subsystem**              | 300-500 | Task planning -> Wave dispatch -> Layer-by-layer         |
| **Epic**                   | 1000+   | Research swarm -> Spec -> Parallel agents -> Integration |

**Skip planning when:** Scope is clear, single-file change, fix describable in one sentence.

**Plan when:** Multiple files, unfamiliar code, uncertain approach.

---

## Dependency Chain

Build things in this order. Validated across fullstack, Rust, and monorepo projects:

```
Types/Models -> Backend Logic -> API Routes -> Frontend Types -> Hooks/Client -> UI Components -> Tests
```

**Fullstack (Python + TypeScript):**

1. Database model + migration
2. Service/business logic layer
3. API routes (FastAPI or tRPC)
4. Frontend API client
5. React hooks wrapping API calls
6. UI components consuming hooks
7. Lint -> typecheck -> test -> commit

**Rust:**

1. Error types (`thiserror` enum with `#[from]`)
2. Type definitions (structs, enums)
3. Core logic (`impl` blocks)
4. Module wiring (`mod.rs` re-exports)
5. `cargo check` -> `cargo clippy` -> `cargo test`

**Key finding:** Database migrations are written AFTER the code that needs them. Frontend drives backend changes as often as the reverse.

---

## Verification Cadence

The single most impactful practice. Get this right and everything else follows.

| Gate                   | When                       | Speed               |
| ---------------------- | -------------------------- | ------------------- |
| **Typecheck**          | After every 2-3 edits      | Fast (primary gate) |
| **Lint (autofix)**     | After implementation batch | Fast                |
| **Tests (specific)**   | After feature complete     | Medium              |
| **Tests (full suite)** | Before commit              | Slow                |
| **Build**              | Before PR/deploy only      | Slowest             |

### The Edit-Verify-Fix Cycle

The sweet spot: **3 changes -> verify -> 1 fix**. This is the most common successful pattern.

The expensive pattern: **2 changes -> typecheck -> 15 fixes** (type cascade). Prevent by grepping all consumers before modifying shared types.

**Combined gates save time:** `turbo lint:fix typecheck --filter=pkg` runs both in one shot. Scope verification to affected packages, never the full monorepo.

**Practical tips:**

- Run `lint:fix` BEFORE `lint` check to reduce iterations
- `cargo check` over `cargo build` (2-3x faster, same error detection)
- Truncate verbose output: `2>&1 | tail -20`
- Wrap tests with timeout: `timeout 120 uv run pytest`

---

## Decision Trees

### Read vs Edit

```
Familiar file you edited this session?
  Yes -> Edit directly (verify after)
  No  -> Read it this session?
    Yes -> Edit
    No  -> Read first (79% of quick fixes start with reading)
```

### Subagents vs Direct Work

```
Self-contained with a clear deliverable?
  Yes -> Produces verbose output (tests, logs, research)?
    Yes -> Subagent (keeps context clean)
    No  -> Need frequent back-and-forth?
      Yes -> Direct
      No  -> Subagent
  No -> Direct (iterative refinement needs shared context)
```

### Refactoring Approach

```
Can changes be made incrementally?
  Yes -> Move first, THEN consolidate (separate commits)
        New code alongside old, remove old only after tests pass
  No  -> Analysis phase first (parallel review agents)
        Gap analysis: old vs new function-by-function
        Implement gaps as focused tasks
```

### Bug Fix vs Feature vs Refactor

| Type         | Cadence                                                                  | Typical Cycles |
| ------------ | ------------------------------------------------------------------------ | -------------- |
| **Bug fix**  | Grep error -> Read 2-5 files -> Edit 1-3 files -> Test -> Commit         | 1-2            |
| **Feature**  | Plan -> Models -> API -> Frontend -> Test -> Commit                      | 5-15           |
| **Refactor** | Audit -> Gap analysis -> Incremental migration -> Verify parity          | 10-30+         |
| **Upgrade**  | Research changelog -> Identify breaking changes -> Bump -> Fix consumers | Variable       |

---

## Error Recovery

**65% of debugging sessions resolve in 1-2 iterations.** The remaining 35% risk spiraling into 6+ iterations.

### Quick Resolution (Do This)

1. Read relevant code first (79% success correlation)
2. Form explicit hypothesis: "The issue is X because Y"
3. Make ONE targeted fix
4. Verify the fix worked

### Spiral Prevention (Avoid This)

1. **Separate error domains** — fix ALL type errors first, THEN test failures. Never interleave.
2. **3-strike rule** — after 3 failed attempts on same error: change approach entirely, or escalate.
3. **Cascade depth > 3** — pause, enumerate ALL remaining issues, fix in dependency order.
4. **Context rot** — after ~15-20 iterations, `/clear` and start fresh. A clean session with a better prompt beats accumulated corrections every time.

### The Two-Correction Rule

If you've corrected the same issue twice, `/clear` and restart. Accumulated context noise defeats accuracy.

---

## Commit Cadence

Commit as you go. Each commit captures one logical chunk that has been built, verified, and tested. Many small commits per session is the norm — never accumulate hours of unrelated work into a single mega-commit. The COMMIT step in the macro-sequence loops back to IMPLEMENT for the next chunk; that loop is the rhythm.

### When to commit

| Trigger                                          | Action          |
| ------------------------------------------------ | --------------- |
| Logical chunk done and verification passes       | Commit now      |
| Move/rename complete (before behavioral changes) | Commit (move)   |
| Behavioral change works (after the move commit)  | Commit (change) |
| Refactor extracted, callers still pass           | Commit          |
| Test added that exercises a fixed bug            | Commit          |
| About to switch to a different concern           | Commit current  |
| Verification fails mid-chunk                     | Don't commit    |
| Speculative or exploratory edits                 | Don't commit    |

Rule of thumb: if a reviewer would want to read it as a separate diff, it's a separate commit.

### Local style first

Before the first commit in any repo, detect the local style. Repos have personalities — your commits should match.

```bash
git log -10 --oneline
```

Observe the actual patterns and mirror them:

| Pattern              | Example                          | Mirror               |
| -------------------- | -------------------------------- | -------------------- |
| Conventional Commits | `feat(api): add token refresh`   | `type(scope): msg`   |
| Gitmoji              | `✨ Add token refresh`           | Leading emoji + msg  |
| Ticket prefix        | `[ENG-1234] Add token refresh`   | Mirror bracket style |
| Module prefix        | `auth: add token refresh`        | Mirror separator     |
| Plain                | `Add token refresh`              | No prefix, plain     |

**Mirror format, NOT quality.** If existing commits are terse one-liners, you still write a descriptive subject and body — you're elevating the standard, not lowering yours to match. If no clear pattern exists, default to Conventional Commits.

### Conventional Commits (default)

Format: `type(scope): subject`. Scope is optional but encouraged when the change is localized.

| Type       | When                                     |
| ---------- | ---------------------------------------- |
| `feat`     | New user-facing capability               |
| `fix`      | Bug fix                                  |
| `refactor` | Restructure without behavior change      |
| `perf`     | Performance improvement                  |
| `test`     | Add/update tests only                    |
| `docs`     | Documentation only                       |
| `style`    | Formatting, whitespace (no logic change) |
| `chore`    | Tooling, deps, housekeeping              |
| `build`    | Build system, packaging                  |
| `ci`       | CI/CD configuration                      |

### Message anatomy

**Subject line:**

| Rule                     | Why                                                        |
| ------------------------ | ---------------------------------------------------------- |
| Imperative mood          | "Add token refresh", not "Added" or "Adds"                 |
| ≤72 characters           | Renders cleanly in `git log --oneline` and PR lists        |
| No trailing period       | It's a title, not a sentence                               |
| No emojis (Conventional) | Breaks parser tooling; emoji belongs in body if anywhere   |
| Skip filenames           | The diff already shows them — describe behavior, not paths |
| Be specific              | "Fix null deref in token refresh" beats "Fix bug"          |

**Body (always include one):**

- Explain **why**, not what — the diff shows what
- Wrap at ~72 chars, separate from subject with one blank line
- Two sentences is often enough; a few short paragraphs when warranted
- Mention load-bearing context: hidden constraints, related issues, what a future bisect would want to know
- **No uncertain language.** Banish "likely", "probably", "might", "seems", "appears to", "presumably". You wrote the code — state facts. If you don't know what a change does, read more before committing.

### Co-Authored-By

When an agent does meaningful work in a commit, add a `Co-Authored-By:` trailer with a descriptive identity that names the model. This makes attribution legible across multi-agent sessions and `git log`.

```
Co-Authored-By: Nova (Claude Opus 4.7) <noreply@anthropic.com>
```

Use a name that signals which model or persona contributed — not just "Claude".

### The HEREDOC pattern

Always pass commit messages via HEREDOC to preserve formatting and avoid shell-quoting bugs:

```bash
git commit -m "$(cat <<'EOF'
fix(auth): guard against null session in token refresh

Refresh requests racing with logout were dereferencing a freed session
pointer, surfacing as a 500 with no log trail. Added an early return
that emits a single warn log so the failure mode is visible without
spamming on every refresh attempt.

Co-Authored-By: Nova (Claude Opus 4.7) <noreply@anthropic.com>
EOF
)"
```

### Examples

| Bad                        | Why bad                 | Good                                              |
| -------------------------- | ----------------------- | ------------------------------------------------- |
| `fix: bug`                 | Vague                   | `fix(api): resolve null pointer in token refresh` |
| `update stuff`             | No type, no specificity | `chore(deps): bump axios to 1.7.4`                |
| `WIP`                      | Not a commit message    | `feat(auth): scaffold magic-link sign-in flow`    |
| `Added new file for users` | Filename + past tense   | `feat(users): add bulk import endpoint`           |
| `feat: it works now`       | Doesn't say what works  | `feat(search): add fuzzy matching to user lookup` |

### Multi-agent hygiene

Other agents may be working in parallel. Stage with care:

```bash
git status                # See the full picture first
git diff --staged         # Review what you're about to commit
git add <specific-files>  # Only files you personally touched
git commit -m "..."       # HEREDOC for the message
```

| Rule                                            | Why                                        |
| ----------------------------------------------- | ------------------------------------------ |
| Never `git add -A` or `git add .`               | Picks up other agents' WIP and secrets     |
| Never `git restore` files you didn't modify     | May discard another agent's in-flight work |
| Never `git push` unless explicitly asked        | Push is the human's call                   |
| Skip planning docs, scratch files, `.local.md`  | These don't belong in the repo             |
| Verify before commit, not after                 | A red commit poisons bisect history        |

---

## Anti-Patterns

| Anti-Pattern                                     | Fix                                             |
| ------------------------------------------------ | ----------------------------------------------- |
| 20+ edits without verification                   | Verify every 2-3 edits                          |
| Fix without verifying the fix (73% of fixes!)    | One fix, one verify, repeat                     |
| `fix -> fix -> fix` chains without checking      | Always verify between fixes                     |
| Editing without reading first                    | Read the file immediately before editing        |
| Writing tests from memory                        | Read actual function signatures first           |
| Changing shared types without grepping consumers | `Grep` all usages before modifying shared types |
| Mixing move and change in one commit             | Move first commit, change second commit         |
| Debugging spiral past 3 attempts                 | Change approach or escalate                     |
| Premature optimization                           | Correctness first, optimize after tests pass    |
| One mega-commit at end of session                | Commit each logical chunk as it lands           |
| Bare titles like `fix: bug` or `update stuff`    | Specific subject + body explaining why          |
| Skipping the body to "save time"                 | Always include a body — even two sentences      |
| Filenames or paths in the subject line           | Describe the behavior, not the file             |
| Uncertain language ("might fix", "should work")  | State facts; read more code if you don't know   |
| `git add -A` / `git add .`                       | Stage specific files only                       |
| `git push` without explicit request              | Push is the human's call; never autonomous      |
| Silently picking one interpretation              | Surface options; ask before committing to one   |
| "Improving" code adjacent to your change         | Stay surgical; touch only what's asked          |
| Touching comments you don't understand           | Leave them; not your scope                      |
| Bloated abstraction for single-use code          | Write the function; abstract when reused        |
| Vague "make it work" goal                        | Define a verifiable check first                 |

---

## Cross-Model Review

For high-stakes changes, use `/hyperskills:codex-review` after implementation. A fresh model context eliminates implementation bias and catches real bugs: migration idempotency, PII in debug logging, empty array edge cases, missing batch limits.

---

## References

For quantitative benchmarks and implementation archetype templates, consult `references/benchmarks.md`.

---

## What This Skill is NOT

- **Not a gate.** Don't follow all five phases for a typo fix. Scale selection exists for a reason.
- **Not a replacement for reading code.** This skill tells you HOW to implement, not WHAT to implement.
- **Not a planning tool.** Use `/hyperskills:plan` for task decomposition.
- **Not an excuse to skip tests.** "Verify" means running actual checks, not eyeballing the diff.
