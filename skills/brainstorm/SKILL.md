---
name: brainstorm
description: Use this skill when exploring an open product or architecture question before choosing an approach. Activates on mentions of brainstorm, ideate, design session, explore options, what should we build, how should we approach, let's think about, new project, architecture decision, or design exploration. Skip it for a clear implementation request.
---

# Collaborative Brainstorming

Turn uncertainty into a useful choice or a focused experiment.

The user's instructions take precedence over this skill; carry existing authorization forward and do not add approval gates.

## Choose the Work Shape

| Situation                                  | Useful output                                            |
| ------------------------------------------ | -------------------------------------------------------- |
| The user wants open exploration            | Distinct directions, concrete tradeoffs, open questions  |
| The problem is clear, the mechanism is not | A recommendation and the evidence that would overturn it |
| One assumption determines feasibility      | A small test of that assumption before any design        |
| Approach chosen, implementation authorized | Continue into implementation                             |
| The user asks why something happens        | Diagnose the cause before designing a fix                |

## Ground the Question

Recall prior decisions through the installed Sibyl skill when configured (`sibyl context "<decision>" --intent plan`), and recheck any volatile claim it returns. Find the nearest existing instance and the prior work before generating alternatives.

Translate taste into examples and observations. For "smooth," identify the interaction and visible delay. For "gorgeous," inspect the reference and name the composition, motion, or typography worth preserving. Quantification helps where a metric represents the experience; a proxy metric does not replace the experience itself. A reference the user supplies is the specification: match it before reinterpreting it, and when a concept could move, show it moving.

Treat the user's hunch as a hypothesis: a decisive check can confirm part of it and reject the rest, so report both. Do not downgrade an explicit "use X" to a preference because it was written casually; if it conflicts with feasibility, say so before designing around it.

## Compare the Alternatives That Matter

Add an unconventional option only when the obvious ones share an untested assumption.

| Approach    | What improves            | Carrying cost                     | Main uncertainty           | Decisive check           |
| ----------- | ------------------------ | --------------------------------- | -------------------------- | ------------------------ |
| [Mechanism] | [User or system outcome] | [Maintenance, runtime, migration] | [What could invalidate it] | [Experiment or evidence] |

## Test the Uncertainty Before Polishing

Pick the next move by its power to change the decision; a rough prototype often settles more than another design paragraph.

| Evidence gap                                  | Next move                                                           |
| --------------------------------------------- | ------------------------------------------------------------------- |
| An API or model capability may have changed   | Read current primary docs and inspect the installed version         |
| Performance determines feasibility            | Test a representative workload against a baseline and resource caps |
| Several independent domains affect the choice | Delegate bounded research when permitted, or batch the reads        |
| Stakeholders value different outcomes         | Surface the value tradeoff to the user                              |
| A favored approach has weak support           | Seek a concrete counterexample or failure condition                 |

Reviewer agreement is not proof, since reviewers may share training, sources, or framing. Settle consequential disagreements with code, sources, or an experiment, and say when evidence stays inconclusive.

## Decide and Preserve the Reason

Recommend the best-supported direction with its main tradeoff and next action, or keep exploration open when that is the deliverable.

For a durable decision, record the choice, rationale, rejected alternative worth remembering, evidence, and reconsideration trigger in configured project memory. Preserve deliberately open decisions and user corrections verbatim when paraphrase would narrow them.

Route unresolved factual questions to `research`, complex execution to `plan`, and a clear bounded change to `implement`; these are optional compositions, not a mandatory pipeline.

## Evidence

Reviewed 2026-09-04 and 2026-10-27; sources and their limits are in `references/evidence.md`.

## Anti-Patterns

| Anti-pattern                                | Better move                                     |
| ------------------------------------------- | ----------------------------------------------- |
| Brainstorm before every code edit           | Explore only unresolved direction               |
| Ask the user to reconfirm known constraints | Carry prior authorization and decisions forward |
| Offer options that differ only cosmetically | Compare different mechanisms or tradeoffs       |
| Polish an approach with an untested premise | Run the feasibility check first                 |
| Turn an anecdote into a universal rule      | Retain the mechanism and state its conditions   |

## What This Skill is NOT

- A prerequisite for implementation, debugging, or routine fixes.
- A requirement to produce a spec, a fixed option count, or a final approval question.
- A substitute for the user's product judgment or current technical evidence.
