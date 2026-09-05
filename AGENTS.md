# Hyperskills Contributor Guide

Read this before adding or changing a skill. Hyperskills supplies non-obvious procedural knowledge for capable agents. Model names and tool versions change; useful constraints, evidence, and operational failure modes should survive them.

## Design Contract

A skill earns its place when it changes a decision the model would otherwise get wrong. Keep fragile operation ordering, meaningful decision criteria, and reusable checks. Remove generic tutorials, repeated host policy, unsupported performance claims, and historical anecdotes presented as universal rules.

User instructions take precedence over skill guidelines. Skills preserve the requested scope and existing authorization; they do not invent approval gates, silently expand external actions, or bypass host permissions. Use the current tool schema for dispatch, waits, and capabilities.

Treat the repository as shared space. Check status before edits, inspect existing diffs, and own explicit paths. Follow the user's commit and publishing policy. Do not modify installed user configuration as a side effect of editing a skill.

## Repository Map

```text
hyperskills/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── skills/
│   ├── brainstorm/SKILL.md
│   ├── plan/SKILL.md
│   ├── research/SKILL.md
│   ├── orchestrate/
│   │   ├── SKILL.md
│   │   └── references/dispatch-briefs.md
│   ├── implement/
│   │   ├── SKILL.md
│   │   └── references/{benchmarks,recovery}.md
│   ├── cross-model-review/
│   │   ├── SKILL.md
│   │   └── references/{prompts,failure-recovery,cli-flags}.md
│   ├── hyper-pr-review/
│   │   ├── SKILL.md
│   │   └── references/{lenses,thermonuclear}.md
│   ├── codex-imagegen/SKILL.md
│   ├── super-good-pr/SKILL.md
│   ├── deslop/
│   │   ├── SKILL.md
│   │   ├── scripts/{slopscan.pl,selftest.sh}
│   │   └── references/ # catalog, profiles, craft, evidence, fixtures
│   ├── dream/
│   │   ├── SKILL.md
│   │   └── references/{conversation-formats,extraction-guide}.md
│   ├── git/SKILL.md
│   ├── tilt/
│   │   ├── SKILL.md
│   │   └── references/{api-reference,patterns}.md
│   └── tui-design/
│       ├── SKILL.md
│       └── references/{visual-catalog,app-patterns}.md
├── scripts/validate_skills.py
├── tests/test_validate_skills.py
├── evals/README.md
├── docs/library-review-2026-09.md
├── Makefile
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
├── README.md
└── LICENSE
```

The brace notation groups filenames; it is not a literal path.

## Skill Inventory

| Skill                | References      | Purpose                                      |
| -------------------- | --------------- | -------------------------------------------- |
| `brainstorm`         | none            | Explore unresolved direction                 |
| `plan`               | none            | Decompose requirements and dependencies      |
| `research`           | none            | Gather and adjudicate evidence               |
| `orchestrate`        | 1               | Coordinate independent work and integration  |
| `implement`          | 2               | Implement and verify behavior                |
| `cross-model-review` | 3               | Dispatch and consume independent reviews     |
| `hyper-pr-review`    | 2               | Conduct evidence-based review                |
| `codex-imagegen`     | none            | Delegate raster asset generation             |
| `super-good-pr`      | none            | Author and maintain PR descriptions          |
| `deslop`             | 4 plus fixtures | Edit prose without semantic or voice damage  |
| `dream`              | 2               | Consolidate authorized conversation evidence |
| `git`                | none            | Perform complex Git operations               |
| `tilt`               | 2               | Diagnose build, sync, reload, and readiness  |
| `tui-design`         | 2               | Design terminal behavior and presentation    |

Process skills cover approaches to work: brainstorm, plan, research, orchestrate, implement, cross-model-review, hyper-pr-review, codex-imagegen, super-good-pr, deslop, and dream.

Domain skills cover specialized operational knowledge: git, tilt, and tui-design. Ordinary package management, linting, and type checking use current tool help and official documentation; the former Astral skills are retired.

## Authoring

Every skill directory contains `SKILL.md` with valid YAML frontmatter:

```yaml
---
name: skill-name
description: Use this skill when a specific workflow needs its specialized guidance. Activates on concrete task language.
---
```

The name matches its directory, uses lowercase letters, digits, and single hyphens, and is at most 64 characters. The description is a nonempty string of at most 1,024 characters. Describe the capability and realistic triggers; add exclusions when they prevent likely misrouting. Keyword counts are not a quality measure.

Keep the entrypoint as short as the task permits. Under 5,000 words is the repository ceiling, not a target. Put conditional detail in `references/` as soon as it helps retrieval. Link each supporting file where it becomes useful. A self-contained skill needs no reference directory.

Write imperative guidance for the non-obvious moves. Use tables for comparisons and decisions, prose for connected reasoning, and examples for fragile mechanics. Include relevant anti-patterns and a clear scope boundary, conventionally titled "What This Skill is NOT". Graphviz `dot` is the default for internal workflow diagrams; choose a diagram only when it explains something prose cannot efficiently show.

Label local conventions, observed incidents, and external evidence distinctly. A research claim needs a source, date or version where relevant, and limits. Do not generalize one model's benchmark into a permanent agent-count, token, confidence, or review-round quota. If a new model makes a workaround unnecessary, retire it after checking the behavior it protected.

Scripts belong in `scripts/` when deterministic execution improves reliability. Explain dependencies and side effects. Never present generated files or a model's self-report as proof without inspecting the actual output.

## Validation and Evaluation

Run `make check` for manifests, parsed YAML, required metadata, size limits, and concrete bundled references. The validator inspects all skill directories, including new untracked skills. Run `make test` for validator and scanner regressions. The checks use uv to run isolated Python with PyYAML, plus Bash and Perl.

For a workflow change, select realistic cases from [evals/README.md](evals/README.md) or add a case for a newly discovered failure. Evaluate the produced artifact and actions, not whether the response repeats a heading or phrase. Include a negative routing case when changing discovery metadata. A task requiring additional live access or publishing uses an isolated fixture or stops at a reviewable artifact.

For broad changes, obtain independent verification on the final scope. A contributor's self-check is useful evidence but is not independent review. Record unavailable checks as unavailable. Do not report a model-performance improvement without a comparable baseline, repeat trials, and an outcome-based grader.

## Publishing Metadata

Update the inventory and README when a skill is added, removed, renamed, or materially changes scope. Update the plugin description and keywords when the public surface changes. Keep `CLAUDE.md` as a symlink to this guide.

Version changes follow the user-facing surface:

| Change                                        | Version increment |
| --------------------------------------------- | ----------------- |
| Existing skill fixes or content updates       | Patch             |
| Skill addition, removal, or rename            | Minor             |
| Plugin architecture or manifest layout change | Major             |

A local version bump is not permission to tag, release, or push to main. Keep temporary research notes and private session material out of commits. A requested public review report is a deliverable; an internal planning scratchpad is not.

## Maintenance Questions

Before adding another instruction, ask what failure it prevents, whether that failure still occurs, and whether a tool or test can enforce the invariant better. Check the new instruction against the other skills that commonly compose with it. Prefer one clear owner for a procedure over several almost-identical copies.

The [Agent Skills specification](https://agentskills.io/specification) defines the metadata format. [OpenAI's Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) explains why conflicting skill instructions deserve attention. Both were checked on 2026-09-04; current host behavior remains authoritative for execution details.
