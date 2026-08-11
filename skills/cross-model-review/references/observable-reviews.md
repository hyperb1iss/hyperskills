# Observable Claude Reviews

Use this path for Codex → Claude reviews when Codex or a human needs progress visibility while the reviewer runs.

## Launch Contract

1. Write the complete review brief to a temporary prompt file.
2. Run `scripts/run_claude_review.py --prompt-file <path> --cwd <repo> --label <scope>` with `yield_time_ms: 1000`.
3. Record the printed review directory and returned Codex shell session ID.
4. Treat `Process running` as success. Never launch a duplicate reviewer.
5. Read progress with `scripts/review_status.py <review-dir>` and reap only the original shell session in 20–30 second windows.
6. Freeze the entire reviewed Git worktree while Claude runs. Reads are safe; any net tracked or non-ignored untracked difference present at completion voids the verdict.
7. After process exit, require `status.json` state `complete` before consuming `final.md`.

The runner rejects empty prompts and reused non-empty review directories. A caller-supplied `--review-dir` must live outside the resolved Git worktree and is forced to mode `0700`; omit it for an equally private unique system-temporary directory. `--claude-bin` exists for alternate installations and deterministic tests. The runner strips `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN`, supplies the prompt through file-backed stdin that reaches EOF, defers to the user's configured Claude model, and disables session persistence. Claude's `--safe-mode` disables customizations including MCP servers and custom agents while preserving auth, model selection, built-in tools, and permissions; `--tools` then allowlists only `Read`, `Glob`, and `Grep`, with Write/Edit/Bash tools explicitly denied as defense in depth.

## Artifact Contract

The runner creates a unique temporary directory:

| File           | Contract                                                                             |
| -------------- | ------------------------------------------------------------------------------------ |
| `meta.json`    | Launch context plus the child PID and initial Git snapshot                           |
| `events.jsonl` | Append-only raw Claude `stream-json`; use for diagnosis, not routine context loading |
| `status.json`  | Atomically replaced high-level state safe to poll while the review runs              |
| `stderr.log`   | Claude startup, authentication, permission, and transport errors                     |
| `final.md`     | Final result extracted only from Claude's `result` event                             |

`status.json` progresses through `starting`, `running`, then `complete`, `failed`, or `stale`. Its active phase is normally `starting`, `inspecting`, `validating`, or `reporting`; the terminal phase matches the terminal state. A `stale` result means HEAD or the tracked/non-ignored-untracked worktree fingerprint differs between launch and completion, or a freshness check that succeeded at launch became unavailable at completion. The runner exits 90, so discard the verdict and inspect the worktree delta; `freshness_error` explains a check that became unavailable. Wrapper exit 91 means Claude did not produce a usable, non-empty success result; inspect `status.json` for its actual child exit code or result error. `target_stale=unknown` means Git freshness could not be established at launch; disclose that boundary before using a non-Git review.

## Monitoring Rules

- Report meaningful phase changes to the user; do not narrate every file read.
- Use status changes, `last_event_at`, event count, and process state as liveness evidence.
- Do not enable `--include-partial-messages` by default. Partial deltas are noisy and can persist content that is irrelevant to progress.
- Do not expose hidden reasoning from the raw stream. The status helper derives only coarse activity from system, tool-use, assistant-text, and final-result events.
- Do not parse `stderr.log` as a verdict. On failure, preserve and report the exact error boundary.
- Do not delete the review directory until findings have been dispositioned; its files are the recovery record if the Codex shell handle is lost. After disposition, remove it only when local retention policy permits, because raw events can contain source excerpts and thinking blocks.

## Stall Recovery

If `status.json` stops changing, compare two monitoring windows and inspect the original process state. Growing `events.jsonl` means Claude is alive. An unchanged event count with a live process warrants one more window, then the isolation ladder in `failure-recovery.md`. Kill only a confirmed-stuck process tree, never respawn blindly.

If the process exits but state remains `starting` or `running`, inspect `stderr.log` and `events.jsonl`; treat the review as failed. If state is `complete` but the Git snapshot no longer matches, treat the verdict as stale even if `final.md` says PASS.
