---
name: plan
description: Use this skill when decomposing complex work into structured tasks before implementation. Activates on mentions of write a plan, create a plan, break this down, task decomposition, implementation plan, what are the steps, plan the work, spec this out, or decompose this feature.
---

# Structured Planning

Verification-driven task decomposition with Sibyl-native tracking. Mined from 200+ real planning sessions: the plans that actually survived contact with code.

**Core insight:** Plans fail when steps can't be verified. Decomposition that lands in concrete checks survives contact with reality; abstract bullets don't. And a plan is a durable artifact consumed by autonomous runs and other agents, not chat exhaust — tracking in Sibyl and the repo lets it outlive the context window that produced it.

**How to read this skill:** the phases below describe the rhythm of a useful planning pass, not a procedure to march through. Skip planning entirely for small clear work, compress phases when the answers are obvious, and treat the first plan as a hypothesis. Replanning is the rule, not the exception.

The shape: SCOPE → EXPLORE → DECOMPOSE → VERIFY & APPROVE → TRACK, with a loop back to DECOMPOSE when review finds gaps.

---

## Phase 1: SCOPE

Bound the work before decomposing it. The goal is calibrating planning depth to actual scope, not generating a deliverable.

### Common moves

- **Search Sibyl** for related tasks, decisions, and prior plans: `sibyl search "<feature keywords>"`, `sibyl task list -s todo`. Cheap and often surfaces an already-decomposed predecessor.
- **Define success criteria** in measurable terms ("tests pass", "endpoint returns X", "p95 latency < 200ms") instead of vague goals like "improve performance".
- **Write completion criteria an autonomous run can consume**: complete AND validated — what proves each wave, plus review gates at wave checkpoints when stakes warrant. A run that can't close every gate ends blocked with receipts and a runbook for the remaining gates; blocked-cleanly is a legitimate terminal state, fake-done is not.
- **Identify constraints**: files that shouldn't change, dependencies to respect, timeline or budget pressure.
- **Calibrate planning depth** to scope:

  | Scale         | Description                | Planning depth             |
  | ------------- | -------------------------- | -------------------------- |
  | **Quick fix** | < 3 files, clear solution  | Skip planning, go build    |
  | **Feature**   | 3-10 files, known patterns | Light plan (this skill)    |
  | **Epic**      | 10+ files, new patterns    | Full plan + orchestration  |
  | **Redesign**  | Architecture change        | Full plan + research first |

If the work is a quick fix, stop planning and go build. Planning a five-minute change is pure overhead.

---

## Phase 2: EXPLORE

Understand the codebase surface before decomposing it. Plans built from filenames alone fall apart at contact with the actual code.

### Common moves

- **Map the impact surface**: which files and modules will this touch? Read the actual code rather than guessing from names; spawn an Explore agent when scope is genuinely uncertain.
- **Identify existing patterns**: how does similar functionality already work? What conventions apply (naming, file structure, test patterns)?
- **Trace dependencies**: what must exist before this can work, and what breaks if we change X?
- **Dig up the repo's real gate commands** — package scripts, hooks, CI jobs — so every task's Verify field can name a copy-paste runnable command instead of vague "run CI".

You're aiming for a mental model you can articulate: "this touches module A (new endpoint), module B (type changes), module C (tests); pattern follows existing feature X; depends on infrastructure Y being available." If you can't write that sentence, decomposition will rest on guesses.

---

## Phase 3: DECOMPOSE

Break the work into steps you can actually verify. The discipline that separates plans-that-survive from plans-that-fail is connecting each step to a concrete check.

### Measure twice: look for the reframe first

The most expensive plan is one that faithfully decomposes the wrong shape: tidy tasks, clean DAG, all building something that didn't need to exist. Before breaking work down, spend one pass hunting the judo move that shrinks it.

- **Can a reframe collapse the task list?** A different shape might turn ten tasks into three. Reframe before you decompose, not after you've built.
- **Does the codebase already own this?** Reusing an existing pattern, module, or canonical helper beats decomposing a bespoke build of the same thing.
- **What can we not build?** The cheapest task is the one you strike from the plan. Delete a mode, a layer, a config surface rather than scheduling work to construct it.

Ambition of the destination and complexity of the mechanism are separate dials — pressure-test both. Plans get bounced for timidity as often as implementations get bounced for sprawl; the bar is usefulness, not smallness. Two questions calibrate the mechanism: **how long does this live?** (a two-week component earns no release pipeline) and **what's the riskiest narrow path?** — slice canary-first, one concrete end-to-end proof before generalizing.

Measure twice, cut once: confirm this is the simplest shape that reaches the real destination, then decompose it.

### The verification heuristic

A step without a verification method is a hope, not a step. Push every task toward a concrete check before considering it decomposed. For each task, the useful fields are:

| Field          | Description                     |
| -------------- | ------------------------------- |
| **What**       | Specific implementation action  |
| **Files**      | Exact files to create/modify    |
| **Verify**     | How to confirm it works         |
| **Depends on** | Which tasks must complete first |

### Name the real gates

"Verify: tests pass" is a placeholder; `moon run core:test && moon run core:lint` is a gate. Use the repo's actual commands — found during EXPLORE — so every Verify field is copy-paste runnable. Reserve manual verification for surfaces with genuinely no automation, and say why.

### Decomposition heuristics

- **Slice size is a negotiated dial, not a constant.** Small slices verify tightly; larger slices buy throughput but decay corrections faster and drift scope further, so they need proportionally stronger pinned invariants and wave-boundary recall. And slice size only matters if progress integrates — parallel work that can't merge makes worktrees, not cumulative progress.
- **One concern per task.** "Add endpoint AND write tests" is two tasks; treat conjunctions in task titles as splitting hints.
- **Mark parallelizable tasks.** Tasks with no shared files can run simultaneously, which matters once you hand off to orchestration.

### Pin what priors will erase

Deliberately-open decisions ("the result is 0..N PRs, agent's choice") are exactly what models re-narrow to conventional shapes over long runs. Write them into the plan as named invariants, verbatim, with rejected alternatives preserved rather than deleted — then re-read them at wave boundaries and before touching adjacent surface. When the user drops a constraint mid-planning, it lands in the plan the same turn it's spoken: conversational corrections decay, pinned ones don't.

### Task Format

```markdown
## Task [N]: [Imperative title]

**Files:** `src/path/file.ts`, `tests/path/file.test.ts`
**Depends on:** Task [M]
**Parallel:** Yes/No (can run alongside Task [X])

### Implementation

[2-4 bullet points of what to do]

### Verify

- [ ] `pnpm typecheck` passes
- [ ] `pnpm test -- file.test.ts` passes
- [ ] [specific assertion about behavior]
```

---

## Phase 4: VERIFY & APPROVE

Sanity-check the plan before presenting it. The goal isn't ceremony; it's catching the obvious failure modes that turn plans into churn.

### Worth confirming before presenting

- Every task has a verification method (the most common gap)
- Dependencies form a DAG, no cycles
- No two parallel tasks touch the same files
- Total scope still matches the success criteria from Phase 1
- Nothing snuck in that you don't actually need yet (YAGNI)
- No task survives that a reframe could delete (the judo check from Phase 3)
- The plan names its **non-goals** — the adjacent things it deliberately does not build. Downstream gates measure correctness, not sprawl; the fence is what wave-boundary checks read.

### Fact-audit before build

A plan handed to implementation is a set of claims, not orders. Before executing — yours or inherited — label each load-bearing claim VERIFIED / STALE / WRONG against the live repo and deployment, veto phases whose premises fail, and fold findings into the plan itself: patch the spec, don't comment on it. A plan older than the tree it describes gets this pass automatically.

Iterate the plan to convergence. Spec defects are the most expensive class, so review a plan until it holds up ("until we love it"), not until an iteration counter expires — the caps on code-review loops exist to stop re-litigating the same finding and don't apply here.

### Present for Approval

Show the plan as a structured list with waves:

```markdown
## Plan: [Feature Name]

**Success criteria:** [measurable outcome]
**Non-goals:** [adjacent things this deliberately does not build]
**Estimated tasks:** [N] across [M] waves

### Wave 1: Foundation

- [ ] Task 1: [title] → verify: [method]
- [ ] Task 2: [title] → verify: [method]

### Wave 2: Core Implementation

- [ ] Task 3: [title] → verify: [method] (depends: 1)
- [ ] Task 4: [title] → verify: [method] (depends: 2)

### Wave 3: Integration

- [ ] Task 5: [title] → verify: [method] (depends: 3, 4)
```

### Gap analysis

Once the plan is on the page, ask whether anything's missing, whether tasks should be combined or split further, and whether the success criteria still feel right. The user often spots gaps you can't because they hold context you don't.

---

## Phase 5: TRACK

Make the plan durable. Skip this only when losing the plan would cost nothing to reconstruct — compaction, crashes, and other agents needing pickup all count as "spanning sessions" even inside one sitting.

**The plan doc is durable state, not chat exhaust.** For anything spanning compactions, sessions, or agents, the plan lives in the repo (graduate it from scratch dirs once it's load-bearing) and doubles as the progress ledger: current stack truth, wave-numbered statuses, the named next step, a memory checkpoint id. Write decisions into it before executing them — a decision that lives only in conversation doesn't survive the context window.

Mirror the plan into Sibyl as an epic with linked tasks and a pinned plan note ("[N] tasks across [M] waves, key decisions, critical path"); the sibyl skill carries the current invocation shapes. Task subjects mirror the plan's own IDs (R1.1, Wave 3) so the graph and the doc stay joinable.

### Adaptive replanning

Plans meet reality and reality usually wins. When a task surfaces unexpected complexity, pause and reassess instead of forcing through. Adjust the task list, update Sibyl, and surface the change: "task 3 revealed X, adjusting plan: [changes]." Replanning is a feature of the workflow, not evidence the original plan was bad.

After any pivot or section fix, thread it through the whole artifact: sweep for the dead vocabulary and stale table rows until every remaining hit is provably intentional — rejected-alternatives sections are the legitimate survivors. The dominant spec-revision failure is fixing one section without threading it through the others.

---

## Execution Handoff

Once the plan is approved, hand off to the right tool:

| Situation                      | Handoff                                       |
| ------------------------------ | --------------------------------------------- |
| 3-5 simple tasks, user present | Execute directly with verification gates      |
| 5-15 tasks, mixed parallel     | `/hyperskills:orchestrate` with wave strategy |
| Large epic, 15+ tasks          | Orchestrate with Epic Parallel Build strategy |
| Needs more research first      | `/hyperskills:research` before executing      |

**Package by review surface, not action count.** Phases become rollout gates inside one PR unless reviewer domains or behavior isolation force a split. Over-serialization is compliance theater; a ten-PR plan is as wrong as a one-blob plan.

### Wave-boundary shape check

Tests and reviews measure correctness; nothing downstream measures sprawl unless the plan gave it a fence. At each wave boundary, check shape too: classify the branch diff by top-level path against the mission (`git diff --name-only origin/${BASE:-main}...HEAD | awk -F/ '{print $1"/"$2}' | sort | uniq -c | sort -nr   # BASE = the PR's actual base ref`) and ask which pieces prove the MVP, not which pieces merely exist. The next-spec-gap loop is the engine of unattended work and the engine of accidental empires — the non-goals fence from Phase 4 is what this check reads.

### Trust gradient for execution

Heavy review on every task accumulates noise; zero review accumulates risk. Lean toward heavier review early and lighter review once patterns prove stable:

| Review level      | What it includes                               | When it applies                             |
| ----------------- | ---------------------------------------------- | ------------------------------------------- |
| **Full ceremony** | Implement + spec review + `cross-model-review` | Early waves, high stakes, unproven patterns |
| **Standard**      | Implement + spec review                        | Mid-plan waves once patterns stabilize      |
| **Light**         | Implement + quick verify                       | Late waves on established patterns          |

This is earned confidence, not cutting corners. The gradient resets if a task departs from the established pattern. Stay heavy for anything touching auth, payments, migrations, or data integrity regardless of where you are in the plan.

More review is not free: review-fix loops are a monotonic scope ratchet unless responses triage blockers from follow-ups and the fix pass carries a pre-declared file budget.

---

## Anti-Patterns

| Anti-Pattern                           | Fix                                          |
| -------------------------------------- | -------------------------------------------- |
| Planning a five-minute fix             | Build directly and verify                    |
| Tasks without verification             | Add a concrete check or split the task       |
| Parallel tasks touching the same files | Sequence them or repartition ownership       |
| Planning from filenames only           | Read the actual code path before decomposing |
| Decomposing a bad shape into tasks     | Hunt the judo move before you decompose      |
| Treating the first plan as permanent   | Replan when reality reveals new constraints  |
| Plan doc that lives only in chat       | Write it to the repo before executing        |
| Open decision left unpinned            | Prior drift re-narrows it; pin it verbatim   |
| Green gates as proof of shape          | Wave-boundary diff check against non-goals   |

---

## What This Skill is NOT

- **Not required for simple tasks.** If the solution is obvious, just build it.
- **Not an architecture essay — and not a bare checklist either.** The plan carries decisions, pinned invariants, and rejected alternatives (the things prior-drift erases), and never its own making-of: review sausage and version stories stay out of the artifact.
- **Not a blocker.** If the user says "just start building," start building. You can plan in parallel.
- **Not rigid.** Plans adapt. The first plan is a hypothesis.
