# Hyperskills Agents

Compatible with the [skills.sh](https://skills.sh) open ecosystem.

## Installation

```bash
npx skills add hyperbliss/hyperskills --all
```

Or install specific skills:

```bash
npx skills add hyperbliss/hyperskills --skill ai
npx skills add hyperbliss/hyperskills --skill fullstack
npx skills add hyperbliss/hyperskills --skill security
```

## Agent Registry

### Fullstack Development (`fullstack`)

- `frontend-developer` - React 19, Next.js, RSC patterns, Tailwind
- `backend-architect` - APIs, databases, system design, auth
- `rapid-prototyper` - MVP development in 6-day sprints
- `database-specialist` - Schema design, optimization, migrations

### Mobile Development (`mobile`)

- `mobile-app-builder` - React Native, Expo SDK 53, cross-platform

### AI/ML Engineering (`ai`)

- `ai-engineer` - LLM integration, RAG, MCP, DSPy
- `mlops-engineer` - Model deployment, monitoring, pipelines
- `data-scientist` - Analysis, A/B testing, predictive models
- `ml-researcher` - Paper implementation, novel architectures
- `cv-engineer` - Computer vision, object detection, segmentation

### Platform Engineering (`platform`)

- `platform-engineer` - GitOps, IaC, Kubernetes, observability
- `data-engineer` - Pipelines, ETL, data infrastructure
- `finops-engineer` - Cloud cost optimization, FinOps framework
- `git-wizard` - Complex rebases, merge conflicts, git archaeology

### Security Operations (`security`)

- `security-architect` - Threat modeling, secure design, compliance
- `incident-responder` - Incident handling, forensics, recovery

### Quality Engineering (`quality`)

- `test-writer-fixer` - Test creation, maintenance, CI integration
- `accessibility-specialist` - WCAG compliance, Playwright + Axe

### Growth & Product (`growth`)

- `growth-hacker` - Viral loops, PLG, acquisition experiments
- `app-store-optimizer` - ASO strategy, keyword research
- `content-strategist` - Multi-platform content, SEO, repurposing
- `trend-researcher` - Market research, viral opportunity identification
- `product-strategist` - Competitive intel, feature prioritization

## Stats

| Metric | Count |
|--------|-------|
| Skills | 7 |
| Agents | 22 |
| Commands | 2 |

## Usage

Skills auto-activate based on context. Agents are invoked via the Task tool:

```
Task(subagent_type="ai-engineer", prompt="Implement RAG pipeline...")
```

## License

MIT
