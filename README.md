<h1 align="center">
  ⚡ hyperskills
</h1>

<p align="center">
  <strong>Elite AI Agent Skills for Rapid Product Development</strong><br>
  <sub>Ship in days, not months</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Skills-7_Domains-e135ff?style=for-the-badge&logo=anthropic&logoColor=white" alt="7 Skills">
  <img src="https://img.shields.io/badge/Agents-23_Specialized-80ffea?style=for-the-badge&logo=robot&logoColor=black" alt="23 Agents">
  <img src="https://img.shields.io/badge/skills.sh-Compatible-ff6ac1?style=for-the-badge&logo=vercel&logoColor=white" alt="skills.sh">
</p>

<p align="center">
  <a href="https://github.com/hyperb1iss/hyperskills/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/hyperb1iss/hyperskills?style=flat-square&logo=apache&logoColor=white" alt="License">
  </a>
  <a href="https://github.com/hyperb1iss/hyperskills/releases">
    <img src="https://img.shields.io/github/v/release/hyperb1iss/hyperskills?style=flat-square&logo=github&logoColor=white" alt="Release">
  </a>
</p>

<p align="center">
  <a href="#-installation">Installation</a> •
  <a href="#-skills">Skills</a> •
  <a href="#-agents">Agents</a> •
  <a href="#-sota-knowledge">SOTA Knowledge</a> •
  <a href="#-philosophy">Philosophy</a>
</p>

---

## 💎 What This Is

**hyperskills** is a collection of 23 specialized AI agents across 7 skill domains, designed for teams that ship fast. Originally developed as the agent ecosystem for [Contains Studio](https://github.com/hyperb1iss/agents)—a rapid app development framework built around 6-day sprint cycles—these agents have been battle-tested, consolidated, and enhanced with cutting-edge 2026 techniques.

Instead of one generalist agent fumbling through everything, you get **specialists**:

- A **security architect** who knows eBPF, Zero Trust, and SLSA
- An **AI engineer** who speaks DSPy and MCP fluently
- A **platform engineer** who thinks in GitOps and OpenTofu
- A **growth hacker** who designs viral loops that actually work

Works with Claude Code, Codex CLI, Cursor, and any agent supporting the [skills.sh](https://skills.sh) ecosystem.

## ⚡ Installation

### Claude Code

```bash
# Install the plugin
/plugin install hyperskills
```

### Vercel Skills (skills.sh)

```bash
# Install all skills
npx skills add hyperb1iss/hyperskills --all

# Or specific skills
npx skills add hyperb1iss/hyperskills --skill ai
npx skills add hyperb1iss/hyperskills --skill security
```

### Manual

```bash
git clone https://github.com/hyperb1iss/hyperskills.git
ln -s $(pwd)/hyperskills/skills ~/.claude/skills/hyperskills
```

## 🎯 Usage

Invoke skills with `/hyperskills:<skill>`:

```bash
/hyperskills:fullstack    # Web development patterns
/hyperskills:ai           # AI/ML engineering
/hyperskills:security     # Security architecture
```

We recommend adding this to your `CLAUDE.md`:

> When working on this project, invoke the relevant `/hyperskills:<skill>` to ensure best practices are followed.

## 🔮 Skills

Skills are contextual knowledge bundles that auto-activate when relevant. Working on React code? The fullstack skill loads. Mention "Kubernetes deployment"? Platform skill activates.

| Skill                   | Domain            | Agents | Triggers                                           |
| ----------------------- | ----------------- | ------ | -------------------------------------------------- |
| `hyperskills:fullstack` | Web Development   | 4      | React, Next.js, APIs, databases, Tailwind          |
| `hyperskills:mobile`    | Mobile Apps       | 1      | React Native, Expo, iOS, Android                   |
| `hyperskills:ai`        | AI/ML Engineering | 5      | LLMs, RAG, embeddings, MLOps, computer vision      |
| `hyperskills:platform`  | Infrastructure    | 4      | Kubernetes, GitOps, CI/CD, data pipelines          |
| `hyperskills:security`  | Security Ops      | 2      | Pentesting, incidents, compliance, threat modeling |
| `hyperskills:quality`   | Testing & A11y    | 2      | Tests, accessibility, performance, code review     |
| `hyperskills:growth`    | Growth & Product  | 5      | ASO, viral loops, content, market research         |

## 🦋 Agents

Agents are invoked via the Task tool with `subagent_type="hyperskills:agent-name"`.

### Fullstack Development

| Agent                             | Specialty                                                              |
| --------------------------------- | ---------------------------------------------------------------------- |
| `hyperskills:frontend-developer`  | React 19, Server Components, React Compiler, TanStack Query, shadcn/ui |
| `hyperskills:backend-architect`   | API design, system architecture, auth patterns, database modeling      |
| `hyperskills:rapid-prototyper`    | MVP scaffolding, 6-day sprint delivery, trend integration              |
| `hyperskills:database-specialist` | Schema design, query optimization, migrations, replication             |

### Mobile Development

| Agent                            | Specialty                                                    |
| -------------------------------- | ------------------------------------------------------------ |
| `hyperskills:mobile-app-builder` | React Native New Architecture, Expo SDK 53+, NativeWind, EAS |

### AI/ML Engineering

| Agent                        | Specialty                                                                |
| ---------------------------- | ------------------------------------------------------------------------ |
| `hyperskills:ai-engineer`    | LLM integration, RAG pipelines, MCP servers, DSPy programmatic prompting |
| `hyperskills:mlops-engineer` | Model deployment, monitoring, feature stores, A/B testing infrastructure |
| `hyperskills:data-scientist` | Statistical analysis, A/B testing, predictive modeling, causal inference |
| `hyperskills:ml-researcher`  | Paper implementation, novel architectures, Flash Attention, MoE          |
| `hyperskills:cv-engineer`    | Object detection (YOLO, RT-DETR), segmentation (SAM), video analysis     |

### Platform Engineering

| Agent                           | Specialty                                                             |
| ------------------------------- | --------------------------------------------------------------------- |
| `hyperskills:platform-engineer` | GitOps (Argo CD/Flux), OpenTofu, Crossplane v2, OpenTelemetry         |
| `hyperskills:data-engineer`     | ETL/ELT pipelines, dbt, Airflow, Flink streaming, data quality        |
| `hyperskills:finops-engineer`   | Cloud cost optimization, FinOps framework, right-sizing, reservations |
| `hyperskills:git-wizard`        | Complex rebases, merge conflicts, lock files, encrypted secrets       |

### Security Operations

| Agent                            | Specialty                                                                 |
| -------------------------------- | ------------------------------------------------------------------------- |
| `hyperskills:security-architect` | Threat modeling, Zero Trust, SBOM/SLSA, eBPF (Tetragon/Falco), compliance |
| `hyperskills:incident-responder` | NIST IR framework, digital forensics, log analysis, recovery coordination |

### Quality Engineering

| Agent                                  | Specialty                                                              |
| -------------------------------------- | ---------------------------------------------------------------------- |
| `hyperskills:test-writer-fixer`        | Test creation, failure analysis, CI integration, coverage optimization |
| `hyperskills:accessibility-specialist` | WCAG 2.2, Playwright + Axe automation, screen reader testing           |

### Growth & Product

| Agent                             | Specialty                                                            |
| --------------------------------- | -------------------------------------------------------------------- |
| `hyperskills:growth-hacker`       | Viral loops, PLG patterns, referral systems, conversion optimization |
| `hyperskills:app-store-optimizer` | ASO strategy, keyword research, screenshot optimization, A/B testing |
| `hyperskills:content-strategist`  | Multi-platform content, SEO, repurposing workflows, video scripts    |
| `hyperskills:trend-researcher`    | TikTok trends, app store intelligence, competitive analysis          |
| `hyperskills:product-strategist`  | Feature prioritization, competitive intel, user feedback synthesis   |

## 🧪 SOTA Knowledge

Every skill is enhanced with cutting-edge techniques (research-backed, 2025-2026):

### Fullstack

- **React 19** — Server Components, React Compiler, `use()` hook
- **State** — TanStack Query v5, Zustand, jotai for atoms
- **UI** — shadcn/ui + Radix primitives, Tailwind v4, Base UI
- **Forms** — React Hook Form + Zod, Conform for progressive enhancement

### AI/ML

- **Prompting** — DSPy programmatic prompting (manual prompts are dead)
- **RAG** — Hybrid search, RAGAS evaluation, ColBERT late interaction
- **Fine-tuning** — LoRA/QLoRA, Unsloth, PEFT adapters
- **Serving** — vLLM, TensorRT-LLM, speculative decoding

### Platform

- **GitOps** — Argo CD, Flux v2, ApplicationSets, progressive delivery
- **IaC** — OpenTofu (not Terraform), Pulumi, Crossplane compositions
- **Observability** — OpenTelemetry everywhere, Grafana stack, eBPF tracing
- **Data** — dbt for transforms, Great Expectations for quality, Polars for speed

### Security

- **Runtime** — eBPF-based detection (Tetragon, Falco), runtime policies
- **Supply Chain** — SBOM generation, SLSA attestations, Sigstore signing
- **Compliance** — Automated evidence collection (Vanta/Drata patterns)
- **Zero Trust** — Identity-aware proxies, microsegmentation, SPIFFE/SPIRE

### Quality

- **Testing** — Playwright for E2E, Component Testing, Axe for a11y
- **Performance** — Core Web Vitals (INP focus), bundle analysis, edge caching
- **Code Review** — AI-assisted review patterns, semantic diff analysis

### Growth

- **PLG** — Product-led growth funnels, self-serve onboarding, usage-based pricing
- **Viral** — K-factor optimization, referral mechanics, UGC loops
- **Content** — Multi-platform repurposing, short-form video hooks, SEO clusters

## 📦 Structure

```
hyperskills/
├── .claude-plugin/
│   ├── plugin.json           # Claude Code manifest
│   └── marketplace.json      # Distribution index
├── agents/                    # 23 specialized subagents
├── skills/
│   ├── fullstack/
│   │   ├── SKILL.md          # Quick reference + triggers
│   │   ├── references/       # Deep documentation
│   │   └── examples/         # Production configs
│   ├── mobile/
│   ├── ai/
│   ├── platform/
│   ├── security/
│   ├── quality/
│   └── growth/
├── commands/                  # Slash commands
├── AGENTS.md                  # skills.sh registry
└── Makefile                   # Lint, format, validate
```

## 🪄 Commands

```bash
/hyperskills:prototype       # Scaffold a new project with best practices
/hyperskills:audit-security  # Run security audit on codebase
```

## 🌐 Compatibility

| Platform           | Installation                                       |
| ------------------ | -------------------------------------------------- |
| **Claude Code**    | `/plugin install hyperskills`                      |
| **Codex CLI**      | `npx skills add hyperb1iss/hyperskills -a codex`   |
| **Cursor**         | `npx skills add hyperb1iss/hyperskills -a cursor`  |
| **GitHub Copilot** | `npx skills add hyperb1iss/hyperskills -a copilot` |
| **Gemini CLI**     | `npx skills add hyperb1iss/hyperskills -a gemini`  |

## 🦋 Philosophy

These skills embody the Contains Studio methodology:

| Principle                        | What It Means                                                            |
| -------------------------------- | ------------------------------------------------------------------------ |
| **Ship in 6 days**               | Every feature fits a sprint. No multi-month projects.                    |
| **Research first**               | SOTA techniques, not outdated tutorials. Web search beats training data. |
| **Specialists over generalists** | Deep expertise wins. One agent per domain.                               |
| **Automate the boring**          | CI/CD, testing, security—if it can run automatically, it should.         |
| **Delight users**                | Whimsy matters. Error messages can be fun. Loading states can spark joy. |

## 🧪 Development

```bash
# Clone
git clone https://github.com/hyperb1iss/hyperskills.git
cd hyperskills

# Lint & format
make lint
make format

# Validate structure
make check

# Test locally
claude --plugin-dir .
```

## 💜 Origins

hyperskills evolved from the [Contains Studio agent ecosystem](https://github.com/hyperb1iss/agents)—59 specialized agents built for rapid app development. We consolidated them down to 23 essential agents, dropped the outdated ones (manual prompt engineering is dead, platform-specific social media bots are pointless), and enhanced everything with 2025-2026 SOTA techniques.

The original agents powered 6-day sprint cycles for shipping apps fast. Now they're available for everyone.

## License

Apache-2.0 — See [LICENSE](LICENSE)

---

<p align="center">
  Created by <a href="https://hyperbliss.tech">Stefanie Jane</a>
</p>

<p align="center">
  <a href="https://github.com/hyperb1iss">
    <img src="https://img.shields.io/badge/GitHub-hyperb1iss-181717?style=for-the-badge&logo=github" alt="GitHub">
  </a>
  <a href="https://bsky.app/profile/hyperbliss.tech">
    <img src="https://img.shields.io/badge/Bluesky-@hyperbliss.tech-1185fe?style=for-the-badge&logo=bluesky" alt="Bluesky">
  </a>
</p>
