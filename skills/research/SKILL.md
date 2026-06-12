---
name: research
description: Use this skill when gathering knowledge at scale before making decisions - technology evaluation, SOTA analysis, codebase archaeology, competitive analysis, or any investigation requiring multiple sources. Activates on mentions of research, investigate, evaluate options, what's the best, compare alternatives, state of the art, deep dive, explore the landscape, or find out how.
---

# Multi-Agent Research

Wave-based knowledge gathering with deferred synthesis. Mined from 300+ real research dispatches: the pattern that consistently produces actionable intelligence.

**Core insight:** Research breadth-first, synthesize after. Conclusions drawn from the first three results miss nuance the fourth wave would have surfaced. Deploying agents in waves and accumulating findings before synthesizing produces sharper recommendations.

**How to read this skill:** the wave structure below is a shape, not a procedure. Quick mode skips most of it. Standard research uses one wave plus targeted follow-ups. Deep dives genuinely need the full pattern. Calibrate to the question, not the framework.

## The Shape

```dot
digraph research {
    rankdir=TB;
    node [shape=box];

    "1. PRIME" [style=filled, fillcolor="#e8e8ff"];
    "2. WAVE 1: Broad Sweep" [style=filled, fillcolor="#ffe8e8"];
    "3. GAP ANALYSIS" [style=filled, fillcolor="#fff8e0"];
    "4. WAVE 2+: Targeted" [style=filled, fillcolor="#ffe8e8"];
    "5. SYNTHESIZE" [style=filled, fillcolor="#e8ffe8"];
    "6. DECIDE & RECORD" [style=filled, fillcolor="#e8e8ff"];

    "1. PRIME" -> "2. WAVE 1: Broad Sweep";
    "2. WAVE 1: Broad Sweep" -> "3. GAP ANALYSIS";
    "3. GAP ANALYSIS" -> "4. WAVE 2+: Targeted";
    "4. WAVE 2+: Targeted" -> "3. GAP ANALYSIS" [label="still gaps", style=dashed];
    "3. GAP ANALYSIS" -> "5. SYNTHESIZE" [label="coverage sufficient"];
    "5. SYNTHESIZE" -> "6. DECIDE & RECORD";
}
```

---

## Phase 1: PRIME

Lean on existing knowledge before spawning agents. Re-running research that already lives in Sibyl burns tokens and produces duplicate entries.

### Common moves

- **Search Sibyl first:** `sibyl search "<research topic>"`, `sibyl search "<related technology>"`, `sibyl search "<prior decision in this area>"`. Surface what's already known before generating new findings.
- **Check for staleness.** Fast-moving topics (frameworks, models, cloud services) usually warrant re-research even when Sibyl has recent entries; treat the existing knowledge as a baseline. Stable topics with recent entries often don't need a fresh pass at all.
- **Sharpen the research question.** "Research databases" is too vague to dispatch on. "Compare PostgreSQL vs CockroachDB for multi-region write-heavy workloads with <10ms p99 latency" gives agents enough scope to do useful work.
- **Calibrate the research budget** to the decision the research is feeding:

   | Depth          | Agents | Time      | When                                         |
   | -------------- | ------ | --------- | -------------------------------------------- |
   | **Quick scan** | 2-3    | 2-5 min   | Known domain, just need latest info          |
   | **Standard**   | 5-10   | 10-15 min | Technology evaluation, architecture options  |
   | **Deep dive**  | 10-30  | 20-40 min | Greenfield decisions, SOTA analysis          |
   | **Exhaustive** | 30-60+ | 40-90 min | New project inception, competitive landscape |

### Source quality contract

This bit is non-negotiable: the value of research collapses when claims rest on stale blog posts. Specific claim types deserve specific source standards:

| Claim type              | Preferred source                                 |
| ----------------------- | ------------------------------------------------ |
| Current version         | Package registry, release page, or official CLI  |
| CLI flags / config keys | Official docs or local `--help` output           |
| Security frameworks     | OWASP, NIST, SLSA/OpenSSF, CIS, ISO, PCI sources |
| Cloud/provider behavior | Provider docs and current changelog              |
| Research papers / SOTA  | Paper, benchmark repo, or authors' artifact      |
| Community health        | Repository activity plus issue/release cadence   |

When primary sources disagree with secondary ones, trust the primary source and note the discrepancy. Date volatile facts explicitly, and prefer commands/sources the next agent can rerun over screenshots that go stale.

---

## Phase 2: WAVE 1: Broad Sweep

Deploy the first wave of agents across the full research surface. The goal is breadth; accept that some agents will produce mediocre output, that's what gap analysis is for.

### What good agent prompts have

Vague prompts produce vague research. Each agent benefits from:

- **One specific topic** (not "research everything about X")
- **An output file path** (no ambiguity about where to write)
- **Search hints** (include year: "search [topic] 2026")
- **8-12 numbered coverage items** that scope the research precisely
- **Source quality guidance** ("prefer official docs and GitHub repos over blog posts")

### Wave 1 Template

```markdown
Research [SPECIFIC_TOPIC] for [PROJECT/DECISION].

Create a research doc at docs/research/[filename].md covering:

1. Current state (latest version, recent changes)
2. [Specific capability A relevant to our use case]
3. [Specific capability B]
4. [Integration with our stack: list specific technologies]
5. Performance characteristics / benchmarks
6. Known limitations and gotchas
7. Community health (stars, activity, maintenance)
8. Comparison with alternatives (name 2-3 specific alternatives)

Use WebSearch for current information. Include dates on all facts.
Cite sources with URLs.
```

### Deployment notes

- **Use the host's fan-out verb.** Claude Code: parallel background `Agent` calls. Codex: `spawn_agent`. Pi (pi-nova pack): the `dispatch` tool with `"mode": "parallel"` researcher tasks — keep each task narrow, source-quality explicit, and output-oriented.
- **Background by default.** Research agents have no inter-dependencies, so foreground execution serializes work that should run in parallel.
- **3-4 seconds between dispatches** avoids rate limiting in practice. Tighter cadences sometimes work, sometimes hit limits, so pace yourself.
- **One file per agent.** Shared outputs create write contention and lose attribution.
- **Group by theme** when researching many topics. 12 separate dispatches become 3-4 thematic clusters with clearer synthesis later.

### Coverage Strategy

For technology evaluations, cover these dimensions:

| Dimension       | Question                          |
| --------------- | --------------------------------- |
| **Capability**  | Does it do what we need?          |
| **Performance** | Is it fast enough?                |
| **Ecosystem**   | Does it integrate with our stack? |
| **Maturity**    | Is it production-ready?           |
| **Community**   | Will it be maintained in 2 years? |
| **Cost**        | What does it cost at our scale?   |
| **Migration**   | How hard is it to adopt/abandon?  |

---

## Phase 3: GAP ANALYSIS

After Wave 1, look for what's missing before synthesizing. Premature synthesis is the most common research failure: the answer feels obvious after three docs and turns out to be wrong after eight.

### What to look for

- **Coverage gaps**: dimensions the wave didn't touch, missing comparisons, questions raised but not answered
- **Contradictions**: agents reaching different conclusions on the same question (often signal for verification agents)
- **Bias signals**: all-positive findings (suspicious, look for failure cases), only-official-docs (need community experience), same sources cited repeatedly (need source diversity)

### Decision Point

| Finding                        | Action                                |
| ------------------------------ | ------------------------------------- |
| Good coverage, minor gaps      | Synthesize now, note gaps             |
| Significant gaps               | Deploy Wave 2 targeted agents         |
| Contradictory findings         | Deploy verification agents to resolve |
| Entirely new direction emerged | Deploy Wave 2 in new direction        |

---

## Phase 4: WAVE 2+: Targeted Research

Fill specific gaps identified in the analysis. Wave 2 agents differ from Wave 1 in shape:

- **Smaller scope**: one specific question per agent
- **Higher quality bar**: "find production experience reports, not just docs"
- **Cross-reference prompts**: "Agent X found [claim], verify against [alternative source]"
- **Deep reads**: "Read the full README and API docs for [library], not just the landing page"

### When to stop

Stop deploying waves when the research question can be answered with confidence, when additional agents would produce diminishing returns, when key claims have 2+ independent sources, or when the user signals "enough, let's decide."

Three waves is usually the practical ceiling. Past that, more research rarely sharpens the answer; it usually means the question itself needs reframing.

---

## Phase 5: SYNTHESIZE

**Combine all findings into actionable intelligence. This is where the magic happens.**

### Synthesis Structure

```markdown
## Research: [Topic]

### TL;DR

[2-3 sentences. The answer, not the journey.]

### Recommendation

[Clear choice with justification. Don't hedge, pick one.]

### Options Evaluated

| Option | Fit | Maturity | Perf | Ecosystem | Verdict         |
| ------ | --- | -------- | ---- | --------- | --------------- |
| A      | ... | ...      | ...  | ...       | Best for [X]    |
| B      | ... | ...      | ...  | ...       | Best for [Y]    |
| C      | ... | ...      | ...  | ...       | Avoid: [reason] |

### Key Findings

1. [Most important finding with source]
2. [Second most important]
3. [Third most important]

### Risks & Gotchas

- [Known issue or limitation]
- [Migration complexity]
- [Hidden cost]

### Sources

- [Source 1](url): [what it contributed]
- [Source 2](url): [what it contributed]
```

### Synthesis principles

- **Lead with the recommendation.** Forcing the reader to wade through findings to find the answer is the most common synthesis failure.
- **Separate facts from opinions.** "PostgreSQL supports JSONB" (fact) vs "PostgreSQL is better for this use case" (opinion backed by evidence). Both are useful; conflating them isn't.
- **Include dissenting evidence.** If one source contradicts the recommendation, name it. Cherry-picked synthesis is worse than no synthesis.
- **Date everything.** "As of [month] [year], [library] is at v4.2." Research spoils fast.
- **Note confidence level.** "High confidence: well-documented" / "Low confidence: based on one blog post" gives the reader the calibration they need.

---

## Phase 6: DECIDE & RECORD

**Lock in the decision and capture it for future sessions.**

### Actions

1. **Present the synthesis** to the user with a clear recommendation

2. **Record in Sibyl:**

   ```
   sibyl add "Research: [topic]" "Evaluated [options]. Chose [X] because [reasons]. Key risk: [Y]. Sources: [primary URLs]. Date: [today]."
   ```

3. **Archive research docs**: keep the wave outputs for reference:
   - If in a project: `docs/research/[topic]/`
   - If general knowledge: Sibyl learning entry is sufficient

4. **Exit to next action:**

   | Next Step                  | When                                             |
   | -------------------------- | ------------------------------------------------ |
   | `/hyperskills:brainstorm`  | Research surfaced multiple viable approaches     |
   | `/hyperskills:plan`        | Decision made, ready to decompose implementation |
   | `/hyperskills:orchestrate` | Decision made, work is parallelizable            |
   | Direct implementation      | Research confirmed a simple path                 |

---

## Quick Research Mode

For focused questions that don't need the full wave protocol:

1. **Search Sibyl** (always)
2. **2-3 targeted searches** (WebSearch + WebFetch on key URLs)
3. **Synthesize inline** (no separate docs)
4. **Record if non-obvious** (Sibyl learning)

**Use when:** "What's the latest version of X?", "Does Y support Z?", "What's the recommended way to do W?"

---

## Research Patterns by Type

### Technology Evaluation

```
Wave 1: Official docs + GitHub README for each option (parallel)
Wave 2: Production experience + benchmarks (parallel)
Synthesize: Comparison matrix + recommendation
```

### Codebase Archaeology

```
Wave 1: Explore agents mapping each subsystem (parallel)
Wave 2: Grep for specific patterns / usage (parallel)
Synthesize: Architecture diagram + dependency map
```

### SOTA Analysis

```
Wave 1: WebSearch for latest papers, blog posts, releases (parallel)
Wave 2: Deep read the most relevant 3-5 sources (parallel)
Synthesize: What's genuinely novel vs rehashed + recommendation
```

### Competitive Landscape

```
Wave 1: Feature matrix for each competitor (parallel)
Wave 2: Pricing, community size, trajectory (parallel)
Synthesize: Positioning matrix + gap analysis
```

---

## Anti-Patterns

| Anti-Pattern                         | Fix                                                                             |
| ------------------------------------ | ------------------------------------------------------------------------------- |
| Synthesizing after Wave 1 only       | Wait for gap analysis, premature conclusions miss nuance                        |
| 50 agents with "research everything" | Specific scope per agent, vague prompts produce vague results                   |
| Only official documentation          | Include community experience, docs show intent, community shows reality         |
| No dates on findings                 | Date everything, research spoils faster than produce                            |
| No recommendation                    | Force a decision, "more research needed" is only valid with a specific question |
| Researching what Sibyl already knows | Always prime first, don't burn tokens re-discovering known patterns             |

---

## What This Skill is NOT

- **Not a substitute for reading code.** If the answer is in the codebase, read the codebase.
- **Not an infinite loop.** Max 3 waves. If that's not enough, reframe the question.
- **Not required for known domains.** If you already know the answer, just say so and cite your knowledge.
- **Not a delay tactic.** Research serves a decision. If no decision follows, the research was waste.
