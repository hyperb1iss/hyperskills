<h1 align="center">
  ⚡ hyperskills
</h1>

<p align="center">
  <strong>Focused AI agent skills for things models don't already know</strong>
</p>

<p align="center">
  <em>Knowledge, guidance, wisdom, SOTA. Reach for what fits.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Skills-16-e135ff?style=for-the-badge&logo=anthropic&logoColor=white" alt="16 Skills">
  <img src="https://img.shields.io/badge/skills.sh-Compatible-ff6ac1?style=for-the-badge&logo=vercel&logoColor=white" alt="skills.sh">
</p>

<p align="center">
  <a href="https://github.com/hyperb1iss/hyperskills/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/hyperb1iss/hyperskills?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="License">
  </a>
  <a href="https://github.com/hyperb1iss/hyperskills/releases">
    <img src="https://img.shields.io/github/v/release/hyperb1iss/hyperskills?style=flat-square&logo=github&logoColor=white" alt="Release">
  </a>
</p>

---

## 💎 What This Is

Models already know how to write React components, Kubernetes manifests, and PyTorch code. They don't need 300 lines of examples for that.

hyperskills is built around an agent workflow. Brainstorming structured by the Double Diamond. Wave-based research with deferred synthesis. Verification-driven planning and implementation. Cross-model peer review that catches what self-review misses. Seven orchestration strategies for multi-agent work. Conversation consolidation that pulls signal out of past sessions into persistent memory. The process skills are the heart of it, mined from thousands of real dispatches and tens of thousands of tracked operations — most recently re-hardened against a 100-day corpus of 600 real Claude and Codex sessions (Jul 2026).

Domain skills round out the toolbox where models have stale or missing knowledge: current Astral Python tooling, Tilt operational decision trees, and terminal UI design that survives across emulators.

Each skill encodes procedural knowledge, decision trees, anti-patterns, and current SOTA. None prescribes a strict workflow. They give you knowledge and framing; you decide when to reach for them. Skills carry procedural knowledge in-context; [Sibyl](https://github.com/hyperb1iss/sibyl) carries decisions, patterns, and learnings across sessions. 16 skills, all installable independently.

## ⚡ Installation

### Claude Code

```bash
# Register the marketplace, then install
/plugin marketplace add hyperb1iss/hyperskills
/plugin install hyperskills@hyperb1iss
```

### Vercel Skills (skills.sh)

```bash
# All skills
npx skills add hyperbliss/hyperskills --all

# Pick what you need
npx skills add hyperbliss/hyperskills --skill implement
npx skills add hyperbliss/hyperskills --skill orchestrate
```

### Manual

```bash
git clone https://github.com/hyperb1iss/hyperskills.git
ln -s $(pwd)/hyperskills/skills ~/.claude/skills/hyperskills
```

## 🪄 Composing Skills

Skills are independent. None of them require the others. A typo fix doesn't need brainstorming, a clear bug doesn't need research, and the Python tooling skills compose freely.

A few combinations come up often, more as observation than prescription:

| Situation               | Skills that pair well                                 |
| ----------------------- | ----------------------------------------------------- |
| New feature             | brainstorm, plan, implement, cross-model-review       |
| Greenfield project      | brainstorm, research, plan, orchestrate, implement    |
| Architecture decision   | brainstorm, research                                  |
| Large refactor          | plan, orchestrate, implement, cross-model-review      |
| Bug fix                 | implement (the skill scales itself for trivial fixes) |
| Opening a PR            | super-good-pr, then announce it in your own voice     |
| Python project work     | uv, ruff, ty, uv-build                                |
| Knowledge consolidation | dream pulls insights from past sessions into Sibyl    |

Domain skills (git, tilt, tui-design, uv, ruff, ty, uv-build) plug in wherever the work touches their territory. Any skill can loop back when new questions emerge.

## 🔮 Skills

### Process Skills

How to approach a class of work: workflows, phases, decision gates. The interesting part of hyperskills lives here.

#### `brainstorm`: Structured Ideation

Double Diamond model for creative work. Diverge on the problem, converge on a definition, diverge on solutions, converge on a decision. Grounded in Sibyl so you don't re-explore solved problems. Reads the ask before picking a mode (stakes plus uncertainty means explore wide, not plan), pressure-tests both dials of the bar (ambitious destination, boring mechanism), and carries the multi-model shapes that survive contact with real work: artifact-mediated design consults and cross-model convergence as a confidence signal.

```bash
/hyperskills:brainstorm
```

#### `research`: Multi-Agent Knowledge Gathering

Wave-based research with deferred synthesis. Deploy agents in waves across a research surface, run gap analysis between waves, then synthesize with the full picture. Covers technology evaluation, codebase archaeology, SOTA analysis, and competitive landscape patterns. The wave budget is a churn guard, not a wall: keep going while waves yield, reframe when they oscillate. Epistemics are load-bearing: premise-check before any fan-out, date-anchored briefs, and consensus-is-not-verification — version claims settle against a live registry, never vote count.

```bash
/hyperskills:research
```

#### `plan`: Task Decomposition

Verification-driven planning centered on a durable spec artifact: pinned invariants (including the deliberately-open decisions that model priors love to erase), adversarial fact-audits that patch the spec rather than comment on it, completion criteria of complete-and-validated, and shape checkpoints at wave boundaries that catch the sprawl green gates miss. Decomposes into dependency-ordered tasks with parallelizable waves, tracks in Sibyl when work outlives a session, and scales review ceremony by stakes rather than task number.

```bash
/hyperskills:plan
```

#### `implement`: Verification-Driven Coding

Distilled from 21,321 tracked operations across 64+ projects. Patterns that consistently ship working code:

- 2-3 edits then verify, the cadence that prevents debugging spirals
- Proof lives at the consumption boundary — and a green check only counts if it demonstrably did the work
- Scale selection from trivial (1-5 edits) to epic (1000+ edits), with the right strategy for each
- The judo move, the shape checkpoint at commit, and fix-the-class-bound-the-fix
- Error recovery: name the failure class first, spiral prevention, incident mode (depth up, breadth flat)

```bash
/hyperskills:implement
```

#### `orchestrate`: Multi-Agent Coordination

Seven orchestration strategies mined from 597+ real agent dispatches: Research Swarm, Epic Parallel Build, Sequential Pipeline, Parallel Sweep, Multi-Dimensional Audit, Fleet/Stack Maintenance, and Full Lifecycle. Covers the whole arc, not just launch: worker-brief anatomy (scope fences, done-means, traps, receipts-already-run), deviation adjudication, the fleet verification lifecycle, slow-vs-stuck watcher contracts, and shape checkpoints against the scope drift that kills long fan-outs. Copyable dispatch briefs live in references.

```bash
/hyperskills:orchestrate
```

#### `cross-model-review`: Bidirectional Cross-Model Code Review

The author model writes, a different model reviews — and the independence claim is scoped honestly: it breaks self-review bias, not shared-training staleness. Works in either direction: Claude Code calls Codex via `codex review`, and Codex calls Claude via `claude -p`, whose gnarly gotchas (the `yield_time_ms: 300000` rule, the `--` separator for variadic flags, output capture to a file rather than `tail`) are all documented. Now covers the receiving half too: findings are claims to verify, findings-ledger re-review loops that converge instead of churning, verdict freshness (a PASS covers a SHA), the hang playbook, and a labeled degradation ladder. Beyond code review: claim-level fact-checks, diagnosis checks before fix mode, and artifact-mediated design consults.

```bash
/hyperskills:cross-model-review
```

#### `codex-review`: Codex-Specific Code Review

The Claude → Codex direction in depth. `codex review` (structured diff, custom prompt supported) and `codex exec` (freeform deep-dive), multi-pass strategy, the Ralph Loop with a convergence budget instead of a hard round cap, the hang playbook (output-file growth is the discriminator, never elapsed time), and honest degradation when the reviewer can't run. Reach for `cross-model-review` when you want bidirectional coverage; reach for this one when you specifically want Codex reviewing from a Claude session.

```bash
/hyperskills:codex-review
```

#### `super-good-pr`: Reviewer-First PR Descriptions

What a PR description is actually for: handing a human the mental model fast, proving the parts they'd doubt, and being honest about what you didn't do. Lead with why, prove every claim with a receipt, name the load-bearing invariant, stay honest about blast radius. And because a body is born once but lives for weeks: surgical read-modify-write maintenance (never regenerate), SHA-keyed receipt refresh after every push, squash rewrites that carry the story into the body, and review-thread disposition ledgers. Carries the section spine, the emoji palette (and the AI-slop set to avoid), and repo-template integration.

```bash
/hyperskills:super-good-pr
```

#### `dream`: Conversation Memory Consolidation

Conversation review aimed at what inline capture can't see: gotchas that repeat across sessions, prompt-stream telemetry (instruction frequency is the codify-next signal; vanished instructions prove an encoding worked), and cross-project connections. Harvests Claude Code and Codex sessions and writes durable knowledge into Sibyl — from a quick end-of-day nap up to swarm-scale mining runs (distill, fan out, merge, review).

```bash
/hyperskills:dream
```

### Domain Skills

Specialized knowledge for specific technologies where models have stale or missing training data. Reference material, decision trees, field-tested patterns.

#### `git`: Advanced Git Operations

The operations that actually cause problems, weighted the way real work is: the PR-branch upkeep loop (rebase, pinned-lease push, review settlement), squash-merge-aware surgery, the rewrite bracket (backup ref before, machine-checkable proof after — a clean rebase is not a correct rebase), lock file regeneration, undo operations by scenario, commit bodies via quoted heredoc or message file, and shared-repo coexistence for multi-agent worktrees.

```bash
/hyperskills:git
```

#### `tilt`: Kubernetes Development

Tilt operational guide. CLI commands for log viewing, resource management, and debugging. Tiltfile authoring with build strategy selectors, live update decision trees, and resource configuration. Full API catalog and power patterns live in progressive disclosure references.

```bash
/hyperskills:tilt
```

#### `tui-design`: Terminal UI Design System

Framework-agnostic TUI design patterns. Layout paradigm selector, interaction model decision trees, terminal color theory, visual hierarchy techniques, data visualization, and animation patterns. Works with Ratatui, Ink, Textual, Bubbletea, or any TUI toolkit. Includes a Unicode visual catalog and a gallery of real TUI app design patterns.

```bash
/hyperskills:tui-design
```

#### `uv`: Python Package & Project Management

Astral uv workflows for projects, scripts, tools, Python versions, workspaces, locking, publishing, and Docker / CI patterns. Encodes when to use project commands instead of the pip interface.

```bash
/hyperskills:uv
```

#### `ruff`: Python Linting & Formatting

Current Ruff guidance for lint rule selection, formatter compatibility, suppression, preview mode, dependency graph analysis, and debugging resolved configuration.

```bash
/hyperskills:ruff
```

#### `ty`: Python Type Checking

Astral ty guidance for beta adoption, CLI usage, configuration, suppression comments, editor and LSP setup, current limitations, and migration from mypy or Pyright.

```bash
/hyperskills:ty
```

#### `uv-build`: Python Build Backend

uv_build backend guidance for pure Python packages, module discovery, namespace and stub packages, file inclusion, publishing workflows, migration from setuptools / hatchling / flit, and reproducible build checks.

```bash
/hyperskills:uv-build
```

## 🧪 Architecture

Skills use progressive disclosure. Light when you don't need depth, deep when you do.

```
Level 1: Metadata (name + description)     ← Always in context, ~100 words
Level 2: SKILL.md body                     ← Loaded when the skill triggers, 1,500-3,000 words
Level 3: references/                       ← Loaded on demand, no length cap
```

Skills with reference files for the deep-dive material:

| Skill                | Reference Files                                                                               |
| -------------------- | --------------------------------------------------------------------------------------------- |
| `implement`          | `benchmarks.md`, `recovery.md`: quantitative data from 21k operations, error-recovery detail  |
| `codex-review`       | `prompts.md`: ready-to-use review prompt templates                                            |
| `cross-model-review` | `prompts.md`, `failure-recovery.md`: review prompts, hang ladder and failure triage           |
| `orchestrate`        | `dispatch-briefs.md`: copyable worker, reviewer, and research dispatch briefs                 |
| `dream`              | `conversation-formats.md`, `extraction-guide.md`: session schemas and memory extraction rules |
| `tilt`               | `api-reference.md`, `patterns.md`: full Tiltfile API and power patterns                       |
| `tui-design`         | `visual-catalog.md`, `app-patterns.md`: Unicode catalog and app gallery                       |
| `uv`                 | `configuration.md`, `docker-ci.md`, `resolution.md`: uv config, CI patterns, resolver details |
| `ruff`               | `configuration.md`, `rules.md`: Ruff config and rule catalog snapshot                         |
| `ty`                 | `migration.md`, `type-system.md`: migration from mypy or Pyright and beta type-system support |

## Compatibility

| Platform           | Installation                                                                                 |
| ------------------ | -------------------------------------------------------------------------------------------- |
| **Claude Code**    | `/plugin marketplace add hyperb1iss/hyperskills`<br>`/plugin install hyperskills@hyperb1iss` |
| **Codex CLI**      | `npx skills add hyperbliss/hyperskills -a codex`                                             |
| **Cursor**         | `npx skills add hyperbliss/hyperskills -a cursor`                                            |
| **GitHub Copilot** | `npx skills add hyperbliss/hyperskills -a copilot`                                           |
| **Gemini CLI**     | `npx skills add hyperbliss/hyperskills -a gemini`                                            |

## 🛠️ Development

```bash
git clone https://github.com/hyperb1iss/hyperskills.git
cd hyperskills

make lint       # Run linters
make format     # Format files
make check      # Validate plugin structure
make stats      # Show plugin statistics
```

See [AGENTS.md](AGENTS.md) for the contributor guide on adding new skills.

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  💜
</p>

<p align="center">
  <a href="https://github.com/hyperb1iss">
    <img src="https://img.shields.io/badge/GitHub-hyperb1iss-181717?style=for-the-badge&logo=github" alt="GitHub">
  </a>
  <a href="https://bsky.app/profile/hyperbliss.tech">
    <img src="https://img.shields.io/badge/Bluesky-@hyperbliss.tech-1185fe?style=for-the-badge&logo=bluesky" alt="Bluesky">
  </a>
</p>

<p align="center">
  <sub>
    Built by <a href="https://hyperbliss.tech"><strong>Hyperbliss Technologies</strong></a>
  </sub>
</p>
