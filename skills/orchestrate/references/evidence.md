# Evidence and limits

Reviewed 2026-09-04. Anthropic's [multi-agent research case study](https://www.anthropic.com/engineering/multi-agent-research-system) supports explicit scope and parallel independent investigations, while warning about coordination and token overhead. Research results do not establish a best coding-agent count.

The [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) recommends making delegation expectations explicit. Apply that within the actual host contract; API capabilities do not prove a particular CLI exposes them.

## 2026-10-27 review

1. Anthropic's [Opus 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5) (read at the source 2026-10-27): delegate only for large, genuinely independent work; do not delegate work finishable in a handful of tool calls; do not use subagents to verify or double-check your own work.
2. Anthropic's [Fable 5.1 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1) (read at the source 2026-10-27): letting the lead keep working while subagents run lowers time to completion at similar quality and cost.
3. [arXiv 2512.08296](https://arxiv.org/abs/2512.08296) (Dec 2025, abstract only): across 260 configurations, multi-agent setups gained on parallelizable tasks and lost on sequential ones; independent agents amplified errors more than centralized ones.
4. [arXiv 2609.28090](https://arxiv.org/abs/2609.28090) (2026, abstract only): a reviewer prompt stating the code may be clean cut false-positive findings from 20.8% to 0% on a clean-control benchmark.

Limits and reconciliation: the two arXiv results were read from their abstracts during the 2026-10-27 audit, not reproduced. The library's default is to fan out whenever work parallelizes; the Opus 5 caution in note 1 applies to tiny tasks and self-verification, not to independent work, and the multi-agent losses in note 3 were on sequential tasks. Note 1 and this skill's independent-verifier brief are reconciled by trigger, not by choosing one: the skill body limits "do not delegate" to small changes the coordinator can verify in a handful of tool calls, and reserves a separate verifier for consequence or run length (shared or production state, unattended runs past a checkpoint, an acceptance check the implementer cannot touch), following the [Fable 5 guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)'s finding that fresh-context verifiers outperform self-critique on long runs.
