# Failure Recovery: Triage Tables and the Hang Ladder

Lookup material for when a cross-model review errors, stalls, or goes silent. SKILL.md carries the headline rules; this file carries the full symptom map. Drawn from a Jun 2026 audit of 4k+ Claude/Codex JSONL conversations plus a Jul 2026 pass over ~600 sessions — most failures are wrapper mechanics, not model quality.

## Codex → Claude Failure Triage

Classify the failure before changing tactics.

| Symptom                                                 | Meaning                                   | Recovery                                                                           |
| ------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------- |
| `Process running with session ID NNNN`                  | The review is alive; Codex yielded early  | Reap `session_id` with `yield_time_ms: 300000`; never re-run the command           |
| `Input must be provided either through stdin...`        | A variadic flag swallowed the prompt      | Re-run once with `--` before the prompt, or use the gold-path template             |
| `zsh: read-only variable: status`                       | The shell wrapper assigned `status=$?`    | Rename the variable to `rc` or `exit_code`; the Claude invocation may have worked  |
| Exit `124`                                              | A shell `timeout` killed the review       | Remove `timeout`; if an external guard is mandatory, use a much longer one         |
| Exit `130`, exit `143`, or `aborted by user`            | The process was interrupted or terminated | Read the output file first; do not infer a review verdict from the exit code alone |
| `write_stdin failed: stdin is closed`                   | The host lost the reaping handle          | Read the output file if printed; otherwise re-run once with the gold-path template |
| `Execution error` with little output                    | Claude runner failed after launch         | Inspect the output file, then retry once with a narrower prompt or diff packet     |
| `Unable to connect to API`, spend limit, or auth errors | External auth/billing/network state       | Stop retrying; surface the exact error and ask for auth or quota repair            |

**Timeout policy:** default to no shell `timeout` around `claude -p`. Codex already has the reap loop, and real reviews in the audited logs exceeded 180-240 seconds often enough that short timeouts created false failures.

## When the Reviewer Hangs

Silence is not failure. Output-file growth plus process state is the discriminator — never elapsed time. Growing output across reaps means still working, and slow can be a quality signal: a fast rubber stamp on a large surface would be suspicious. Work the ladder top-down:

| Rung         | Move                                                                                                                                                                                                                                |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Diagnose** | Check output-file size and the process tree before declaring it stuck                                                                                                                                                                |
| **Isolate**  | One variable at a time. Startup hooks / MCP helpers: `claude --bare` (drops subscription auth) or `--safe-mode` (keeps auth, drops hooks). Permission waits: `--permission-mode dontAsk`. Stdin hangs: pass the diff as an argument |
| **Degrade**  | No-tools piped diff, narrower file scope — same question, less payload                                                                                                                                                               |
| **Kill**     | Only the stuck process tree, never respawn blind. Pre-declare the give-up condition ("if this attempt sticks, I record the review as unavailable") and disclose the failed review in the wrap                                        |

Wedges observed in the field (as of Jul 2026): a stray MCP helper in the reviewer's startup path, a broken MCP transport, and permission prompts waiting on a stdin nobody was reading. Each was found by isolating one variable, not by rerunning the same command harder.

If every rung fails, step down the Degradation Ladder in SKILL.md — an honest "review unavailable" beats a fake green check.
