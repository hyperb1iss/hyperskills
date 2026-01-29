<h1 align="center">
  hyperskills
</h1>

<p align="center">
  <strong>Focused AI agent skills for things models don't already know</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Skills-3-e135ff?style=for-the-badge&logo=anthropic&logoColor=white" alt="3 Skills">
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

Modern models already know how to write React components, Kubernetes manifests, and PyTorch code. They don't need 300 lines of examples for that.

**hyperskills** provides skills for things that are genuinely hard to get right without guidance:

- **Orchestrating dozens of agents** without stepping on each other's work
- **Security frameworks** that are easy to forget under pressure
- **Git decision trees** for the operations that actually trip people up

Three skills. Zero bloat.

## Installation

### Claude Code

```bash
/plugin install hyperskills
```

### Vercel Skills (skills.sh)

```bash
# Install all skills
npx skills add hyperbliss/hyperskills --all

# Or specific skills
npx skills add hyperbliss/hyperskills --skill orchestrate
npx skills add hyperbliss/hyperskills --skill security
npx skills add hyperbliss/hyperskills --skill git
```

### Manual

```bash
git clone https://github.com/hyperb1iss/hyperskills.git
ln -s $(pwd)/hyperskills/skills ~/.claude/skills/hyperskills
```

## Skills

### `hyperskills:orchestrate`

Meta-orchestration patterns mined from 597+ real agent dispatches. This is the skill that tells you _which_ multi-agent strategy to use, _how_ to structure prompts for parallel agents, and _when_ to use background vs foreground.

**Strategies:** Research Swarm, Epic Parallel Build, Sequential Pipeline, Parallel Sweep, Multi-Dimensional Audit, Full Lifecycle.

### `hyperskills:security`

Frameworks and checklists for secure systems. Zero Trust principles, STRIDE threat modeling, OWASP Top 10 checklist, SLSA supply chain levels, incident response phases, and compliance framework reference.

### `hyperskills:git`

Decision trees for the git operations that actually cause problems. When to rebase vs merge, how to handle lock file conflicts, SOPS encrypted file resolution, undo operations by scenario, and repository archaeology commands.

## Usage

```bash
/hyperskills:orchestrate   # Multi-agent coordination
/hyperskills:security      # Security frameworks & checklists
/hyperskills:git           # Complex git operations
```

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
make check      # Validate structure
make stats      # Show plugin statistics
```

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
