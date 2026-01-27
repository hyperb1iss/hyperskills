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

### Fullstack Development (`hyperskills:fullstack`)

- `hyperskills:frontend-developer` - React 19, Next.js, RSC patterns, Tailwind
- `hyperskills:backend-architect` - APIs, databases, system design, auth
- `hyperskills:rapid-prototyper` - MVP development in 6-day sprints
- `hyperskills:database-specialist` - Schema design, optimization, migrations

### Mobile Development (`hyperskills:mobile`)

- `hyperskills:mobile-app-builder` - React Native, Expo SDK 53, cross-platform

### AI/ML Engineering (`hyperskills:ai`)

- `hyperskills:ai-engineer` - LLM integration, RAG, MCP, DSPy
- `hyperskills:mlops-engineer` - Model deployment, monitoring, pipelines
- `hyperskills:data-scientist` - Analysis, A/B testing, predictive models
- `hyperskills:ml-researcher` - Paper implementation, novel architectures
- `hyperskills:cv-engineer` - Computer vision, object detection, segmentation

### Platform Engineering (`hyperskills:platform`)

- `hyperskills:platform-engineer` - GitOps, IaC, Kubernetes, observability
- `hyperskills:data-engineer` - Pipelines, ETL/ELT, dbt, Airflow, streaming
- `hyperskills:finops-engineer` - Cloud cost optimization, FinOps framework
- `hyperskills:git-wizard` - Complex rebases, merge conflicts, git archaeology

### Security Operations (`hyperskills:security`)

- `hyperskills:security-architect` - Threat modeling, secure design, compliance
- `hyperskills:incident-responder` - Incident handling, forensics, recovery

### Quality Engineering (`hyperskills:quality`)

- `hyperskills:test-writer-fixer` - Test creation, maintenance, CI integration
- `hyperskills:accessibility-specialist` - WCAG compliance, Playwright + Axe

### Growth & Product (`hyperskills:growth`)

- `hyperskills:growth-hacker` - Viral loops, PLG, acquisition experiments
- `hyperskills:app-store-optimizer` - ASO strategy, keyword research
- `hyperskills:content-strategist` - Multi-platform content, SEO, repurposing
- `hyperskills:trend-researcher` - Market research, viral opportunity identification
- `hyperskills:product-strategist` - Competitive intel, feature prioritization

## Stats

| Metric   | Count |
| -------- | ----- |
| Skills   | 7     |
| Agents   | 23    |
| Commands | 2     |

## Usage

Invoke skills with `/hyperskills:<skill>`:

```bash
/hyperskills:fullstack
/hyperskills:ai
/hyperskills:security
```

Agents are invoked via the Task tool:

```
Task(subagent_type="hyperskills:ai-engineer", prompt="Implement RAG pipeline...")
```

## License

Apache-2.0
