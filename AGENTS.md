# Hyperskills — Contributor Guide

How to add new skills to this plugin. Read this before creating or modifying any skill.

## Project Structure

```
hyperskills/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest (version, keywords, metadata)
│   └── marketplace.json     # skills.sh marketplace listing
├── skills/
│   ├── brainstorm/
│   │   └── SKILL.md
│   ├── plan/
│   │   └── SKILL.md
│   ├── research/
│   │   └── SKILL.md
│   ├── orchestrate/
│   │   └── SKILL.md
│   ├── implement/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── benchmarks.md
│   ├── codex-review/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── prompts.md
│   ├── cross-model-review/
│   │   ├── SKILL.md
│   │   └── references/
│   │       └── prompts.md
│   ├── dream/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── conversation-formats.md
│   │       └── extraction-guide.md
│   ├── security/
│   │   └── SKILL.md
│   ├── git/
│   │   └── SKILL.md
│   ├── tilt/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── api-reference.md
│   │       └── patterns.md
│   ├── agent-sandbox/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── crds.md
│   │       ├── patterns.md
│   │       └── clients.md
│   ├── tui-design/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── visual-catalog.md
│   │       └── app-patterns.md
│   ├── uv/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── docker-ci.md
│   │       ├── resolution.md
│   │       └── configuration.md
│   ├── ruff/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── rules.md
│   │       └── configuration.md
│   ├── ty/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── type-system.md
│   │       └── migration.md
│   └── uv-build/
│       └── SKILL.md
├── CLAUDE.md -> AGENTS.md   # Claude reads the same contributor guide
├── AGENTS.md                # This file — contributor guide
├── LICENSE
└── README.md
```

## Design Philosophy

**Only build skills for things models don't already know.** Claude is already good at writing code, explaining concepts, and general problem-solving. Skills should encode:

- **Procedural knowledge** — multi-step workflows that require specific ordering
- **Decision trees** — when to choose X over Y based on situational factors
- **Reference material** — API surfaces, Unicode catalogs, framework-specific patterns
- **Hard-won patterns** — gotchas, anti-patterns, and real-world failure modes

If the model can already do it well without guidance, don't write a skill for it.

## Adding a New Skill

### Step 1: Create the Directory

```bash
mkdir -p skills/<skill-name>
touch skills/<skill-name>/SKILL.md
```

Add `references/` only if the skill needs detailed reference material that would bloat the main SKILL.md beyond ~3,000 words:

```bash
mkdir -p skills/<skill-name>/references
```

### Step 2: Write SKILL.md

Every SKILL.md has two parts: YAML frontmatter and markdown body.

#### Frontmatter (Required)

```yaml
---
name: skill-name
description: Use this skill when [specific triggers]. Activates on mentions of [keyword1], [keyword2], [keyword3], or [keyword4].
---
```

**Description rules:**

- Start with "Use this skill when" followed by concrete scenarios
- Include "Activates on mentions of" with specific trigger words/phrases
- Be generous with triggers — list 8-12 keywords that should activate the skill
- Include both formal terms ("threat modeling") and casual phrasing ("security review")

**Good example:**

```yaml
description: Use this skill for complex git operations including rebases, merge conflict resolution, cherry-picking, branch management, or repository archaeology. Activates on mentions of git rebase, merge conflict, cherry-pick, git history, branch cleanup, git bisect, worktree, force push, or complex git operations.
```

**Bad example:**

```yaml
description: Helps with git stuff.
```

#### Body Structure

The body is what Claude reads when the skill triggers. Structure it for fast scanning:

```markdown
# Skill Title

One-paragraph summary of what this skill provides and its core insight.

## Section 1: [Core Content]

Tables, decision trees, and procedures. Prefer tables over prose:

| Situation | Action |
| --------- | ------ |
| X         | Do Y   |
| Z         | Do W   |

## Section 2: [More Content]

...

## Anti-Patterns

| Anti-Pattern   | Fix             |
| -------------- | --------------- |
| Common mistake | How to avoid it |

## What This Skill is NOT

- Not a replacement for [X]
- Not required for [Y]
```

**Body guidelines:**

- Target 1,500-3,000 words. Move anything beyond that to `references/`
- Use tables over prose — they scan faster and waste fewer tokens
- Include decision trees for branching logic
- Add anti-pattern tables — knowing what NOT to do is as valuable as knowing what to do
- End with "What This Skill is NOT" to prevent misuse
- Flowcharts use Graphviz `dot` format in fenced code blocks (```dot)

### Step 3: Add Reference Files (Optional)

For skills with extensive reference material, use progressive disclosure:

```
skills/<skill-name>/
├── SKILL.md                    # Core procedures (~2,000 words)
└── references/
    ├── api-reference.md        # Full API surface
    ├── patterns.md             # Advanced patterns
    └── visual-catalog.md       # Lookup tables, catalogs
```

**Reference files:**

- No YAML frontmatter needed — just plain markdown
- Can be large (2,000-10,000+ words)
- Only loaded into context when Claude determines it needs them
- Must be referenced from SKILL.md so Claude knows they exist

**Reference from SKILL.md like this:**

```markdown
## References

For detailed API documentation, consult `references/api-reference.md`.
For advanced configuration patterns, see `references/patterns.md`.
```

**When to use references vs inline:**

| Content Type                    | Where         |
| ------------------------------- | ------------- |
| Core workflow steps             | SKILL.md body |
| Decision trees                  | SKILL.md body |
| Quick-reference tables          | SKILL.md body |
| Anti-patterns                   | SKILL.md body |
| Full API surfaces               | `references/` |
| Unicode/visual catalogs         | `references/` |
| Advanced patterns (>20 entries) | `references/` |
| Real-world app galleries        | `references/` |

### Step 4: Update Plugin Metadata

After creating the skill, update these files:

#### `.claude-plugin/plugin.json`

Add relevant keywords to the `keywords` array:

```json
{
  "keywords": ["existing-keyword", "new-skill-keyword-1", "new-skill-keyword-2"]
}
```

Bump the version following semver:

- New skill = minor version bump (e.g., 3.0.0 → 3.1.0)
- Skill content update = patch bump (e.g., 3.1.0 → 3.1.1)
- Breaking changes (rename/remove skill) = major bump

#### `AGENTS.md` / `CLAUDE.md`

`CLAUDE.md` is a symlink to `AGENTS.md`. Edit `AGENTS.md`; Claude sees the same file.

Add an install command:

```bash
npx skills add hyperbliss/hyperskills --skill <skill-name>
```

Add a skill description section:

```markdown
### Skill Title (`hyperskills:<skill-name>`)

One-sentence description of what it provides.
```

Add to the usage section:

```bash
/hyperskills:<skill-name>
```

### Step 5: Validate

Before committing, verify:

- [ ] `skills/<name>/SKILL.md` exists with valid YAML frontmatter
- [ ] Frontmatter has both `name` and `description` fields
- [ ] Description includes specific trigger phrases (8-12 keywords)
- [ ] Body is under 5,000 words (ideally 1,500-3,000)
- [ ] All files referenced from SKILL.md actually exist
- [ ] No duplicate content between SKILL.md and reference files
- [ ] Tables used instead of prose where possible
- [ ] Anti-patterns section included
- [ ] "What This Skill is NOT" section included
- [ ] `plugin.json` keywords updated
- [ ] `AGENTS.md` updated with install command, description, and usage
- [ ] Version bumped in `plugin.json`

## Existing Skill Inventory

| Skill                | Tokens | References | Domain                                           |
| -------------------- | ------ | ---------- | ------------------------------------------------ |
| `brainstorm`         | ~2,500 | none       | Process — ideation                               |
| `plan`               | ~2,800 | none       | Process — decomposition                          |
| `research`           | ~3,200 | none       | Process — knowledge gathering                    |
| `orchestrate`        | ~4,000 | none       | Process — multi-agent dispatch                   |
| `implement`          | ~4,200 | 1 file     | Process — implementation                         |
| `codex-review`       | ~2,000 | 1 file     | Process — Codex-specific review (Claude → Codex) |
| `cross-model-review` | ~2,400 | 1 file     | Process — bidirectional cross-model review       |
| `dream`              | ~2,300 | 2 files    | Process — conversation memory consolidation      |
| `security`           | ~1,500 | none       | Domain — security ops                            |
| `git`                | ~1,200 | none       | Domain — git operations                          |
| `tilt`               | ~2,500 | 2 files    | Domain — Kubernetes dev                          |
| `agent-sandbox`      | ~2,000 | 3 files    | Domain — agent-sandbox Kubernetes operator       |
| `tui-design`         | ~3,000 | 2 files    | Domain — terminal UI                             |
| `uv`                 | ~3,000 | 3 files    | Domain — Python package management               |
| `ruff`               | ~2,800 | 2 files    | Domain — Python linting & formatting             |
| `ty`                 | ~2,500 | 2 files    | Domain — Python type checking                    |
| `uv-build`           | ~2,500 | none       | Domain — Python build backend                    |

## Skill Categories

When adding a new skill, it should fit one of these categories:

**Process skills** — HOW to approach a class of work:

- `brainstorm`, `plan`, `research`, `orchestrate`, `implement`, `codex-review`, `cross-model-review`, `dream`
- These tend to be workflow-heavy with phases and decision gates

**Domain skills** — specialized knowledge for a specific technology or practice:

- `security`, `git`, `tilt`, `agent-sandbox`, `tui-design`, `uv`, `ruff`, `ty`, `uv-build`
- These tend to be reference-heavy with decision trees and lookup tables

## Writing Style

- **Imperative form:** "Search Sibyl first" not "You should search Sibyl first"
- **Tables over prose:** Decision trees, comparisons, and reference data in table format
- **Graphviz for flows:** Use ```dot fenced code blocks for process diagrams
- **Concrete over abstract:** "Run `git rebase origin/main`" not "rebase your branch"
- **Date volatile info:** "As of Feb 2026" — skills spoil like research
- **No fluff:** Every sentence should teach something or guide a decision

## Common Mistakes

| Mistake                                                | Fix                                                         |
| ------------------------------------------------------ | ----------------------------------------------------------- |
| Vague description with no trigger words                | Add 8-12 specific keywords after "Activates on mentions of" |
| Entire skill is >5,000 words in SKILL.md               | Split into SKILL.md (core) + references/ (detail)           |
| Prose paragraphs explaining options                    | Convert to decision tree tables                             |
| Duplicating what models already know                   | Only encode non-obvious procedural knowledge                |
| No anti-patterns section                               | Add one — knowing pitfalls is half the value                |
| Missing "What This Skill is NOT"                       | Add scope boundaries to prevent misuse                      |
| Reference files exist but aren't mentioned in SKILL.md | Add a References section pointing to them                   |
| Forgetting to update plugin.json and AGENTS.md         | Always update both after adding/changing skills             |
