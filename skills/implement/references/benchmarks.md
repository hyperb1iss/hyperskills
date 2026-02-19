# Implementation Benchmarks & Archetypes

Quantitative data from 21,321 tracked operations across 64+ projects.

## Quantitative Benchmarks

| Metric | Value | Source |
|--------|-------|--------|
| Reads per code change | 0.8 | Sibyl (21k ops) |
| Searches per code change | 0.5 | Sibyl |
| Edits between verifications (sweet spot) | 2-3 | Sibyl + v2 |
| Changes per commit | 48.7 | Sibyl |
| Verifications per commit | 23.2 | Sibyl |
| Typecheck:Lint:Test ratio | 4.6:1.9:1 | Sibyl |
| Edit:Write ratio (mature codebase) | 9:1 | v2 |
| Verification failure rate | ~35% | v2 |
| Post-fix verification rate | 27% | Debugging (612 sessions) |
| Quick fix rate (1-2 iterations) | 42% | Debugging |
| Spiral rate (6+ iterations) | 42% | Debugging |
| Context overflow in spirals | 99% | Debugging |
| Sessions with tests | 90% | Sibyl |
| Exploration before first edit (10+ reads) | 31% | v2 |
| Agent survivorship in research swarms | 67-100% | Config/skills |

---

## Implementation Archetypes

### The Quick Fix

```
Read error -> Grep for pattern -> Read 2-3 files -> Edit 1-2 files -> Verify -> Commit
```

- **Budget:** 1-2 cycles, 5-20 edits
- **Verification:** One typecheck + one test run
- **When:** Bug with clear error, config change, typo fix

### The Feature Build

```
Orient (read existing patterns) -> Plan (task list) -> Implement layer-by-layer
  -> Verify per layer (typecheck + lint) -> Tests -> Commit
```

- **Budget:** 5-15 cycles, 50-200 edits
- **Verification:** Typecheck per layer, tests at end
- **When:** New endpoint, new UI component, new service integration

### The Research-First Build

```
Dispatch 3-7 research agents -> Synthesize findings -> Write spec/plan
  -> Implement in dependency order -> Verify -> Cross-model review -> Commit
```

- **Budget:** 10-30 cycles, 200-500 edits
- **Verification:** Per-wave verification + final cross-model review
- **When:** Unfamiliar domain, greenfield feature, technology evaluation needed

### The Parallel Epic

```
Research swarm -> Task graph with dependencies -> Wave dispatch (3-7 agents per wave)
  -> Collect outputs -> Integration -> Full verification suite -> Commit
```

- **Budget:** 30-100+ cycles, 500-1000+ edits
- **Verification:** Per-agent verification + integration verification + full suite
- **When:** Multi-system feature, major refactor, new project inception

---

## Context Engineering Budget

| Item | Tokens |
|------|--------|
| Baseline system + CLAUDE.md | ~20k |
| Usable budget (200k window) | ~180k |
| Target utilization | 40-60% |
| Context rot threshold | ~15-20 iterations |

### Context Preservation Strategies

- **Subagent delegation:** Research and verbose operations in separate context windows
- **Just-in-time loading:** Glob/Grep to discover, Read on demand (don't pre-load everything)
- **`/clear` between unrelated tasks:** Kitchen-sink sessions kill performance
- **After compaction:** Always preserve modified file list and test commands

---

## The Ralph Loop (Edit-Verify-Fix Cycle)

346 cycles detected across 27/30 Sibyl sessions:

| Profile | Pattern | Frequency |
|---------|---------|-----------|
| **Quick fix** | 3 changes -> LINT -> 1 fix | Most common |
| **Standard** | 5.8 changes -> verify -> 5.7 fixes | Average |
| **Type cascade** | 2 changes -> TC -> 15 fixes | Most expensive |

- Lint triggers most cycles (~140 of 346)
- Typecheck triggers fewest but costliest cycles
- Average cycle: 5.8 initial changes, then 5.7 fixes to clean up
