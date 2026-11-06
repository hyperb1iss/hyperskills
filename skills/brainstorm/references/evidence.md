# Evidence and limits

Reviewed 2026-09-04. The [Design Council's Double Diamond](https://www.designcouncil.org.uk/resources/the-double-diamond/) describes iterative divergence and convergence; it does not prescribe option counts or divide judgment between humans and models. Treat it as a design aid, not an effectiveness benchmark.

The [OpenAI Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) recommends explicit instruction precedence and follow-through because conflicting skill guidance can cause unnecessary pauses. Apply that to workflow clarity without assuming every host exposes the same capabilities.

Reviewed again 2026-10-27 during the library audit; no change to the sources.

## 2026-11-06 review

Thariq Shihipar (Claude Code, Anthropic), [Unhobbling Claude: the difficulties and processes of building agents](https://www.youtube.com/watch?v=FlHfhwQaAFM), a talk at a Browserbase event published 2026-09-25, read from the auto-generated transcript on 2026-11-06: prompting the Claude 5 models is finding your unknowns. The prompt is a map and the codebase the territory; the user holds known unknowns, things they treat as obvious and leave out, and things they have not considered. The patterns he names are a blind-spot pass when the user does not know a domain, an interview when the user holds context they have not written, divergent directions for taste work the user cannot describe, references, and surfaced judgment calls. The elicitation paragraph and the two work-shape rows follow those patterns; the interview is for stated ambiguity, not a gate before every design.

Limits: one engineer's account of the Claude Code harness and of eval transcripts, with no numbers and no controlled comparison. His observation that the Claude 5 models want smaller context and no examples concerns tool descriptions in that harness, not skill prose.
