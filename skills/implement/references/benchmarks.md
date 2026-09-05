# Evaluating Implementation Workflows

Use this reference when comparing coding workflows or deciding whether a process rule earns its cost. The filename preserves existing links; the guidance concerns measurement rather than prescribing historical activity ratios.

## Retire Activity Counts as Targets

Earlier guidance listed corpus counts and ratios without a reproducible dataset, extraction method, or controlled comparison. Those figures cannot establish that reading a certain number of files, verifying every few edits, or using a fixed context percentage improves outcomes. Do not convert observational workflow frequencies into quality requirements.

Measure delivered behavior and the effort needed to achieve it. A failed check that prevents a regression may be valuable; a high test count or large agent fleet is not inherently productive.

## Compare the Whole System

Record the model, reasoning configuration, harness, tools, task input, repository revision, and environment. Change one meaningful factor at a time where feasible. Model and harness interact, so an older workaround deserves re-evaluation after a model upgrade.

| Dimension     | Useful evidence                                   | Misleading substitute                    |
| ------------- | ------------------------------------------------- | ---------------------------------------- |
| Correctness   | Required behavior and preserved existing behavior | Agent's claim that the work is complete  |
| Reliability   | Repeated trials and observed failure modes        | Best selected run                        |
| Efficiency    | Cost and elapsed time per successful outcome      | Tokens per second or raw tool-call count |
| Scope control | Necessary changed behavior and maintenance cost   | Fewer lines regardless of semantics      |
| Recovery      | Correct diagnosis and successful repair           | Number of retries                        |
| Handoff       | Another session resumes from recorded state       | Length of the summary                    |

Use representative tasks, including the failure modes the skill is meant to prevent. For skill changes, compare realistic requests with and without the changed guidance when the cost is warranted. Check task completion, unnecessary pauses, scope drift, incorrect tool use, and required verification. A Markdown validator proves syntax, not behavior.

Keep grader expectations aligned with the user request. Do not mark a valid alternative implementation wrong because the grader assumes an unstated file path or method. Conversely, do not let an agent weaken assertions or redefine completion to improve its score.

## Preserve Enough Context to Resume

Use artifact paths and concise checkpoints for information that must survive compaction. Record decisions and unresolved constraints; load implementation details when needed. No universal context-utilization percentage or scheduled reset interval is established here. Re-ground when state becomes uncertain, and test memory changes against actual resumption quality.

## Evidence and Limits

Sources opened 2026-09-04:

- [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (2026-01-09): evaluate environment outcomes with task-appropriate graders and multiple trials. Success metrics must match the task rather than a preferred trajectory.
- [Anthropic, Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (2025-09-29): describes selective context retrieval, compaction, and structured notes. These are engineering strategies, not a measured universal threshold for context use.
- [Gloaguen et al., Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988) (v2, 2026-06-23): reports that repository context files do not generally improve task success and increase inference cost in the evaluated settings, while remaining useful for non-standard coding practices. The paper studies repository context files, not this skill library or every future model. Use the result to motivate behavioral evaluation of instructions, not to discard useful local contracts.
- [Anthropic, Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) (2026-03-24): reports retiring a context-reset workaround after model improvements. Treat the case as a reason to retest scaffolding, not proof that resets or any particular evaluator arrangement always help.
