# Evidence and limits

Reviewed 2026-09-04. Anthropic's [multi-agent research report](https://www.anthropic.com/engineering/multi-agent-research-system) supports independent research decomposition and explicit briefs, while reporting significant token overhead and weaker fit for heavily dependent work. Its internal results describe a particular 2025 model/harness combination, not a universal swarm-size prescription.

For evaluating competing approaches, Anthropic's [agent evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) distinguishes trials, graders, trajectories, and environment outcomes. Apply those distinctions when judging evidence; do not equate a polished report with a validated result.

Reviewed again 2026-10-27 during the library audit; no change to the sources.

## 2026-11-06 review

Thariq Shihipar (Claude Code, Anthropic), [Unhobbling Claude: the difficulties and processes of building agents](https://www.youtube.com/watch?v=FlHfhwQaAFM), a talk at a Browserbase event published 2026-09-25, read from the auto-generated transcript on 2026-11-06: telling the model "I know nothing about this provider, do a blind-spot pass" changes the deliverable from doing the task to mapping the unknown unknowns, because by default the model does the work it was asked for. The table row follows that.

Limits: one engineer's account of the Claude Code harness and of eval transcripts, with no numbers and no controlled comparison. His observation that the Claude 5 models want smaller context and no examples concerns tool descriptions in that harness, not skill prose.
