# Evidence and limits

Reviewed 2026-09-04. The [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) explicitly notes over-testing on small tasks and unnecessary blocking from conflicting instructions. The proportional checks and user precedence in the skill address those risks.

Neither sibling reference (`benchmarks.md`, `recovery.md`) establishes universal edit ratios or model-independent performance guarantees.

## 2026-10-27 review

- Anthropic's [Opus 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5), read at the source on 2026-10-27, says explicit verification instructions such as "use a subagent to verify" cause over-verification on that model and should be removed.
- Anthropic's [Fable 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5), read at the source on 2026-10-27, says separate, fresh-context verifier subagents tend to outperform self-critique on long-running tasks; the trigger in this skill follows consequence and run length to honor both.

## 2026-10-30 review corpus

Observed, not external research: 161 distinct inline findings from a single reviewer over about a week on roughly fifty pull requests in a private repository, classified independently by a second model. 76% ended with a code change. The largest classes: a test that stays green with the code under test removed or wrong (21) plus a changed failure path with no test (12); a wrong number, label, or message at an edge (21); a copy that will drift (16); one failure taking out healthy work (12); a race or ordering gap (12); a silent failure (11); unbounded cost (10); a boundary failing open (9). The self-review table in `SKILL.md` encodes those classes. One reviewer, one repository, one week; the classes are a checklist, not a frequency claim about other teams. Names and repository are omitted on purpose.

## 2026-11-06 review

Thariq Shihipar (Claude Code, Anthropic), [Unhobbling Claude: the difficulties and processes of building agents](https://www.youtube.com/watch?v=FlHfhwQaAFM), a talk at a Browserbase event published 2026-09-25, read from the auto-generated transcript on 2026-11-06: in eval transcripts the model finds an edge case the prompt did not cover and makes a judgment call one way or the other, and surfacing that call for a human to answer would pass almost every eval they have. The section on recording calls follows that claim; the one-question rule for material readings comes from the maintainer's contract, not the talk. He also reports that the Claude Code system prompt shrank by about 80% for the Claude 5 models, with prohibitions replaced by criteria; the contributor guide carries that heuristic.

Limits: one engineer's account of the Claude Code harness and of eval transcripts, with no numbers and no controlled comparison. His observation that the Claude 5 models want smaller context and no examples concerns tool descriptions in that harness, not skill prose.
