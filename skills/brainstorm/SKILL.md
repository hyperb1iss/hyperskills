---
name: brainstorm
description: Use this skill before any creative work - new features, architecture decisions, project inception, or design exploration. Activates on mentions of brainstorm, ideate, design session, explore options, what should we build, how should we approach, let's think about, new feature, new project, architecture decision, or design exploration.
---

# Collaborative Brainstorming

Structured ideation using the Double Diamond model, grounded in persistent memory. Mined from 100+ real brainstorming sessions across production projects.

**Core insight:** AI excels at divergent phases (volume, cross-domain connections). Humans excel at convergent phases (judgment, selection). Separating the two, and using Sibyl to avoid re-exploring solved problems, is the shape that consistently produces useful brainstorms.

**How to read this skill:** the phases below describe the natural rhythm of a good brainstorm, not a procedure to march through. Skip phases that don't apply. Revisit earlier phases when new info changes the frame. Use judgment about when to compress, when to skip to action, and when divergent exploration is actually warranted.

## Reading the Brief

The brief tells you how wide to go. Read its signals before choosing a mode.

| Signal in the brief                                                                          | Mode it selects                                                     |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Stakes + uncertainty + an open question ("i'm terrified to announce...", "let's get weird!") | Go wide — exploration is the deliverable, not a plan                |
| Crisp problem, known options                                                                 | Quick mode; ceremony scales inversely with brief clarity            |
| Risk or hardening framing ("get evil", "get gnarly")                                         | Adversarial depth; generic-but-safe findings read as under-delivery |
| "Build it" / momentum words                                                                  | Not a brainstorm — exit to implementation                           |

---

## Phase 1: GROUND (Memory-First)

Lean on existing knowledge before generating new ideas. The cost of a Sibyl search is low; the cost of re-discovering a pattern we already learned is high.

### Common moves

- **Search Sibyl** for related patterns, decisions, and known constraints. Useful queries: `sibyl search "<topic keywords>"`, `sibyl search "<related architecture>"`, plus a quick scan of existing tasks/epics on the topic.
- **Surface constraints** that aren't up for debate: tech stack locks, budget, timeline, conventions you'd be foolish to violate.
- **Ask for operator-known facts early**: accounts that don't exist, past-incident gotchas, environments that must not break. One line from the user prunes more of the option tree than any research wave, and each fact absorbed becomes a hard constraint instantly.
- **Present prior art** before ideating: "Sibyl has 3 relevant entries: [pattern X], [decision Z], [gotcha W]. Want to factor these in?"

If Sibyl already has a directly applicable answer, surface it first. The brainstorm is then about whether to apply it as-is, adapt it, or genuinely diverge, not re-deriving it from scratch.

---

## Phase 2: DIVERGE: Explore the Problem Space

**Goal:** Generate breadth. Understand what we're actually solving before reaching for solutions.

### Common moves

- **Lean toward one load-bearing question at a time.** Stacking five questions buries the signal; building understanding incrementally surfaces what actually matters. The exception is when the user fires multiple parallel asks; then answer them in parallel rather than artificially serializing.
- **Reframe the problem** from multiple angles: user view ("as a [user], I need..."), system view ("the system currently..."), constraint view ("we're bounded by...").
- **Spawn parallel Explore agents** when the problem space is genuinely large: research how similar projects solve this, map the existing codebase surface, search for SOTA approaches.
- **Run the kill-check.** Identify the one load-bearing assumption that decides whether the requested approach can work at all, and verify it with a decisive check before building options on it. The user's framing is a hypothesis too — confirm, refute, or split it with receipts, then keep solving the underlying problem either way.
- **Translate felt-experience asks into named criteria.** "Buttery smooth", "gorgeous", "tip top" are valid problem statements; convert them into checkable acceptance criteria (what's observable, in whose environment, verified how) before exploring solutions, and draft beloved existing artifacts as fixtures.

The discipline here is staying in problem space when the pull toward solutions is strong. If the problem is already crisp, skip ahead. This phase exists to prevent solving the wrong thing, not to perform exploration.

### Anti-patterns

- Jumping to solutions before the problem frame is clear
- Stacking questions when the answers depend on each other
- Dismissing vague input ("make it faster" is a valid starting point — translate it into named criteria instead of rejecting it)

---

## Phase 3: CONVERGE: Define the Core Problem

**Goal:** Narrow from exploration to a crisp problem statement before exploring solutions for it.

Synthesize the exploration into a 1-2 sentence problem statement, confirm it lands ("is this what we're solving?"), and call out scope boundaries. The output usually looks like:

> **Problem:** [crisp statement]
> **In scope:** [what we'll address]
> **Out of scope:** [what we won't]
> **Key constraint:** [the most important limiting factor]

If the problem was already crisp coming in, this phase is a 30-second confirmation, not a deliverable.

---

## Phase 4: DIVERGE: Explore Solutions

**Goal:** Generate multiple viable approaches with explicit tradeoffs.

### Common moves

- **Present 2-3 approaches** with tradeoffs side-by-side. Two is the floor (otherwise it's a recommendation, not a brainstorm); past four, decision fatigue kicks in.

  | Approach  | Pros | Cons | Complexity   | Risk |
  | --------- | ---- | ---- | ------------ | ---- |
  | A: [name] | ...  | ...  | Low/Med/High | ...  |
  | B: [name] | ...  | ...  | Low/Med/High | ...  |
  | C: [name] | ...  | ...  | Low/Med/High | ...  |

- **Include one unconventional option** when the obvious paths look similar. Fixation on the first decent idea is the failure mode this phase is designed to prevent.
- **Carry one subtractive option.** The judo move at the approach altitude: alongside the options that build something, include the one that builds less or nothing. Reuse an existing system, solve it with config, or delete the need entirely. The cheapest complexity is what you never write, and it rarely makes the list unless you force it on.
- **Run the wheels gate.** Name the prior art you'd borrow versus the genuinely novel part you'd build — steal patterns ruthlessly — and give the build side a maintenance ceiling with a named kill condition ("if we can't prove value in a few focused files plus tests, we stop").
- **Ground in existing patterns:** "this follows what we did in [project X]" or "this diverges from our convention because [reason]".
- **Name the verification method** for each approach so the choice connects to a concrete check (test, benchmark, visual confirmation).

### Exploration vs exploitation

Don't fixate on the first decent idea:

- If all approaches look similar → push for a wild card option
- If approaches are wildly different → that's healthy divergence
- If the user gravitates early → present the contrarian case before converging

### Two dials, corrected independently

Ambition of the destination and complexity of the mechanism are separate dials. Push the destination ("is this ambitious enough to matter?") while keeping the mechanism boring. The bar is usefulness, not smallness — a minimal option that only proves plumbing is as wrong as a gold-plated one. Ask the lifespan question: something deleted in two weeks earns deliberately boring architecture; something that will live earns the timeless treatment.

### When the design gets attacked

Concede without defending sunk work, then diagnose the pressure that produced the bad shape ("polling showed up because the gateway needed X — but convenience is not architecture"). Match the user's simplification energy, and fence the one load-bearing invariant that must survive it. A constraint absorbed this way usually makes the design better; say so when it does. On an overcorrection, offer the third option that satisfies both constraints.

### Anti-patterns

- Seven "maybe" options instead of 2-3 real choices with tradeoffs
- Options presented without explicit costs (every option has one)
- Options that quietly violate constraints surfaced in Phase 1
- Treating the dials as coupled: shrinking the destination when asked to simplify the mechanism, or gold-plating the mechanism when asked for more ambition
- Every option builds something; none asks what we could remove or reuse instead

---

## Phase 5: CONVERGE: Decide and Record

**Goal:** Lock in the approach, record the decision, exit to action.

Present your recommendation with conviction. Route to the user only the forks they actually own — product policy, risk appetite, taste — and decide the rest with your own judgment, saying so. End in one precise consent question, not a menu of everything; that preserves genuine choice without mush. When the user's answer is a cleaner model than your question, adopt it out loud. Then record the decision in Sibyl so future sessions don't re-litigate it:

```
sibyl add "Brainstorm: [topic]" "Chose [approach] because [reason]. Rejected [other approaches] due to [tradeoffs]. Key constraint: [X]."
```

Record deliberately-open decisions as pinned invariants too ("the result is not necessarily one PR — agent's choice"); open-endedness is exactly what future sessions' priors will erase. And keep requirement separate from preference: a casual "use X" is a preference until the user makes it a constraint.

Hand off to whatever's next:

| Next Step                  | When                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `/hyperskills:plan`        | Complex feature needing decomposition                                                                               |
| `/hyperskills:research`    | Need deeper investigation first                                                                                     |
| `/hyperskills:orchestrate` | Ready to dispatch agents                                                                                            |
| Direct implementation      | Simple enough to just build                                                                                         |
| Write a spec               | Needs formal documentation — then cross-model review, iterating to convergence ("until we love it"), not to a count |

### Output

> **Decision:** [what we're doing]
> **Approach:** [which option, brief description]
> **Why:** [1-2 sentences on the reasoning]
> **Next:** [the immediate next action]

---

## Quick Mode

For small decisions that don't need the full diamond: search Sibyl, present two options with tradeoffs, decide, record. Skip problem exploration entirely when the problem is already well-understood and the user just needs help choosing between known options. Most "brainstorms" are actually this.

---

## Multi-Model Brainstorming

Two shapes proven in the wild (as of Jul 2026):

- **Consult mode.** Write the design to a file and confer with the other model on the undecided question. Advisory, not a verdict: no iteration cap, but give the consult a deadline and a degraded fallback so it never blocks the decision.
- **Convergence as signal.** When independent starts — parallel research agents, another model from a blank page, prior art — agree on the spiky parts, that agreement is the confidence signal to proceed. Where they diverge is where the real decision lives.

A different model breaks self-review bias only; it shares your training staleness. Version, SOTA, and ecosystem claims need live primary sources (registry, release page, official docs) no matter how many models agree.

Adversarial advocate/critic splits are available when options have entrenched camps, but the two shapes above are the ones that earn their cost.

---

## Anti-Patterns

| Anti-Pattern                              | Fix                                              |
| ----------------------------------------- | ------------------------------------------------ |
| Jumping to solutions before defining pain | Spend one pass on the problem frame first        |
| Asking a stack of questions at once       | Ask one load-bearing question, then adapt        |
| Presenting seven "maybe" options          | Offer 2-3 real choices with tradeoffs            |
| Ignoring prior decisions in Sibyl         | Search memory first and surface relevant context |
| Brainstorming when the user said build it | Switch to implementation and keep momentum       |

---

## What This Skill is NOT

- **Not a gate.** You don't need permission to skip phases. If the user says "just build it," build it.
- **Not a waterfall.** Phases can revisit. New information in Phase 4 can send you back to Phase 2.
- **Not a document generator.** The output is a decision, not a design doc (unless the user wants one).
- **Not required for everything.** Bug fixes, typo corrections, and clear-spec features don't need brainstorming.

## YAGNI Check

Before concluding, ask both poles: **"Is there anything in this plan we don't actually need yet?"** Strip it. Then the mirror: **"Is the destination still ambitious enough to matter?"** The minimum you build must prove usefulness, not just that the pipes connect.
