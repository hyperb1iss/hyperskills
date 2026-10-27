# Evidence and limits

Reviewed 2026-09-04. The [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) explicitly notes over-testing on small tasks and unnecessary blocking from conflicting instructions. The proportional checks and user precedence in the skill address those risks.

Neither sibling reference (`benchmarks.md`, `recovery.md`) establishes universal edit ratios or model-independent performance guarantees.

## 2026-10-27 review

- Anthropic's [Opus 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5), read at the source on 2026-10-27, says explicit verification instructions such as "use a subagent to verify" cause over-verification on that model and should be removed.
- Anthropic's [Fable 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5), read at the source on 2026-10-27, says separate, fresh-context verifier subagents tend to outperform self-critique on long-running tasks; the trigger in this skill follows consequence and run length to honor both.
