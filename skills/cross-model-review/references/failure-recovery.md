# Review Failure Recovery

Preserve the original prompt, output path, process handle, and error. Classify the failure before changing anything. Never run a duplicate beside an active reviewer.

| Signal                         | Interpretation and next check                                                                           |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- |
| A process/session/cell ID      | The host yielded. Poll that handle with its supported wait operation                                    |
| Missing prompt error           | Check variadic options and the `--` separator; confirm prompt stdin is nonempty                         |
| Read-only shell variable error | Rename the wrapper variable; inspect output because the reviewer may already have completed             |
| Exit 124                       | A surrounding timeout ended the process; it is not a model verdict                                      |
| Exit 130 or 143                | Interrupted or terminated; retain partial findings and mark incomplete coverage                         |
| Lost polling handle            | Inspect saved output and the exact process tree before relaunching; the reviewer may still be alive     |
| Auth, quota, or provider error | Report the actual access problem; do not change credentials or billing routes silently                  |
| Tool denied                    | Decide whether the check can be performed with existing access; otherwise disclose the missing evidence |

For the [observable runner](observable-reviews.md), inspect `status.json` and `stderr.log` before reading the raw stream. Wrapper exit 90 marks a changed or lost Git snapshot; exit 91 means no usable successful result. A saved `complete` state confirms process/result handling, not the substantive review verdict.

## Slow Versus Stuck

Read output growth and process state together. The runner's event count and last activity describe observed events, not guaranteed liveness; verify the original process when status stops changing. A quiet process can be computing, waiting on stdin, or blocked by a helper. Neither quiet output nor a long runtime proves failure. Growing output can also be an unproductive loop.

When progress is uncertain, identify the contended resource or pending operation. Inspect the specific child process, available stderr, and host session state. Do not print its environment or unrelated process command lines (they may contain credentials).

If startup customizations are implicated, isolate them with supported safe-mode controls. If permissions are waiting for input, use the host's noninteractive denial mode and report any check it prevents. Close unused stdin when the prompt is an argument. Change one diagnosed cause per retry.

Choose a stopping condition that fits the review's scope and the user's time or budget constraints. A deadline can end incomplete work; it cannot convert it into PASS. Terminate only the identified job and its children, confirm termination, then consider a narrower retry. If the environment still cannot support the review, report INCONCLUSIVE with the captured error and useful partial results.

## Recover the Result Before Repeating Work

A process exit and a substantive verdict are separate evidence. Read the entire saved result or locate all findings plus the final verdict without discarding the original. A large transcript can contain a valid review; a short report can be an error message.

For a follow-up, resume the same session only if persistence was enabled and the CLI supports it. Otherwise launch a new scoped review with the prior finding and exact delta. A fresh reviewer must not inherit an unverified PASS.
