# Dispatch Brief Templates

Copyable full-length templates for the brief anatomy described in SKILL.md. Every shape here is distilled from briefs that ran in production swarms; adapt slots to the task, drop slots that don't apply.

## Pi Dispatch Task Shape

```json
{
  "mode": "parallel",
  "tasks": [
    {
      "agent": "worker",
      "task": "Implement <task> in <path>. Run <verification>. Return summary, files changed, and patch notes.",
      "tools": ["read", "grep", "find", "ls", "bash", "edit", "write"]
    }
  ]
}
```

## Research Brief

```markdown
Research [TECHNOLOGY] for [PROJECT]'s [USE CASE].

Create a comprehensive research doc at [OUTPUT_PATH]/[filename].md covering:

1. Latest [TECH] version and features (search "[TECH] 2026" or "[TECH] latest")
2. [Specific feature relevant to project]
3. [Another relevant feature]
4. [Integration patterns with other stack components]
5. [Performance characteristics]
6. [Known gotchas and limitations]
7. [Best practices for production use]
8. [Code examples for key patterns]

Current month is [MONTH YEAR] — do NOT rely on memory for version or
ecosystem claims. Use WebSearch and WebFetch to get current docs.
Include code examples where possible.
```

## Sweep Brief (same fix across a partition)

```markdown
Fix all [TOOL] issues in the [MODULE_NAME] directory ([PATH]).

Current issues ([COUNT] total):

- [RULE_CODE]: [description] ([count]) -- [domain-specific fix guidance]
- [RULE_CODE]: [description] ([count]) -- [domain-specific fix guidance]

Run `[TOOL_COMMAND] [PATH]` to see exact issues.

IMPORTANT for [DOMAIN] code:
[Domain-specific guidance, e.g., "GTK imports need GI.require_version()
before gi.repository imports"]

After fixing, run `[TOOL_COMMAND] [PATH]` to verify zero issues remain.
```

## Worker Brief (build/fix)

```markdown
**Task: [DESCRIPTIVE TITLE]** (task_[ID])

Work in /absolute/path/to/[directory]

## The ask (verbatim)

> [The user's exact words. Do not paraphrase. If your read of this brief
> conflicts with the ask, say so in your report.]

## Scope fence

Own these files only:

- [path/one]
- [path/two]

You are not alone in the codebase. Do not revert or overwrite edits
outside your assigned files.

[Same-worktree fleets only] Contracts you may rely on: another agent is
adding [interface, e.g. `GET /api/ready?probe=k8s`] and [env var / schema].

## Context

[What exists, what to read first, what infrastructure is available.]
[e.g., "Redis is available at `app.state.redis`", "Follow pattern from `src/auth/`"]

Receipts already run (attack residual risk, don't repeat these):

- `[command]` -> [result/count]

Settled decisions (do not re-litigate):

- [decision + one-line rationale]

Known traps:

- [trap] — [its failure mechanism, e.g. "calls `runWithOperationContext({})`
  which throws without an ALS store"]

Standing corrections from this session (verbatim):

- "[user veto, quoted]"

## Your job

1. [Specific change with file paths]
2. [Test requirements]
3. [Integration requirements]

You can [concrete capability grants: "restart the dev server", "read the
db pod directly"].

## Done means

- Focused tests pass: `[command]`
- `[lint/typecheck command]` passes if your edits touch [language]
- Final response lists changed files and exact commands/results
- A required "Deviations from brief" section: every departure, each with
  its justification (empty section if none)
- If blocked: stop, report the blocker with evidence, do not improvise
  outside the fence
- Do not commit. The coordinator will review and commit.
  [Or: commit only files YOU created, message "feat([scope]): [summary]"]
```

## Read-Only Verifier Brief

```markdown
Independent verification of [CHANGE] at commit [SHA].

Do NOT edit, checkout, switch branches, or mutate any state. Read only.
Inspect via `git show [SHA]:[path]` and `git diff [base]..[SHA]` — never
touch the working tree.

## The original ask (verbatim)

> [user's exact words — verify against intent, not the implementer's summary]

## CURRENT TRUTH ([date] — flag anything that contradicts this)

- [pinned fact, e.g. "1.0 shipped; any framing of shipped features as
  'planned / coming soon' is STALE and a high-severity finding"]

## Open findings to confirm or refute

- [finding] — [status claimed by implementer]

## Priority lenses

[Named failure categories that matter most, including what tests can't see:
mixed-version rollout windows, config inheritance scope, guards one level
below the threat model, rollback paths, what the fix removed.]

## Evidence rules

- Receipt = short quote (<=25 words) + file:line or timestamp
- Label inferences "(inferred)"; label unverified claims "[unverified]"
- Skip nits; cap findings at [N]

## Verdict

PASS or FAIL. On FAIL: numbered findings with severity and reproduction.
Scrutinize your own exculpatory claims — reproduce any "pre-existing
failure" on the base before attributing it there.
```

## Warm Re-Verify Delta Brief

Send to the SAME verifier (resume/send_input) so it confirms closure instead of discovering novelty:

```markdown
I fixed your blocking finding. Please re-verify the current working tree
at [FIX SHA], focusing on the exact issue you raised.

Your finding (verbatim): "[quoted finding]"

Fix claim: [file/symbol-level claim, e.g. "validation now requires
`cap.is_finite() && cap > 0.0`"]

Prove these cases specifically: [enumerated inputs/paths, e.g. "default,
positive override, 0, negative, non-numeric, inf, NaN"]

Do not edit files. Also check whether the fix introduced second-order
regressions in [adjacent surface].
```

Use a fresh verifier instead for final certification — a prior PASS is never inherited across commits.

## Verifier Interrupt

When you need a verdict before the verifier finishes:

```markdown
Quick status please. If you are still running commands, stop at the
current safe point and return PASS/FAIL based on the review so far.
Do not edit files. List any side effects you have already caused.
```

Mid-flight scope amendments go the same way — inject the new scope as a message rather than kill-and-respawn, so accumulated context survives.

## Watcher Spec

Declare all four elements at arm time; a watcher missing any of them is a stuck loop waiting to happen:

```markdown
Watch: [what — command/file/endpoint and poll interval]
Exit condition: [named, checkable — "checks settle to SUCCESS or FAILURE",
  not "looks done"; beware conditions no state can satisfy]
On fire: [remediation rung — the ONE action taken, then re-observe]
Ceiling: [max iterations or wall time, then escalate with evidence]
Stale-fire: [if the world changed since arming, no-op and report]
```

Hygiene: smoke-test the watcher against a known state before trusting hours of its output; kill only your own PIDs; tear watchers down as the first act of any pivot; narrate on state change only; surface user input between polls.
