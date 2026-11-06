# Evidence and limits

Reviewed 2026-09-04. Anthropic's [March 2026 harness report](https://www.anthropic.com/engineering/harness-design-long-running-apps) describes outcome-oriented specifications and negotiated verification criteria, while observing that repeated evaluation can also increase implementation complexity. It is an engineering case study, not proof that every project needs a planner-generator-evaluator pipeline.

The procedures here use that distinction: preserve a testable contract and adapt the execution path. Evaluate planning changes through resulting work and correction cost, not the size of the plan.

Reviewed again 2026-10-27 during the library audit; no change to the sources.

## 2026-11-06 review

Thariq Shihipar (Claude Code, Anthropic), [Unhobbling Claude: the difficulties and processes of building agents](https://www.youtube.com/watch?v=FlHfhwQaAFM), a talk at a Browserbase event published 2026-09-25, read from the auto-generated transcript on 2026-11-06: the model no longer needs a markdown plan to keep itself on track, humans do read the plan, long markdown plans are hard for them, and rich artifacts with questions beside diagrams and snippets read better where the host renders them. The resumability paragraph follows that. The unsaid-constraint bullet and the recorded-call sentence follow his observation that runs diverge at the judgment call the prompt did not cover, recorded with the implement skill's evidence.

Limits: one engineer's account of the Claude Code harness and of eval transcripts, with no numbers and no controlled comparison. His observation that the Claude 5 models want smaller context and no examples concerns tool descriptions in that harness, not skill prose.
