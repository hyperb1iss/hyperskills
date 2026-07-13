---
name: dream
description: Use this skill to review recent conversations and consolidate learnings into Sibyl. Activates on mentions of dream, dreaming, consolidate memory, review conversations, what did we learn, sleep cycle, reflect on sessions, consolidate knowledge, memory maintenance, nightly review, digest sessions, transcript mining, session archaeology, or dream mode.
---

# Dream: Conversation Review & Knowledge Consolidation

Bio-inspired two-phase sleep cycle that reviews Claude Code and Codex conversations, extracts structured knowledge, and consolidates it into Sibyl. Like biological dreaming: NREM consolidates, REM discovers.

**Core insight:** inline capture gets the gotchas — as of Jul 2026 the Remember beat fires at volume, per-slice, mid-session. Dreams hunt what no single session can see: gotchas that repeat across sessions, instruction phrases that persist in the prompt stream, cross-project connections, and the blind spots of otherwise good capture (harness friction, the user's unblock one-liners). Dreams are the backstop and the telescope, not the primary channel.

**How to read this skill:** the phases below describe the rhythm of a useful dream cycle, not a procedure to march through. Quick naps compress most of it, deep sleeps stretch it out. The non-negotiable bits are extraction quality (Sibyl entries that meet the bar in `references/extraction-guide.md`) and dedup discipline (every write checked against existing entries). Process shape adapts; quality bar doesn't.

## The Shape

```dot
digraph dream {
    rankdir=LR;
    node [shape=box];

    "ORIENT" -> "HARVEST" -> "NREM: Consolidate" -> "REPORT";
    "NREM: Consolidate" -> "REM: Explore" [label="deep mode"];
    "REM: Explore" -> "REPORT";
}
```

### Depth Modes

| Mode           | Sessions                    | Focus                               | When                                         |
| -------------- | --------------------------- | ----------------------------------- | -------------------------------------------- |
| **Quick nap**  | Last 1-3                    | Extract from today's work           | End of day, `/dream quick`                   |
| **Full sleep** | Last 5-15                   | Standard consolidation cycle        | Default `/dream`                             |
| **Deep sleep** | All since last dream        | Cross-project synthesis + REM       | `/dream deep`                                |
| **Lucid**      | Specific session(s)         | Targeted extraction                 | `/dream <session-id>`                        |
| **Mining run** | Whole corpus (weeks-months) | Fan-out miners → merge → skill-diff | User-dispatched; composes with `orchestrate` |

A mining run is the at-scale form: parallel miners over the transcript corpus, findings merged, consolidation landing as skill and contract patches as much as graph entities.

---

## Phase 1: ORIENT

Get the lay of the land before harvesting. Re-processing already-dreamed sessions wastes tokens and creates duplicate entries.

### Common moves

1. **Check dream state:** when did the last cycle run? The dream-report entry in Sibyl is the cross-host anchor:

   ```bash
   sibyl search "dream report" --limit 3
   ```

2. **Discover conversation sources:**

   ```bash
   # Claude Code sessions across ALL projects (last 7 days)
   find ~/.claude/projects -name "*.jsonl" -not -path "*/subagents/*" -mtime -7 -exec ls -lt {} + | head -30

   # Codex rollouts
   find ~/.codex/sessions -name "rollout-*.jsonl" -mtime -7 -exec ls -lt {} + | head -30
   ```

3. **Count the harvest:** how many sessions since the last dream, which projects were active, any notably long or complex sessions? (file size > 100KB = rich conversation)

4. **Set dream scope** based on depth mode and available sessions.

---

## Phase 2: HARVEST

Read conversations and identify extractable knowledge. The trick is reading targeted segments rather than entire files; most session content is routine, and only specific patterns carry transferable signal.

### What to look for

| Content Type                   | Where to Find                                          | What to Extract                                                           |
| ------------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------- |
| **User corrections**           | User messages following assistant errors               | Anti-patterns, wrong assumptions                                          |
| **User unblock one-liners**    | Short user messages that resolve a stall               | The incantation is the learning ("need to run `./gx setup env --legacy`") |
| **Technical decisions**        | Assistant text blocks with rationale                   | Decision + alternatives considered                                        |
| **Taste directives**           | User standing rules stated mid-task                    | Durable preferences ("preserve the pretty PR body")                       |
| **Debugging chains**           | Sequences of failed → fixed attempts                   | Error patterns, root causes                                               |
| **Evidence-trust calibration** | Green signals that lied (tests passed, behavior broke) | Which check missed what, and the compensating verification                |
| **Tool limits hit**            | Tool hangs or failures at a size/shape boundary        | The exact boundary as a condition, not a ban                              |
| **Retired risks**              | Investigations that cleared a suspected problem        | Dated evidence closing the risk — no lingering fake TODOs                 |
| **Tool invocations**           | `tool_use` blocks (Bash, Edit, etc.)                   | Commands that worked, error patterns                                      |
| **Architecture discussion**    | Longer text blocks with design reasoning               | Patterns, system relationships                                            |
| **Thinking blocks**            | `type: "thinking"` content                             | Reasoning chains, hidden insights                                         |

### Extraction mechanics

Grep scores, python extracts. Claude Code JSONL nests content arrays inside message objects, so line-level grep like `'"role":"user"'` matches assistant messages that quote user content — use grep only for signal counts, python parsing for the actual pull. High-signal fields: `ai-title` (session topic at a glance), `message.model` (which model authored the session), Codex `session_meta` (cwd, branch, model). Schemas, discovery commands, and working extraction snippets for both formats live in `references/conversation-formats.md`.

For promising sessions (high correction count, long duration, many tool calls), read key segments more deeply using `Read` with offset/limit on the JSONL.

### Signal Scoring

Prioritize sessions for deep reading:

| Signal                                 | Score | How to Detect                                                                          |
| -------------------------------------- | ----- | -------------------------------------------------------------------------------------- |
| User corrections present               | +3    | grep for negation words in user messages                                               |
| Gotcha also seen in a previous session | +3    | the repeat is the capture trigger — write it as a gate, test, or invariant, not a note |
| Multiple error-fix cycles              | +2    | tool_use errors followed by successful retries                                         |
| Cross-project references               | +2    | mentions of other project paths                                                        |
| Architecture/design discussion         | +2    | grep for design keywords                                                               |
| New library/tool adoption              | +2    | grep for "install", "add", package names                                               |
| Long session (>50 messages)            | +1    | line count of JSONL                                                                    |
| Simple Q&A session                     | -1    | short session with no tool calls                                                       |

Process top-scored sessions first; quick nap mode usually caps at the top 3. Low-signal sessions can be skipped entirely — extracting from a Q&A session about syntax produces noise, not knowledge. Mind the skew: capture discipline favors domain learnings, but the repeats that burn sessions are usually harness and tooling friction (cwd drift, path bases, quoting, flag shapes). That friction clears the bar.

---

## Phase 3: NREM, Structured Consolidation

Transform raw conversation signal into structured Sibyl entities. This is where the quality bar matters most: a duplicate-laden, vague-titled Sibyl is worse than a smaller, sharper one.

### Write-time discipline

- **Date-stamp volatile claims.** Versions, SOTA, and live state carry an as-of date so future recall can age them — a 25-day-old "latest version" memory nearly caused a wrong downgrade. Recalled memory is a lead, not gospel; write entries that age visibly.
- **Supersede, don't append.** When a finding contradicts an existing entry, correct the old entry in place — including why the obvious fix is a dead end — and title corrections as corrections ("Correction: retain local Supabase PVCs in Tilt").
- **The quality test:** could a future session turn this into a gate, a constraint, or an executable recipe? If not, it's trivia. Full bar and worked examples in `references/extraction-guide.md`.

### Extraction categories

| Category                        | Sibyl home                     | What qualifies                                                                                                                                     |
| ------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Decisions**                   | `episode`, category `decision` | Technical choices with trade-offs: library selection, architecture, API design. Record rationale, alternatives, and provenance (who decided, when) |
| **Patterns**                    | `pattern`                      | Reusable approaches that worked. The bar: would this be useful in a different project?                                                             |
| **Corrections / anti-patterns** | `error_pattern`                | Mistakes that got corrected — the user said "that's wrong," or something broke and was debugged to root cause                                      |
| **Rules**                       | `rule`                         | Hard constraints discovered through experience. "Always X when Y." "Never Z because W."                                                            |
| **Open questions / tensions**   | `episode`, category `tension`  | Raised but unanswered; contradictions between approaches; deferred decisions                                                                       |

Verb and flag shapes live in the `sibyl` skill and the live `--help` — CLI surfaces drift under skills, and installs differ. When a kind or flag is rejected, adapt the capture to what the install accepts rather than dropping it.

### Deduplication

Before writing, check for existing entries — the value of the graph collapses when duplicates accumulate. Dedup the extraction set against itself first (multiple sessions repeat the same insight), then check each survivor against Sibyl:

```bash
sibyl search "[entity title keywords]" --limit 5
```

| Finding                 | Action                                                      |
| ----------------------- | ----------------------------------------------------------- |
| No similar entries      | Create new entity                                           |
| Similar but older entry | Update existing if new info supersedes, or add relationship |
| Exact duplicate         | Skip, log in dream report                                   |
| Contradictory entry     | Create tension entity linking both                          |

Track what was written for the dream report.

### When a write fails

The extraction still ships: paste it verbatim into the dream report flagged **NOT captured**, queue it for flush (pending-writes queue, or file memory as the backstop), and hand the user the exact flush command. The next cycle reports which parked learnings finally landed. An unwritten memory that's visible is a queue; one that's silent is a loss.

---

## Phase 4: REM, Creative Exploration

Only in `deep` mode and mining runs. Find unexpected connections across projects, the cross-pollination phase that biological REM is named after.

### Connection Discovery

Pull the graph wide (`sibyl search` sweeps per kind — patterns, error patterns, unresolved tensions; walk `sibyl explore related` from the anchors it surfaces), then look for:

1. **Pattern reuse:** a pattern from project A that would solve a problem in project B
2. **Contradictory approaches:** project A does X one way, project B does it differently — which is right?
3. **Shared infrastructure gaps:** multiple projects hitting the same limitation
4. **Knowledge transfer:** something learned in one domain that applies to another

Record each connection as an episode (category `cross-project`) naming both projects and the implication.

### Prompt-Stream Telemetry

The user's own prompts are encoding telemetry. Diff recurring instruction phrases against the contract and skills, in both directions:

| Signal                           | Reading                                                                                  |
| -------------------------------- | ---------------------------------------------------------------------------------------- |
| Phrase vanished month-over-month | The encoding landed ("commit as you go" went 11 → 2 → 0 → 0 as the contract absorbed it) |
| Phrase persists across months    | Codify-next candidate                                                                    |

Candidates still pass the net-new-delta gate — a repeat proves demand, not absence. The gap is often execution consistency, not missing rules.

### Staleness Detection

Scan the graph for aging entities (kind-scoped `sibyl search` sweeps; exact verb shapes live in the `sibyl` skill). For anything older than ~90 days: is the project still active, has the technology moved, does the pattern still hold? Resolve with the same write-time maintenance moves applied graph-wide — supersede in place, retire the risk with dated evidence, or tag `stale,needs-review` for a human.

---

## Phase 5: REPORT

The report serves two audiences: the user (what landed) and future dreams (which check this entry to avoid re-processing). Four fields are required; everything else is optional:

- **Coverage:** sessions reviewed, projects, time span — what the next cycle's orient checks
- **Dedup receipts:** entities created / updated / duplicates skipped — the counts that prove dedup ran
- **Highlights:** the 2-3 findings worth a human's attention
- **Parked writes:** learnings that failed to write, verbatim, flagged NOT captured, with the flush command

Record the report itself in Sibyl as an episode (category `dream-report`, tagged `dream`) — it is the anchor the next cycle's orient searches for.

### Beyond the Graph

When a pattern is process-shaped and cross-project, its durable home may be a skill or the contract rather than the graph. Gate every proposed skill edit on net-new delta: re-read the target skill first — most of what a run rediscovers is already written down.

---

## Quick Nap Mode

For fast end-of-day processing:

1. Find today's sessions (Claude + Codex)
2. Grep for corrections and errors only
3. Extract the top 3-5 findings
4. Write to Sibyl
5. One-paragraph dream report

**Skip:** the whole REM phase — cross-project analysis, prompt-stream telemetry, staleness detection.

---

## Integration Notes

### Sibyl Is the Primary Store

Everything goes to Sibyl, not memory/\*.md files. Sibyl provides:

- Semantic search (vector + BM25)
- Relationship modeling (entity connections)
- Temporal awareness (when things were learned)
- Cross-project visibility (shared graph)
- Multi-machine access (network service)

Memory files are only updated for critical session-level behaviors that need to be in the host's native context window.

### Transcript Archaeology

The harvest mechanics double as work-product recovery: grep `message.model` for authorship, extract Write/Edit tool calls to see exactly which files a session produced. This has recovered PR bodies whose /tmp originals died with a reboot.

### Conversation Formats

See `references/conversation-formats.md` for:

- Claude Code JSONL schema (TranscriptMessage types, content blocks)
- Codex rollout JSONL schema (session_meta, response_item, event_msg, turn_context)
- Session discovery, extraction snippets, and useful grep patterns for each format

### Extraction Quality

See `references/extraction-guide.md` for:

- What makes a good vs bad extraction, including the gate/constraint/recipe test
- Sibyl entity type selection guide
- Deduplication strategies
- Examples of high-quality dream extractions across the full taxonomy

---

## Anti-Patterns

| Anti-Pattern                             | Fix                                                                  |
| ---------------------------------------- | -------------------------------------------------------------------- |
| Reading entire JSONL files               | Grep first, read targeted segments                                   |
| Extracting trivial Q&A                   | Only extract non-obvious insights with transfer value                |
| Writing to memory/\*.md instead of Sibyl | Sibyl is the primary store, memory files are a narrow exception      |
| Skipping dedup check                     | Always search Sibyl before writing, duplicates degrade graph quality |
| Dream without orient                     | Always check when last dream ran, avoid re-processing                |
| Extracting everything from every session | Score sessions first, process high-signal ones deeply                |
| Dropping a capture on a rejected flag    | Check live `--help`, adapt the kind to what the install accepts      |
| Losing a failed write silently           | Park it verbatim in the report and queue the flush                   |
| Ignoring Codex sessions                  | Codex conversations contain valuable engineering knowledge too       |

---

## What This Skill is NOT

- **Not a replacement for Auto Dream.** Auto Dream manages memory/\*.md housekeeping. This skill extracts knowledge into Sibyl.
- **Not real-time.** Dreams process past conversations. For live knowledge capture, use the Remember beat (`sibyl` skill) at the moment of learning.
- **Not a full conversation replay.** We extract signal, not transcripts. Sibyl stores insights, not chat logs.
- **Not automatic (yet).** Invoke with `/dream`. Future: SessionEnd hook for automatic NREM processing.
