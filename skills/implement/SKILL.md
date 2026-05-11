---
name: implement
description: Use this skill when writing code, building features, fixing bugs, refactoring, or any multi-step implementation work. Activates on mentions of implement, build this, code this, start coding, fix this bug, refactor, make changes, develop this feature, implementation plan, coding task, write the code, or start building.
---

# Implementation

Verification-driven coding with tight feedback loops. Distilled from 21,321 tracked operations across 64+ projects, 612 debugging sessions, and 2,476 conversation histories. These are the patterns that consistently ship working code.

**Core insight:** Verify in tight loops, roughly every 2-3 edits. 73% of fixes go unverified across the dataset, which is the single biggest quality gap. Sessions that maintain a tight verify cadence avoid the debugging spirals that the rest of this skill is designed to prevent.

**How to read this skill:** the loop and the heuristics below are calibrated for non-trivial implementation work. Trivial fixes (config, typo, single-line) shouldn't drag through five phases. Use judgment, scale planning to scope, and skip what doesn't apply. The Code Discipline section is principles that bias toward caution; for one-line changes, just make the change.

## The Loop

Most implementation work flows through the same shape, regardless of scale:

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

**ORIENT.** Read existing code before touching anything. `Grep → Read → Read` is the dominant opening across the dataset. Sessions that read 10+ files before the first edit require fewer fix iterations downstream. Blind changes are the most expensive way to start.

**PLAN.** Scale-dependent (see below). Trivial fixes don't need a plan; features benefit from a task list; epics earn a research swarm. The decision is "what's proportional," not "always plan."

**IMPLEMENT.** Work in batches of roughly 2-3 edits, then verify. Follow the dependency chain. Edit existing files 9:1 over creating new ones; that's the observed ratio in successful sessions. Fix errors as they surface; accumulating them creates cascade-debugging.

**VERIFY.** Typecheck is the primary gate, fast and cheap; run it between batches. Tests fit naturally after feature-complete. Full suite before commit.

**COMMIT.** Atomic chunks, committed as you go. Verify, stage specific files, commit, loop back to the next chunk. Many small commits per session is the pattern that consistently outperforms one mega-commit at the end. See **Commit Cadence** below for message anatomy.

---

## Code Discipline

Principles that shape how you move through the loop, not steps to execute. Adapted from Karpathy's [observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls: models "make wrong assumptions on your behalf and just run along with them without checking ... really like to overcomplicate code and APIs, bloat abstractions ... implement a bloated construction over 1000 lines when 100 would do."

These principles bias toward caution because that's where models drift. For trivial fixes, the calculus inverts; apply judgment, not the full discipline.

### Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

| Situation                               | Action                            |
| --------------------------------------- | --------------------------------- |
| Multiple interpretations of the request | Present them; don't pick silently |
| A simpler approach is plausible         | Say so; push back when warranted  |
| Something is unclear                    | Stop; name what's confusing; ask  |
| You hold a load-bearing assumption      | State it explicitly               |
| Inconsistency between request and code  | Surface it before proceeding      |

ORIENT (read the code) is the prerequisite. This principle is what to do with what you find: name the gaps, don't paper over them.

### Simplicity first

Minimum code that solves the problem. Nothing speculative.

| Don't                                          | Do                                           |
| ---------------------------------------------- | -------------------------------------------- |
| Add features beyond what was asked             | Solve exactly the stated problem             |
| Build abstractions for single-use code         | Inline first; abstract when reused           |
| Add "flexibility" or configurability not asked | Hardcode now; parameterize on demand         |
| Handle errors for impossible scenarios         | Trust internal invariants; validate at edges |
| Write 200 lines when 50 would do               | Rewrite tighter                              |

The test: would a senior engineer call this overcomplicated? If yes, simplify.

### Surgical changes

Touch only what you must. Clean up only your own mess.

| Rule                                                   | Why                                             |
| ------------------------------------------------------ | ----------------------------------------------- |
| Don't "improve" adjacent code, comments, or formatting | Pollutes the diff; outside your scope           |
| Don't refactor code that isn't broken                  | Scope creep expands blast radius                |
| Match existing style even if you'd do it differently   | Local consistency beats your preferences        |
| Notice unrelated dead code → mention, don't delete     | Other branches/agents may rely on it            |
| Remove imports/vars/funcs _your_ changes orphaned      | Clean up after yourself                         |
| Leave pre-existing dead code alone                     | Outside your remit unless explicitly asked      |
| Don't touch comments you don't understand              | Karpathy: "side effects ... orthogonal to task" |

The test: every changed line should trace directly to the user's request.

### Goal-driven execution

Define verifiable success. Loop until it passes.

| Vague task       | Verifiable goal                                     |
| ---------------- | --------------------------------------------------- |
| "Add validation" | Write tests for invalid inputs, then make them pass |
| "Fix the bug"    | Write a test that reproduces it, then make it pass  |
| "Refactor X"     | Ensure the same tests pass before and after         |
| "Make it work"   | Reject, name the actual signal that proves it works |

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

The single most impactful practice in the dataset. Tight loops here make the rest of the skill mostly unnecessary; loose loops make every other guideline harder to follow.

| Gate                   | Typically                  | Speed               |
| ---------------------- | -------------------------- | ------------------- |
| **Typecheck**          | Between edit batches       | Fast (primary gate) |
| **Lint (autofix)**     | After implementation batch | Fast                |
| **Tests (specific)**   | After feature complete     | Medium              |
| **Tests (full suite)** | Before commit              | Slow                |
| **Build**              | Before PR/deploy only      | Slowest             |

### The edit-verify-fix cycle

The pattern that consistently produces clean sessions: **~3 changes → verify → 1 fix**. Sweet spot, not a hard ratio. Sometimes one edit warrants its own verify, sometimes five edits group cleanly.

The pattern that produces debugging spirals: **2 changes → typecheck → 15 cascading fixes**. Prevent type cascades by grepping consumers before modifying shared types; once the cascade starts, separate fix domains (see Error Recovery).

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

**65% of debugging sessions resolve in 1-2 iterations.** The remaining 35% risk spiraling into 6+. The patterns below are calibrated to keep you in the first bucket.

### Quick resolution

- Read the relevant code first (79% success correlation in the dataset)
- Form an explicit hypothesis: "the issue is X because Y"
- Make one targeted fix
- Verify the fix actually worked before moving on

### Spiral prevention

- **Separate error domains.** Fix all type errors before chasing test failures; interleaving the two is how cascades compound.
- **3-strike heuristic.** Three failed attempts on the same error is the signal to change approach entirely or escalate, not to try variation #4.
- **Cascade depth > 3.** Pause, enumerate all remaining issues, then fix in dependency order rather than reactive whack-a-mole.
- **Context rot.** After ~15-20 iterations, `/clear` and start fresh. A clean session with a better prompt usually outperforms accumulated corrections.

### Two-correction rule

Correcting the same issue twice is the signal to `/clear` and restart. Context noise compounds faster than fixes resolve it.

---

## Commit Cadence

Commit each logical chunk as it lands and verifies. Many small commits per session is the norm, never accumulate hours of unrelated work into one mega-commit. The COMMIT step loops back to IMPLEMENT for the next chunk.

### When to commit

| Trigger                                         | Action          |
| ----------------------------------------------- | --------------- |
| Logical chunk done, verification passes         | Commit          |
| Move/rename complete, before behavioral changes | Commit (move)   |
| Behavioral change works after the move commit   | Commit (change) |
| Refactor extracted, callers still pass          | Commit          |
| About to switch to a different concern          | Commit current  |
| Verification fails or edit is speculative       | Don't commit    |

If a reviewer would want it as a separate diff, it's a separate commit.

### Mirror local style

Before the first commit in any repo, run `git log -10 --oneline` and mirror the pattern. **Mirror format, not quality**, terse history doesn't lower your bar. Default to Conventional Commits when no pattern exists.

| Pattern              | Example                        |
| -------------------- | ------------------------------ |
| Conventional Commits | `feat(api): add token refresh` |
| Gitmoji              | `✨ Add token refresh`         |
| Ticket prefix        | `[ENG-1234] Add token refresh` |
| Module prefix        | `auth: add token refresh`      |
| Plain                | `Add token refresh`            |

Conventional Commit types: `feat` (capability), `fix` (bug), `refactor` (no behavior change), `perf`, `test`, `docs`, `style` (formatting only), `chore` (tooling/deps), `build`, `ci`. Scope is optional but encouraged when the change is localized.

### Message anatomy

**Subject:** imperative mood, ≤76 chars, no trailing period, no filenames. "Fix null deref in token refresh" beats "Fix bug." For Conventional Commits, no emoji in the subject, it breaks parsers.

**Body** (always include one): wrap at 76 chars, separated from subject by a blank line. Explain _why_, the diff shows _what_. State facts: banish "likely", "probably", "might", "seems", "appears to". If you don't know what a change does, read more before committing. Two sentences usually suffices; mention load-bearing context a future bisect would want.

### HEREDOC + Co-Author

Always pass messages via HEREDOC to preserve formatting. Add a `Co-Authored-By` trailer that names the model, "Claude" alone doesn't disambiguate across multi-agent sessions.

```bash
git commit -m "$(cat <<'EOF'
fix(auth): guard against null session in token refresh

Refresh racing with logout was dereferencing a freed session, surfacing
as a 500 with no log trail. Early return plus a single warn log makes
the failure mode visible without spamming on every refresh.

Co-Authored-By: Nova (Claude Opus 4.7) <noreply@anthropic.com>
EOF
)"
```

### Examples

| Bad                        | Good                                              |
| -------------------------- | ------------------------------------------------- |
| `fix: bug`                 | `fix(api): resolve null deref in token refresh`   |
| `update stuff`             | `chore(deps): bump axios to 1.7.4`                |
| `WIP`                      | `feat(auth): scaffold magic-link sign-in flow`    |
| `Added new file for users` | `feat(users): add bulk import endpoint`           |
| `feat: it works now`       | `feat(search): add fuzzy matching to user lookup` |

### Multi-agent staging

Other agents may be working in parallel:

```bash
git status                # See the full picture first
git diff --staged         # Review what you're about to commit
git add <specific-files>  # Only files you personally touched
```

Never `git add -A` or `git add .` (catches other agents' WIP and secrets). Never `git restore` files you didn't modify. Never `git push` without explicit request, push is the human's call. Skip planning docs, scratch files, and `.local.md` from the repo.

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
| Skipping the body to "save time"                 | Always include a body, even two sentences       |
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

For high-stakes changes, run `/hyperskills:cross-model-review` after implementation. A different reviewer model has different blind spots than the author and catches real bugs: migration idempotency, PII in debug logging, empty-array edge cases, missing batch limits. Use `/hyperskills:codex-review` only when you specifically want the Claude → Codex direction with `codex review` subcommand semantics.

---

## References

For quantitative benchmarks and implementation archetype templates, consult `references/benchmarks.md`.

---

## What This Skill is NOT

- **Not a gate.** Don't follow all five phases for a typo fix. Scale selection exists for a reason.
- **Not a replacement for reading code.** This skill tells you HOW to implement, not WHAT to implement.
- **Not a planning tool.** Use `/hyperskills:plan` for task decomposition.
- **Not an excuse to skip tests.** "Verify" means running actual checks, not eyeballing the diff.
