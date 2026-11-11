# Evidence and limits

## 2026-09-04 review

Checked on 2026-09-04 against the official [push](https://git-scm.com/docs/git-push), [fetch](https://git-scm.com/docs/git-fetch), [commit](https://git-scm.com/docs/git-commit), and [range-diff](https://git-scm.com/docs/git-range-diff) manuals. Explicit leases protect an inspected remote expectation. Range-diff helps compare patch series; it is not a semantic-equivalence proof or a reliable replacement for tree comparison after squashing. Local branch ownership, worktree layout, and publishing authorization remain repository policy.

## 2026-10-27 review

Moved here from the entrypoint during the library audit so the citations stop loading at invocation; no change to the sources.

## 2026-11-11 review

Anthropic's [Fable 5.2 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2), read 2026-11-11 through the vendor's bundled migration notes, reports that approval rules in a prompt are applied as written, so a rule should name the exact actions it covers; in its testing an unscoped approval rule made the model hold back about half of its routine requests. The force-push row in the anti-pattern table said "only when approved" while the rebase table and the safety rules treat a pinned-lease push to your own branch as routine, so the row now carries the same scope. Vendor testing on simulated tasks, not a measurement of this skill.
