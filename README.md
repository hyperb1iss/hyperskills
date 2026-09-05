<h1 align="center">
  ⚡ hyperskills
</h1>

<p align="center">
  <strong>Focused skills for things capable agents still need to learn</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Skills-14-e135ff?style=for-the-badge&logo=anthropic&logoColor=white" alt="14 Skills">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-ff6ac1?style=for-the-badge" alt="MIT License"></a>
</p>

## What earns a skill

A model does not need a tutorial for every tool it touches. Hyperskills carries the parts that are easy to miss: how to preserve another worker's edits during Git surgery, distinguish a review finding from a plausible story, verify a generated artifact at its destination, or extract useful memory without turning an old transcript into new instructions.

The process skills help with decisions and evidence. They adapt to the task instead of prescribing agent counts, approval rituals, or a fixed pipeline. Domain skills remain where the operational details justify them: Git, Tilt, and terminal UI design. Use the installed tool's help and current official documentation for ordinary package management, linting, and type checking.

Skills load independently. [Sibyl](https://github.com/hyperb1iss/sibyl) adds durable project memory when available. Host permissions and the user's actual request govern execution; a skill does not create authorization or override a settled decision.

## Installation

### Claude Code

```text
/plugin marketplace add hyperb1iss/hyperskills
/plugin install hyperskills@hyperb1iss
```

### Skills CLI

```bash
npx skills add hyperb1iss/hyperskills --all
npx skills add hyperb1iss/hyperskills --skill implement
```

Use the installer's supported agent selection to choose your host. Check its current help rather than assuming every host has the same skill directory or invocation syntax.

### Local development

```bash
git clone https://github.com/hyperb1iss/hyperskills.git
cd hyperskills
make install
```

The installer links each skill into `~/.agents/skills` and `~/.claude/skills`. Existing directories are backed up before replacement. Installing a plugin or updating this checkout does not automatically remove older standalone copies of retired skills; inspect those copies before removing them.

## Composing skills

Start where the uncertainty is. A clear bug can go straight to implementation; an open product question benefits from exploration before a plan. The combinations below are examples.

| Situation                            | Useful combination                                          |
| ------------------------------------ | ----------------------------------------------------------- |
| Unresolved feature direction         | brainstorm, then research where facts decide the choice     |
| Large change with known requirements | plan, implement, independent review                         |
| Independent workstreams              | orchestrate with explicit ownership and integration         |
| PR review                            | hyper-pr-review; cross-model-review for another perspective |
| PR authoring                         | super-good-pr                                               |
| Prose cleanup                        | deslop with the artifact's existing voice and format        |
| Raster asset from another harness    | codex-imagegen                                              |
| Durable lessons from past sessions   | dream                                                       |

## Process skills

### `brainstorm`

Explore the problem and alternatives before committing to a design. Uses the Double Diamond as a flexible frame, separates requirements from assumptions, and identifies the experiment that would change the recommendation. Clear implementation requests do not need a brainstorming detour.

```text
/hyperskills:brainstorm
```

### `research`

Gather evidence for a question, from a targeted lookup to independent research lanes. Tracks source lineage, contradictions, and benchmark comparability. Synthesize as evidence arrives; deepen the investigation when an unresolved fact could change the answer.

```text
/hyperskills:research
```

### `plan`

Turn requirements into dependency-aware tasks with observable completion criteria. Keep tests with the behavior they verify, preserve deliberately open decisions, and give each worker enough context to resume without reconstructing the conversation.

```text
/hyperskills:plan
```

### `implement`

Make a focused change and verify the behavior where another component consumes it. Covers error diagnosis, shared-workspace ownership, meaningful test receipts, compatibility, and recovery. Verification grows with the uncertainty and consequences of the change.

```text
/hyperskills:implement
```

### `orchestrate`

Partition independent work, define ownership beyond file paths, and integrate results against the original request. Includes worker and reviewer briefs, lifecycle tracking, artifact verification, and honest handling of incomplete work. Agent count follows useful parallelism and available capacity.

```text
/hyperskills:orchestrate
```

### `cross-model-review`

Launch and consume an independent review of code, a specification, a diagnosis, or factual claims. Covers current CLI discovery, process handles, output capture, permissions, billing intent, and evidence-based finding disposition. A second model adds a perspective; agreement still needs proof.

```text
/hyperskills:cross-model-review
```

### `hyper-pr-review`

Conduct the review yourself. Trace changed behavior and actual callers, try to disprove each candidate, and report the trigger, impact, and evidence. Deep review adds deliberate coverage of rollout, security, and structural quality. Required checks that could not run produce an inconclusive verdict.

```text
/hyperskills:hyper-pr-review
```

### `codex-imagegen`

Delegate raster generation or editing when another harness needs Codex's image capability. Preserve reference roles and edit invariants, keep jobs and receipts distinct, and verify the delivered files. Prefer native image tools when already available; capability and billing depend on the configured environment.

```text
/hyperskills:codex-imagegen
```

### `super-good-pr`

Write and maintain PR descriptions around the problem, resulting behavior, and evidence a reviewer needs. Preserve human-authored sections and template requirements. Refresh claims when the artifact changes, and distinguish a rewritten commit identity from changed content.

```text
/hyperskills:super-good-pr
```

### `deslop`

Edit prose while preserving meaning, uncertainty, and the author's voice. Includes a protection-aware scanner, surface profiles, editing techniques, and a dated evidence catalog. Scanner candidates prompt judgment; stylistic patterns do not establish authorship.

```text
/hyperskills:deslop
```

### `dream`

Review authorized conversation history for decisions and recurring lessons that should survive a session. Separates visible evidence from speculation, preserves provenance, checks current state before storing claims, and keeps project scope and sensitive data boundaries intact.

```text
/hyperskills:dream
```

## Domain skills

### `git`

Handle rebases, stacked branches, conflict resolution, and shared worktrees. Preserve inspected remote expectations with explicit leases, compare rewrites using the appropriate evidence, and commit only owned staged content. Recovery begins by preserving the candidate state.

```text
/hyperskills:git
```

### `tilt`

Diagnose the path from file change to build, sync, process reload, and readiness. Covers Live Update ordering, resource dependencies, CI completion, and environment-sensitive operations. References hold the operational patterns that matter when a valid Tiltfile still does the wrong thing.

```text
/hyperskills:tilt
```

### `tui-design`

Design terminal interfaces around capabilities, state, input, and lifecycle. Covers layout and visual hierarchy alongside Unicode width, fallback rendering, keyboard access, resize behavior, and terminal restoration. Includes a visual catalog and examples from existing applications.

```text
/hyperskills:tui-design
```

## Maintaining the library

Metadata supports discovery; the entrypoint contains the essential decisions; references hold conditional detail. Short is useful when the procedure remains complete. A long reference is worthwhile only when an agent can find and use the relevant part.

Version 3.11 removes the `uv`, `ruff`, `ty`, and `uv-build` skills. Their generic tool guidance belongs in model knowledge and current official documentation, while copied version tables require maintenance without adding enough value.

The [September 2026 review](docs/library-review-2026-09.md) records the substantive changes and research limits. The [evaluation cases](evals/README.md) exercise task behavior and routing; schema validation alone cannot establish that a skill helps.

## Development

The checks use `uv` (Python and isolated PyYAML), Bash, and Perl. Markdown linting and formatting use the tools named in the Makefile.

```bash
make check      # Parse manifests, YAML frontmatter, and bundled references
make test       # Exercise malformed inputs and scanner regressions
make all        # Run both checks and tests
make lint       # Optional JSON, YAML, and Markdown lint tools
make format     # Format tracked Markdown and JSON
```

The validator checks concrete `references/`, `scripts/`, and `assets/` declarations in skill entrypoints. It does not execute examples, crawl external links, or grade agent behavior. Review reference contents and run relevant behavioral cases when changing a workflow.

See [AGENTS.md](AGENTS.md) for contribution guidance. Licensed under [MIT](LICENSE).

<p align="center">💜 Built by <a href="https://hyperbliss.tech">Hyperbliss Technologies</a></p>
