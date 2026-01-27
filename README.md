# Hyperskills

Elite AI agent skills for rapid product development. Ship faster with specialized agents that know the cutting edge.

## Skills

| Skill | Domain | Agents |
|-------|--------|--------|
| **fullstack** | Web development | frontend-developer, backend-architect, rapid-prototyper, database-specialist |
| **mobile** | Mobile apps | mobile-app-builder |
| **ai** | AI/ML engineering | ai-engineer, mlops-engineer, data-scientist, ml-researcher, cv-engineer |
| **platform** | Infrastructure | platform-engineer, data-engineer, finops-engineer |
| **security** | Security ops | security-architect, incident-responder |
| **quality** | Testing & a11y | test-writer-fixer, accessibility-specialist |
| **growth** | Growth & product | growth-hacker, app-store-optimizer, content-strategist, trend-researcher, product-strategist |

## Installation

### Claude Code

```bash
# From the plugin marketplace
claude /plugin install hyperskills

# Or from GitHub
claude /plugin install github:hyperb1iss/hyperskills
```

### skills.sh Ecosystem

```bash
npx add-skill hyperb1iss/hyperskills
```

### Manual

```bash
git clone https://github.com/hyperb1iss/hyperskills.git
ln -s $(pwd)/hyperskills/skills ~/.claude/skills/hyperskills
```

## Usage

Skills auto-activate based on context. When you're working on React code, the fullstack skill loads. When you mention "deploy to kubernetes", the platform skill activates.

You can also invoke skills directly:

```
/fullstack - Web development assistance
/mobile - Mobile app development
/ai - AI/ML engineering
/platform - Infrastructure and DevOps
/security - Security operations
/quality - Testing and accessibility
/growth - Growth and product strategy
```

## What Makes Hyperskills Different

### SOTA Knowledge (2026)

Every skill is enhanced with cutting-edge techniques:

- **fullstack**: React 19, Server Components, React Compiler, TanStack Query, shadcn/ui + Base UI
- **mobile**: React Native New Architecture, Expo SDK 53+, Hermes engine
- **ai**: DSPy programmatic prompting, MCP integration, RAG patterns, LoRA/QLoRA, RAGAS evaluation
- **platform**: GitOps (Argo CD/Flux), OpenTofu/Pulumi, Crossplane v2, OpenTelemetry, FinOps
- **security**: Agentic pentesting, eBPF (Tetragon/Falco), Zero Trust, SBOM/SLSA
- **quality**: Playwright + Axe automation, Core Web Vitals (INP), AI code review
- **growth**: PLG patterns, viral loops, UGC strategy, micro-influencer tactics

### Layered Knowledge

```
SKILL.md (Quick reference, auto-activation triggers)
    ↓
agents/ (Specialized subagents for complex tasks)
    ↓
references/ (Deep-dive documentation)
    ↓
examples/ (Production-ready configs, copy-paste code)
```

### Multi-Platform

Works with Claude Code, Codex CLI, Cursor, and any agent supporting the skills.sh ecosystem.

## Philosophy

- **Ship fast**: 6-day sprint mentality, MVPs over perfection
- **Stay current**: Research-backed, constantly updated
- **Be practical**: Real production patterns, not academic exercises
- **Automate everything**: CI/CD, testing, security - if it can be automated, it should be

## Contributing

PRs welcome. Keep skills focused, include examples, cite sources.

## License

Apache-2.0
