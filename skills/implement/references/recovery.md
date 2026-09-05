# Recovery Protocols

Use these procedures when verification fails or an incident changes the operating conditions. Establish the cause before choosing a repair. Preserve evidence and existing authorization; urgency does not grant ownership of other people's work.

## Classify the First Failure

| Failure class            | Evidence to seek                                                       | Response                                                      |
| ------------------------ | ---------------------------------------------------------------------- | ------------------------------------------------------------- |
| Runner or infrastructure | Checkout, network, resource, or runner failure before the target check | Diagnose that resource; rerun only when conditions justify it |
| Install or environment   | Missing dependencies, wrong version, missing generated prerequisite    | Repair the demonstrated environment mismatch                  |
| Invocation               | Flags rejected, filter selects nothing, shell parsing error            | Correct the command and rerun the intended check              |
| Stale artifact           | Running revision or built output differs from inspected source         | Rebuild the affected artifact and verify identity             |
| Shared-output race       | Concurrent writers use the same path, port, or fixture                 | Reproduce in isolation, then fix ownership or isolation       |
| Pre-existing failure     | Matching symptom on an appropriate base under controlled conditions    | Report the baseline and analyze whether the change worsens it |
| Runtime defect           | Reproducer reaches the changed behavior with incorrect results         | Test the cause, make a targeted repair, re-verify             |

The table guides investigation; it is not an elimination algorithm that proves the last remaining category. Several causes can coexist.

Capture the raw log and real exit status before filtering. Trace downstream failures to the earliest failed dependency. Keep the environment, command, inputs, revision, and failure signature with the receipt.

## Reproduce the Relevant Gate

Inspect the actual CI invocation and its semantics: environment variables, coverage settings, test selection, dependency versions, base ref, and setup artifacts. Run the matching check when feasible, or state the precise difference in the local approximation.

Do not assume a package runner forwards file arguments or that a local default matches CI. Inspect the output to confirm the intended tests executed. Preserve pipeline failure status; avoid turning a failed command into a successful `tail` invocation.

Use separate scratch or worktree state for baseline comparisons when needed. Do not check out an older revision over a shared working tree. A clean comparison must control relevant environment and data differences, not just the Git SHA.

## Attribute Failures Causally

A trace containing no changed filename does not exonerate a patch. Configuration, dependency changes, timing, and shared state can affect code absent from the diff. A passing local run also cannot disprove an environment-specific defect.

For a claimed pre-existing failure, show the matching baseline signature under comparable conditions and inspect the changed causal path. If reproduction is unavailable, report "baseline attribution unverified" with what evidence is missing. Rebase only when needed for the task; a red baseline does not automatically justify rewriting branch history.

Treat intermittent failure as a property to investigate. A fail-then-pass sequence proves variability under the observed conditions, not harmlessness. Capture seeds, ordering, concurrency, resources, and environment differences when relevant. An infrastructure error can justify a rerun; a repeated failure needs an updated hypothesis rather than a standing "flake" label.

## Check the Instrument

When the probe disagrees with direct state, inspect its assumptions: authentication, selectors, parsing, expected startup time, and the revision being measured. Test a new detector on both a known positive and a known negative. Progress signals such as artifact growth or completed work can distinguish a slow process from an idle one more reliably than silence alone.

Temporary serialized reproduction can establish a race; the permanent fix belongs in shared-state isolation or coordination. Remove diagnostic restrictions after the cause is resolved. Do not hide a capacity defect behind a new permanent cap.

## Incident Recovery

| Need                              | Action                                                                         |
| --------------------------------- | ------------------------------------------------------------------------------ |
| Stop an ongoing harmful operation | Use the authorized containment action and preserve the current state           |
| Understand impact                 | Inspect deployed revision, affected population, and first failure              |
| Keep recovery work isolated       | Use an owned branch/worktree; do not stash or reset shared edits               |
| Restore service                   | Choose the smallest evidence-supported mitigation or rollback within authority |
| Verify restoration                | Check the consumer path and relevant health signals                            |
| Prevent recurrence                | Add the justified regression check, alert, or runbook correction               |

A hotfix from the deployed revision and a separate durable patch may be appropriate when release state diverges. They are not mandatory tracks for every incident. Record any temporary relaxation, its owner, and the restoration condition. Do not automatically suspend a known safe recovery to perform a ceremonial freeze.

Check sibling environments when the cause plausibly affects them and read access is authorized. Keep the sweep bounded to the demonstrated failure mechanism. Report quantified progress and a named tripwire during live recovery; cancel obsolete watchers and owned background jobs at the end.

## Exit Evidence

State the confirmed cause, corrective action, exact checks and results, remaining uncertainty, and any temporary mitigation still active. Record durable failure mechanisms in configured project memory. A recovery is complete when the requested outcome and applicable checks are satisfied, not when the last command exits successfully.
