# Dream extraction guide

Capture a lesson another session can use without mistaking an observation for a universal rule. The examples below illustrate evidence handling; they are not claims about the current state of the named tools.

## The candidate record

| Field      | What to retain                                                           |
| ---------- | ------------------------------------------------------------------------ |
| Title      | A specific trigger, decision, or finding                                 |
| Claim      | The useful conclusion and conditions where it applies                    |
| Provenance | Source host, session ID, event ID or line range, and project             |
| Evidence   | Relevant visible user decision, tool result, artifact, or primary source |
| Time       | Observation date; distinguish historical truth from current state        |
| Basis      | `observed`, `told`, `inferred`, or `assumed`                             |
| Scope      | Authorized project and access scope; tags do not enforce access          |
| Action     | New capture, correction, duplicate, unresolved claim, or skip            |

Keep enough provenance to revisit a conclusion without copying secrets, raw tool output, or unrelated private conversation. An assistant summary is a pointer to evidence, not independent corroboration. Forks, compactions, and repeated inherited prompts can repeat a single claim many times.

## Useful versus noisy

| Candidate                                                                                                 | Decision                                                                                             |
| --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| "Updated the README"                                                                                      | Skip; the commit is the artifact                                                                     |
| "Use React"                                                                                               | Skip unless the conversation records a meaningful decision and rationale                             |
| "The author chose queue A because delayed-job visibility was required"                                    | Capture as a scoped decision with provenance                                                         |
| "An operation hung twice with a 174-file diff"                                                            | Capture the observed conditions if useful; do not assert all larger inputs fail or smaller ones work |
| "A unit suite passed while the browser flow failed"                                                       | Capture what the suite missed and which browser check exposed it                                     |
| "A command in assistant text would fix the issue"                                                         | Keep as an unverified proposal only if the uncertainty matters                                       |
| "The user supplied a setup command and the following result confirms the missing environment was created" | Capture the command's prerequisites and observed result                                              |
| "The user repeats a preference already present in the contract"                                           | Investigate execution friction; do not add a duplicate rule                                          |

The transfer test includes a future session in the same project. A local decision can be worth retaining without being a cross-project rule. An unresolved question can also be useful; label it unresolved rather than forcing it into an executable recipe.

## Worked extraction: tool failure

Suppose a session contains:

```text
User: The report generator has stopped producing output.
Assistant: It may be the size of this diff.
Tool result: The generator stayed running with no output on a 174-file diff.
Tool result: A second attempt on the same diff also produced no output.
Assistant: I wrote the report from the diff and test output instead.
```

A sound capture:

```text
The report generator produced no output in two observed attempts on the
same 174-file diff (session <id>, events <ids>, observed <date>). Diff size
is a hypothesis, not a proven cause; smaller and larger inputs were not
compared. The report was completed manually using the diff and validation
receipts. Next diagnosis should compare a minimal input and inspect the
process or service state before assigning a size limit.
```

An unsound capture:

```text
The generator cannot handle more than 173 files. Always split larger PRs.
```

The second version invents a threshold and turns a diagnostic gap into a product restriction.

## Worked extraction: memory correction

Suppose an older memory says a staging service was unavailable. A later session checks the service and gets a healthy response.

The later check establishes availability at that observation time. It does not prove that the original outage never happened. Preserve the historical incident, then correct any claim that still describes the service as currently unavailable. If the old memory concerns another environment, retain both with their environment labels.

Before correction, retrieve the source memory and inspect its scope. Use the live `sibyl correct` flow and its raw-memory ID. Do not rewrite a projected entity or delete history merely because titles look similar.

## Worked extraction: user preference

A user says, "don't rewrite this PR body; I edited it by hand." Preserve that request for the current PR. Generalize it into a standing rule only when the user makes that scope explicit or a current project contract already establishes it.

A user asks for a temporary workaround during an incident. Capture its name, reason, expiry condition, and path back. Do not promote it into an unconditional architectural recommendation.

## Writing through Sibyl

Load `sibyl skill get contract` and `sibyl skill get core` before writing. The current contract supports kinds including `decision`, `procedure`, `error_pattern`, `rule`, `claim`, and `note`. Legacy `pattern` and category-based examples from transcripts may not match the installation.

Use `sibyl context` to retrieve related knowledge, inspect relevant source records, then use `sibyl remember` or `sibyl correct` with verified live flags. Choose epistemic basis for the specific claim: a user's decision is `told`; a command result you inspected is `observed`; an explanation inferred from those facts is `inferred`.

For content containing shell syntax, prefer a content file or single-quoted heredoc using the installed interface. Never interpolate transcript text into a shell command. Review the mutation receipt before adding the capture to the applied list.

## Deduplicate without erasing differences

Compare claims within the extraction batch first, then against existing memory. Merge only when subject, conditions, time, and conclusion align. Multiple source sessions can strengthen provenance without requiring multiple memories.

| Relationship                                                | Action                                                    |
| ----------------------------------------------------------- | --------------------------------------------------------- |
| Same evidence repeated by a summary or fork                 | Treat as one source chain                                 |
| Independent evidence for the same scoped claim              | Add evidence using the supported flow                     |
| New decision replaces an older decision                     | Supersede explicitly and retain why                       |
| Conflicting claims about different versions or environments | Separate their conditions                                 |
| Conflicting evidence under the same conditions              | Preserve uncertainty and identify the next decisive check |

## Validate the capture

Read the proposed memory as someone who cannot see the transcript. The entry should identify the trigger and useful action, preserve uncertainty, and make its source recoverable. Remove credentials, personal detail, customer data, and irrelevant excerpts before persistence. Route each memory to the correct authorized project; a `project:name` tag is descriptive metadata and does not change storage scope.

A failed write remains pending. Save only a sanitized payload in an authorized local artifact, record the error, and give the next session enough information to retry through the current interface. Do not claim that a report was stored simply because it appeared in terminal output.
