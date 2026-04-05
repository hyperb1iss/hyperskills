<h1 align="center">
  hyperskills
</h1>

<p align="center">
  <strong>Focused AI agent skills for things models don't already know</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Skills-10-e135ff?style=for-the-badge&logo=anthropic&logoColor=white" alt="10 Skills">
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

## What This Is

Models already know how to write React components, Kubernetes manifests, and PyTorch code. They don't need 300 lines of examples for that.

**hyperskills** provides skills for things that are genuinely hard to get right without guidance — procedural knowledge distilled from thousands of real sessions, decision trees for high-stakes operations, and multi-agent orchestration patterns that actually work in production.

10 skills. Zero bloat. Each one earned its place through real-world evidence.

## Installation

### Claude Code

```bash
/plugin install hyperskills
```

### Vercel Skills (skills.sh)

```bash
# Install all skills
npx skills add hyperbliss/hyperskills --all

# Or pick what you need
npx skills add hyperbliss/hyperskills --skill implement
npx skills add hyperbliss/hyperskills --skill orchestrate
```

### Manual

```bash
git clone https://github.com/hyperb1iss/hyperskills.git
ln -s $(pwd)/hyperskills/skills ~/.claude/skills/hyperskills
```

## How the Skills Work Together

The skills form a workflow pipeline. Each one handles a phase of the development lifecycle and hands off to the next:

```
 brainstorm ──→ research ──→ plan ──→ implement ──→ codex-review
     │              │           │          │
     │              │           │          └──→ git
     │              │           │
     │              │           └──→ orchestrate (parallel agents)
     │              │
     └──────────────┴──→ Any skill can loop back when new questions emerge
```

**Typical flows:**

| Scenario              | Flow                                                             |
| --------------------- | ---------------------------------------------------------------- |
| New feature           | `brainstorm` → `plan` → `implement` → `codex-review`             |
| Greenfield project    | `brainstorm` → `research` → `plan` → `orchestrate` → `implement` |
| Bug fix               | `implement` (straight to it — scale selection handles this)      |
| Architecture decision | `brainstorm` → `research` → decide                               |
| Large refactor        | `plan` → `orchestrate` → `implement` → `codex-review`            |

You don't need to follow the full pipeline. Each skill has built-in scale selection — a typo fix doesn't need brainstorming, and a clear bug doesn't need research. Start wherever makes sense.

## Skills

### Process Skills

These encode _how_ to approach a class of work — workflows, phases, and decision gates.

#### `brainstorm` — Structured Ideation

Double Diamond model for creative work: diverge on the problem, converge on a definition, diverge on solutions, converge on a decision. Grounded in persistent memory (Sibyl) so you never re-explore solved problems. Includes a Council pattern for complex architectural decisions using advocate/critic agents.

```bash
/hyperskills:brainstorm
```

#### `research` — Multi-Agent Knowledge Gathering

Wave-based research with deferred synthesis. Deploy agents in waves across a research surface, run gap analysis between waves, then synthesize with the full picture. Covers technology evaluation, codebase archaeology, SOTA analysis, and competitive landscape patterns. Max 3 waves — if that's not enough, reframe the question.

```bash
/hyperskills:research
```

#### `plan` — Task Decomposition

Verification-driven planning where every step has a concrete check. Decomposes work into 2-5 minute tasks ordered by dependency, marks parallelizable waves for orchestration, and tracks everything in Sibyl. Includes a trust gradient — full ceremony for early tasks, lighter review as patterns stabilize.

```bash
/hyperskills:plan
```

#### `implement` — Verification-Driven Coding

The core implementation skill, distilled from 21,321 tracked operations across 64+ projects. Encodes the patterns that consistently ship working code:

- **2-3 edits then verify** — the sweet spot that prevents debugging spirals
- **Scale selection** — from trivial (1-5 edits) to epic (1000+), with the right strategy for each
- **Dependency chains** — build order for fullstack and Rust projects
- **Error recovery** — spiral prevention, the two-correction rule, when to `/clear` and restart
- **Decision trees** — read vs edit, subagents vs direct, bug fix vs feature vs refactor

```bash
/hyperskills:implement
```

#### `orchestrate` — Multi-Agent Coordination

Meta-orchestration patterns mined from 597+ real agent dispatches. Tells you _which_ multi-agent strategy to use, _how_ to structure prompts for parallel agents, and _when_ to use background vs foreground. Six strategies: Research Swarm, Epic Parallel Build, Sequential Pipeline, Parallel Sweep, Multi-Dimensional Audit, and Full Lifecycle.

```bash
/hyperskills:orchestrate
```

#### `codex-review` — Cross-Model Code Review

Claude writes code, Codex reviews it — different architecture, different training distribution, no self-approval bias. Multi-pass review strategy (correctness → security → architecture → performance), 7 ready-to-use prompt templates, and integration with the Ralph Loop for iterative quality enforcement.

```bash
/hyperskills:codex-review
```

### Domain Skills

These encode specialized knowledge for specific technologies — reference material, decision trees, and hard-won patterns.

#### `security` — Security Operations

Frameworks and checklists for secure systems. STRIDE threat modeling, Zero Trust principles, OWASP Top 10, SLSA supply chain levels, incident response phases, and compliance framework reference (SOC 2, HIPAA, PCI DSS).

```bash
/hyperskills:security
```

#### `git` — Advanced Git Operations

Decision trees for the operations that actually cause problems. When to rebase vs merge, how to handle lock file conflicts, SOPS encrypted file resolution, undo operations by scenario, cherry-pick workflows, and repository archaeology commands.

```bash
/hyperskills:git
```

#### `tilt` — Kubernetes Development

Complete Tilt operational reference. CLI commands for log viewing, resource management, and debugging. Tiltfile authoring with build strategy selectors, live update decision trees, and resource configuration. Full API catalog and power patterns in progressive disclosure references.

```bash
/hyperskills:tilt
```

#### `tui-design` — Terminal UI Design System

Universal design patterns for building exceptional terminal user interfaces. Layout paradigm selector, interaction model decision trees, terminal color theory, visual hierarchy techniques, data visualization, and animation patterns. Framework-agnostic — works with Ratatui, Ink, Textual, Bubbletea, or any TUI toolkit. Includes a Unicode visual catalog and gallery of real TUI app design patterns.

```bash
/hyperskills:tui-design
```

## Architecture

Skills use progressive disclosure to manage context efficiently:

```
Level 1: Metadata (name + description)     ← Always in context (~100 words)
Level 2: SKILL.md body                     ← Loaded when skill triggers (~1,500-3,000 words)
Level 3: references/                       ← Loaded on demand (unlimited)
```

Four skills include reference files for deep-dive content:

| Skill          | Reference Files                                                        |
| -------------- | ---------------------------------------------------------------------- |
| `implement`    | `benchmarks.md` — quantitative data from 21k operations                |
| `codex-review` | `prompts.md` — 7 ready-to-use review prompt templates                  |
| `tilt`         | `api-reference.md`, `patterns.md` — full Tiltfile API + power patterns |
| `tui-design`   | `visual-catalog.md`, `app-patterns.md` — Unicode catalog + app gallery |

## Compatibility

| Platform           | Installation                                       |
| ------------------ | -------------------------------------------------- |
| **Claude Code**    | `/plugin install hyperskills`                      |
| **Codex CLI**      | `npx skills add hyperbliss/hyperskills -a codex`   |
| **Cursor**         | `npx skills add hyperbliss/hyperskills -a cursor`  |
| **GitHub Copilot** | `npx skills add hyperbliss/hyperskills -a copilot` |
| **Gemini CLI**     | `npx skills add hyperbliss/hyperskills -a gemini`  |

## Development

```bash
git clone https://github.com/hyperb1iss/hyperskills.git
cd hyperskills

make lint       # Run linters
make format     # Format files
make check      # Validate plugin structure
make stats      # Show plugin statistics
```

See [AGENTS.md](AGENTS.md) for the full contributor guide on adding new skills.

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

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
