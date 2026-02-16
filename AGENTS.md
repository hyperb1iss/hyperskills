# Hyperskills

Focused skills for things models don't already know. Compatible with the [skills.sh](https://skills.sh) open ecosystem.

## Installation

```bash
npx skills add hyperbliss/hyperskills --all
```

Or install specific skills:

```bash
npx skills add hyperbliss/hyperskills --skill orchestrate
npx skills add hyperbliss/hyperskills --skill security
npx skills add hyperbliss/hyperskills --skill git
npx skills add hyperbliss/hyperskills --skill tilt
```

## Skills

### Multi-Agent Orchestration (`hyperskills:orchestrate`)

Meta-orchestration patterns mined from 597+ real agent dispatches. Research swarms, epic parallel builds, wave dispatch, build-review-fix pipelines, multi-dimensional audits, and full project lifecycles.

### Security Operations (`hyperskills:security`)

Threat modeling (STRIDE), Zero Trust, SLSA supply chain security, OWASP Top 10, incident response phases, and compliance frameworks.

### Git Operations (`hyperskills:git`)

Decision trees for conflict resolution, rebase vs merge, undo operations. Lock file handling, SOPS encrypted files, and repository archaeology.

### Tilt Kubernetes Development (`hyperskills:tilt`)

CLI operations, Tiltfile authoring, live update patterns, build strategy selectors, debugging flows. Complete API reference and power patterns in progressive disclosure references.

## Usage

Invoke skills with `/hyperskills:<skill>`:

```bash
/hyperskills:orchestrate
/hyperskills:security
/hyperskills:git
/hyperskills:tilt
```

## License

MIT
