---
name: brainstorm
description: Use this skill when exploring an open product or architecture question before choosing an approach. Activates on mentions of brainstorm, ideate, design session, explore options, what should we build, how should we approach, let's think about, new project, architecture decision, or design exploration. Skip it for a clear implementation request.
---

# Collaborative Brainstorming

Turn uncertainty into a useful choice or a focused experiment. Explore only the questions that could change the design. A clear implementation request already supplies direction; act on it without manufacturing a brainstorm or approval gate.

The user's instructions take precedence over this skill's guidelines. Preserve their constraints and existing authorization. Resolve routine design details with judgment; ask only when missing information materially changes the outcome and cannot be inferred.

## Choose the Work Shape

| Situation                                                 | Useful output                                                        |
| --------------------------------------------------------- | -------------------------------------------------------------------- |
| The user wants open exploration                           | Distinct directions with concrete tradeoffs and unresolved questions |
| The problem is clear but the mechanism is uncertain       | A recommendation and the evidence that would overturn it             |
| One assumption determines feasibility                     | A small test of that assumption before elaborating designs           |
| The approach is selected and implementation is authorized | Continue into implementation                                         |
| The user asks why something happens                       | Diagnose the cause before designing a fix                            |

## Ground the Question

Read the relevant code, artifact, or workflow and recall prior decisions. When Sibyl is configured, use its installed skill for current commands (`sibyl context "<decision>" --intent plan`). Memory supplies leads; inspect current evidence before reusing a volatile claim.

Name the intended experience or behavior, the constraint that matters most, and what remains unknown. Treat the user's hunch as a hypothesis worth checking, not a claim to rubber-stamp. A decisive check can confirm part of the hunch and reject the rest; report both.

Translate taste into examples and observations. For "smooth," identify the interaction and visible delay. For "gorgeous," inspect the reference and name the composition, motion, or typography worth preserving. Quantification helps where a metric represents the experience; a proxy metric does not replace the experience itself.

Distinguish explicit requirements from inferred preferences. Do not downgrade "use X" to a preference merely because the user wrote casually. If the instruction conflicts with feasibility, explain the conflict and resolve it before choosing an incompatible design.

## Explore the Alternatives That Matter

The Double Diamond offers a useful rhythm: widen the problem frame, narrow it, explore solutions, choose. Revisit the frame when evidence changes it. No phase requires a separate artifact or confirmation.

Generate alternatives along meaningful dimensions: ownership of state, migration cost, runtime behavior, user effort, or reversibility. Different names for the same mechanism do not create real choice. Consider reuse, configuration, or removing the need when those paths still meet the requested outcome. Include an unconventional direction when the obvious options share an untested assumption; do not invent a wildcard to fill a slot.

Compare viable options in the dimensions relevant to this decision:

| Approach    | What improves            | Carrying cost                     | Main uncertainty           | Decisive check           |
| ----------- | ------------------------ | --------------------------------- | -------------------------- | ------------------------ |
| [Mechanism] | [User or system outcome] | [Maintenance, runtime, migration] | [What could invalidate it] | [Experiment or evidence] |

Keep ambition and mechanism separate. Simplifying the machinery should preserve the useful destination. A small implementation that proves only connectivity may miss the actual product; an elaborate one may bury it. Use expected lifetime and likely change boundaries to judge architecture, rather than equating fewer lines with better design.

Before extending a design, ask where each responsibility belongs. A decision repeated across callers may need one owner. A wrapper may instead be enforcing a valuable boundary. Remove indirection after understanding its contract, not because forwarding looks trivial.

## Test the Uncertainty Before Polishing

Choose the next action by its ability to change the decision. A compatibility check, representative benchmark, or rough interaction prototype can settle more than another design paragraph.

| Evidence gap                                  | Next move                                                                    |
| --------------------------------------------- | ---------------------------------------------------------------------------- |
| An API or model capability may have changed   | Open current primary documentation and inspect the installed version         |
| Performance determines feasibility            | Test a representative workload with a baseline and explicit resource limits  |
| Several independent domains affect the choice | Delegate bounded research when permitted, or batch independent reads locally |
| Stakeholders value different outcomes         | Surface the actual value tradeoff for the user                               |
| A favored approach has weak support           | Seek a concrete counterexample or failure condition                          |

Independent opinions can expose assumptions, but agreement is not proof. Reviewers may share training, sources, or framing. Resolve consequential disagreements through code, source material, or an experiment. State when evidence remains inconclusive.

## Decide and Preserve the Reason

Recommend the best-supported direction with its principal tradeoff and the next action. Keep exploration open when that is the requested deliverable; do not force a build decision prematurely. Continue authorized work once the direction is clear. A remaining product or risk decision belongs with the user, but implementation details do not require a new consent question.

For a durable decision, record the choice, rationale, rejected alternative worth remembering, evidence, and condition that would trigger reconsideration. Preserve deliberately open decisions and user corrections verbatim when paraphrase would narrow them. Use configured project memory rather than creating duplicate decision ledgers.

Route unresolved factual questions to `research`, complex execution to `plan`, and a clear bounded change to `implement`. These are optional compositions, not a mandatory pipeline.

## Evidence and Limits

Reviewed 2026-09-04. The [Design Council's Double Diamond](https://www.designcouncil.org.uk/resources/the-double-diamond/) describes iterative divergence and convergence; it does not prescribe option counts or divide judgment between humans and models. Treat it as a design aid, not an effectiveness benchmark.

The [OpenAI Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) recommends explicit instruction precedence and follow-through because conflicting skill guidance can cause unnecessary pauses. Apply that to workflow clarity without assuming every host exposes the same capabilities.

## Anti-Patterns

| Anti-pattern                                | Better move                                     |
| ------------------------------------------- | ----------------------------------------------- |
| Brainstorm before every code edit           | Explore only unresolved direction               |
| Ask the user to reconfirm known constraints | Carry prior authorization and decisions forward |
| Offer options that differ only cosmetically | Compare different mechanisms or tradeoffs       |
| Treat reviewer consensus as validation      | Check the claim against independent evidence    |
| Polish an approach with an untested premise | Run the feasibility check first                 |
| Turn an anecdote into a universal rule      | Retain the mechanism and state its conditions   |

## What This Skill is NOT

- A prerequisite for implementation, debugging, or routine fixes.
- A requirement to produce a spec, a fixed number of options, or a final approval question.
- A substitute for the user's product judgment or current technical evidence.
