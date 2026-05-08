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
  <img src="https://img.shields.io/badge/Skills-17-e135ff?style=for-the-badge&logo=anthropic&logoColor=white" alt="17 Skills">
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

hyperskills is built around an agent workflow. Brainstorming structured by the Double Diamond. Wave-based research with deferred synthesis. Verification-driven planning and implementation. Cross-model peer review that catches what self-review misses. Six orchestration strategies for multi-agent work. Conversation consolidation that pulls signal out of past sessions into persistent memory. The process skills are the heart of it, mined from thousands of real dispatches and tens of thousands of tracked operations.

Domain skills round out the toolbox where models have stale or missing knowledge: the agent-sandbox Kubernetes operator (too new for training data), current Astral Python tooling, Tilt operational decision trees, terminal UI design that survives across emulators, an OWASP/SLSA security reference.

Each skill encodes procedural knowledge, decision trees, anti-patterns, and current SOTA. None prescribes a strict workflow. They give you knowledge and framing; you decide when to reach for them. Skills carry procedural knowledge in-context; [Sibyl](https://github.com/hyperb1iss/sibyl) carries decisions, patterns, and learnings across sessions. 17 skills, all installable independently.

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

| Situation                | Skills that pair well                                            |
| ------------------------ | ---------------------------------------------------------------- |
| New feature              | brainstorm, plan, implement, cross-model-review                  |
| Greenfield project       | brainstorm, research, plan, orchestrate, implement               |
| Architecture decision    | brainstorm, research                                             |
| Large refactor           | plan, orchestrate, implement, cross-model-review                 |
| Bug fix                  | implement (the skill scales itself for trivial fixes)            |
| Python project work      | uv, ruff, ty, uv-build                                           |
| Knowledge consolidation  | dream pulls insights from past sessions into Sibyl               |

Domain skills (security, git, tilt, agent-sandbox, tui-design, uv, ruff, ty, uv-build) plug in wherever the work touches their territory. Any skill can loop back when new questions emerge.

## 🔮 Skills

### Process Skills

How to approach a class of work: workflows, phases, decision gates. The interesting part of hyperskills lives here.

#### `brainstorm`: Structured Ideation

Double Diamond model for creative work. Diverge on the problem, converge on a definition, diverge on solutions, converge on a decision. Grounded in Sibyl so you don't re-explore solved problems. Includes a Council pattern (advocate / critic agents) for complex architectural decisions.

```bash
/hyperskills:brainstorm
```

#### `research`: Multi-Agent Knowledge Gathering

Wave-based research with deferred synthesis. Deploy agents in waves across a research surface, run gap analysis between waves, then synthesize with the full picture. Covers technology evaluation, codebase archaeology, SOTA analysis, and competitive landscape patterns. Caps at 3 waves for most research; if that isn't enough, the question itself needs reframing.

```bash
/hyperskills:research
```

#### `plan`: Task Decomposition

Verification-driven planning. Decomposes work into small tasks ordered by dependency, marks parallelizable waves for orchestration, and tracks in Sibyl when the work spans more than a session. Includes a trust gradient for review overhead: full ceremony early, lighter as patterns stabilize.

```bash
/hyperskills:plan
```

#### `implement`: Verification-Driven Coding

Distilled from 21,321 tracked operations across 64+ projects. Patterns that consistently ship working code:

- 2-3 edits then verify, the cadence that prevents debugging spirals
- Scale selection from trivial (1-5 edits) to epic (1000+ edits), with the right strategy for each
- Dependency chains for fullstack and Rust projects
- Error recovery: spiral prevention, the two-correction rule, when to /clear and restart
- Decision trees: read vs edit, subagents vs direct, bug fix vs feature vs refactor

```bash
/hyperskills:implement
```

#### `orchestrate`: Multi-Agent Coordination

Six orchestration strategies mined from 597+ real agent dispatches: Research Swarm, Epic Parallel Build, Sequential Pipeline, Parallel Sweep, Multi-Dimensional Audit, and Full Lifecycle. Helps you choose which strategy fits the work, how to structure prompts for parallel agents, and when to use background vs foreground.

```bash
/hyperskills:orchestrate
```

#### `cross-model-review`: Bidirectional Cross-Model Code Review

The author model writes code, a different model reviews it. Different architecture, different training distribution, no self-approval bias. Works in either direction: Claude Code calls Codex via `codex review`, and Codex calls Claude via `claude -p`. The latter has gnarly gotchas (the `yield_time_ms: 300000` rule, the `--` separator for variadic flags, output capture to a file rather than `tail`) that bite without warning. All documented. Includes multi-pass strategy, piped-diff vs tool-access modes, and ready-to-use review prompts for security, architecture, performance, error handling, and concurrency.

```bash
/hyperskills:cross-model-review
```

#### `codex-review`: Codex-Specific Code Review

The Claude → Codex direction in depth. `codex review` (structured diff) and `codex exec` (freeform deep-dive), multi-pass strategy (correctness, security, architecture, performance), and integration with the Ralph Loop for iterative quality enforcement. Reach for `cross-model-review` when you want bidirectional coverage; reach for this one when you specifically want Codex reviewing from a Claude session.

```bash
/hyperskills:codex-review
```

#### `dream`: Conversation Memory Consolidation

Two-phase conversation review. Harvests Claude Code and Codex sessions, extracts decisions, patterns, corrections, and unresolved questions, then writes durable knowledge into Sibyl. Use it for end-of-day memory maintenance or deep cross-project synthesis.

```bash
/hyperskills:dream
```

### Domain Skills

Specialized knowledge for specific technologies where models have stale or missing training data. Reference material, decision trees, field-tested patterns.

#### `security`: Security Operations

STRIDE threat modeling, NIST Zero Trust, OWASP Top 10:2025, SLSA 1.2 Build / Source tracks, incident response mapped to NIST CSF 2.0, and a compliance framework reference.

```bash
/hyperskills:security
```

#### `git`: Advanced Git Operations

Decision trees for the operations that actually cause problems. Rebase vs merge, lock file conflicts, SOPS encrypted file resolution, undo operations by scenario, cherry-pick workflows, and repository archaeology commands.

```bash
/hyperskills:git
```

#### `tilt`: Kubernetes Development

Tilt operational guide. CLI commands for log viewing, resource management, and debugging. Tiltfile authoring with build strategy selectors, live update decision trees, and resource configuration. Full API catalog and power patterns live in progressive disclosure references.

```bash
/hyperskills:tilt
```

#### `agent-sandbox`: Kubernetes Operator for AI Agent Runtimes

Operational guide for the [`kubernetes-sigs/agent-sandbox`](https://github.com/kubernetes-sigs/agent-sandbox) operator. SIG Apps subproject, launched at KubeCon Atlanta in November 2025, so most training data predates it. Covers the four CRDs (Sandbox, SandboxTemplate, SandboxClaim, SandboxWarmPool), install and upgrade hazards, warm pool HPA tuning, PDB scoping gotchas, isolation runtime selection (gVisor, Kata), network policy patterns, Karpenter integration, and the Python and Go SDK surface.

```bash
/hyperskills:agent-sandbox
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

| Skill                | Reference Files                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------- |
| `implement`          | `benchmarks.md`: quantitative data from 21k operations and implementation archetype templates            |
| `codex-review`       | `prompts.md`: ready-to-use review prompt templates                                                       |
| `cross-model-review` | `prompts.md`: ready-to-use review prompt templates                                                       |
| `dream`              | `conversation-formats.md`, `extraction-guide.md`: session schemas and memory extraction rules            |
| `tilt`               | `api-reference.md`, `patterns.md`: full Tiltfile API and power patterns                                  |
| `agent-sandbox`      | `crds.md`, `patterns.md`, `clients.md`: CRD fields, production patterns, SDK deep-dive                   |
| `tui-design`         | `visual-catalog.md`, `app-patterns.md`: Unicode catalog and app gallery                                  |
| `uv`                 | `configuration.md`, `docker-ci.md`, `resolution.md`: uv config, CI patterns, resolver details            |
| `ruff`               | `configuration.md`, `rules.md`: Ruff config and rule catalog snapshot                                    |
| `ty`                 | `migration.md`, `type-system.md`: migration from mypy or Pyright and beta type-system support            |

## Compatibility

| Platform           | Installation                                       |
| ------------------ | -------------------------------------------------- |
| **Claude Code**    | `/plugin marketplace add hyperb1iss/hyperskills`<br>`/plugin install hyperskills@hyperb1iss` |
| **Codex CLI**      | `npx skills add hyperbliss/hyperskills -a codex`   |
| **Cursor**         | `npx skills add hyperbliss/hyperskills -a cursor`  |
| **GitHub Copilot** | `npx skills add hyperbliss/hyperskills -a copilot` |
| **Gemini CLI**     | `npx skills add hyperbliss/hyperskills -a gemini`  |

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
