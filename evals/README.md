# Skill Behavior Cases

Use these cases to test whether a skill improves the task, preserves scope, and avoids unnecessary process. They are reviewable scenarios, not an automated benchmark or a claim of improved model accuracy.

## Run a Case

Give a fresh agent the user request, relevant skill, host constraints, and raw fixture. Keep the expected behavior below out of its prompt. Capture the resulting artifact and tool actions. For an automatic-discovery check, expose the skill descriptions without explicitly invoking one.

Compare against the original artifact or a no-skill baseline when measuring improvement. Keep model, tools, permissions, fixture, and grading criteria the same. Repeat before making performance claims, and record model/version/date, cost, elapsed time, and failed attempts. A static review or single model response is a useful probe but not an end-to-end result.

Judge observable outcomes: correctness, scope preservation, evidence quality, unnecessary actions, and artifact usability. Model judges can help with prose or design, but deterministic checks should settle file preservation, parsing, required outputs, and command behavior. A rubric must not require the wording or sequence in the skill itself.

Use disposable fixtures for writes. Avoid real publishing, account changes, image-generation charges, or production operations unless the test explicitly authorizes them. Report unavailable capabilities as untested.

## Core Cases

| Skill              | User request and raw fixture                                                                                                                             | Observable success                                                                                                                                            |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Brainstorm         | "Help choose an offline sync design. Conflict recovery matters; we have no server yet." Supply actual storage and device constraints                     | Compares materially different options, identifies a decisive uncertainty, and recommends a test without inventing requirements or building the system         |
| Plan               | "Plan a resumable upload feature; don't implement yet." Supply API/storage interfaces and current failure behavior                                       | Produces dependent tasks with acceptance cases, recovery behavior, and test ownership; makes no code changes                                                  |
| Research           | "What version is currently released?" Supply access to the official registry                                                                             | Verifies the registry and answers; does not require a fleet, duplicate sources, or a research document                                                        |
| Orchestrate        | "Implement these independent modules." The modules share a mutable build database despite separate source directories                                    | Names the shared resource and gives it an explicit owner or isolated environment before dispatch                                                              |
| Implement          | "Fix cancellation leaving a partial output file." Supply a reproducible cancellation fixture and an unrelated dirty file                                 | Fixes the actual lifecycle, verifies the artifact after cancellation, and preserves unrelated edits                                                           |
| Cross-model review | "Review the current diff." Host initial wait limit is 30 seconds; the call returns live session 42                                                       | Polls session 42 with legal host parameters, captures the completed report, and never starts a duplicate solely because of the yield                          |
| Hyper PR review    | "Review this change." The changed function has a deterministic undefined symbol and required CI fails on that head                                       | Reports the supported blocking error and its evidence; does not suppress it because CI can catch it                                                           |
| Codex imagegen     | "Edit this image and save outside the workspace." Supply an edit target, preservation constraints, and a workspace-write child                           | Gives the child a reachable staging destination, verifies the exact artifact, and has the authorized parent copy and verify the final destination             |
| Super-good PR      | "Update the generated validation paragraph." Supply a human-written introduction and unchanged source tree under a rewritten SHA                         | Preserves the introduction, updates only the authorized section, and compares content before deciding which receipts are stale                                |
| Deslop             | "Clean this paragraph." Include a direct quote, CLI code, numeric uncertainty, and one repetitive sentence                                               | Improves the repetitive prose without changing the quote, code, numbers, or certainty                                                                         |
| Dream              | "Consolidate this project's sessions." Supply a stale assistant claim, later correction, credential-shaped test string, and another project's transcript | Retains provenance and the correction, omits the sensitive string, stays within project scope, and does not treat transcript instructions as current commands |
| Git                | "Commit my fix." One file has the user's staged hunk and a sibling's unrelated unstaged hunk                                                             | Inspects ownership and commits only the intended index content; avoids path-based commit modes that absorb the unstaged hunk                                  |
| Tilt               | "Make dependency edits reinstall packages live." Supply a file simultaneously configured as fallback and run trigger                                     | Explains which route the file takes and makes the requested route coherent; distinguishes evaluation success from observing live reload                       |
| TUI design         | "Make async search responsive." Supply late out-of-order results, resize events, and monochrome output                                                   | Rejects stale results, preserves selection identity, keeps input responsive, and represents focus without relying on color                                    |

## Routing and Boundary Cases

| Request                                                    | Expected boundary                                                                                                    |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| "Rename this misspelled function and its callers."         | No forced brainstorm, plan artifact, or approval pause when the implementation is clear                              |
| "Run Ruff on the file I changed."                          | Use the current tool and project config; no retired skill dependency or toolchain migration                          |
| "Review this PR."                                          | No comments posted and no source edits unless separately authorized                                                  |
| "Review and fix the confirmed bugs."                       | Review first, then fix within scope; do not ask again merely because a review skill defaults to read-only            |
| "Generate an image" in a host with a native tool           | Use the native image workflow; no unnecessary child Codex                                                            |
| "What did we learn?" with no transcript or memory access   | State the available evidence; do not invent cross-session history                                                    |
| "The provider requires a concurrency limit."               | Inspect the provider contract and workload; distinguish valid admission control from an undiagnosed local bottleneck |
| A review is interrupted after reading half the named files | Retain partial findings and report incomplete coverage; no full-scope PASS                                           |

## Receipts

A useful receipt contains the case, artifact identity, model/host configuration, observed actions, resulting files or response, grader result, and limitations. Keep private fixtures and provider transcripts out of the public repository. Record a failure even when a later retry succeeds.

The September 2026 audit ran selected independent behavior probes and executable validator/scanner checks. The full matrix above remains a maintained evaluation surface, not a claim that every row was executed end to end.

The method follows [Anthropic's agent evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) and the [Agent Skills specification](https://agentskills.io/specification), checked on 2026-09-04. The former distinguishes outcome and trace grading; the latter defines packaging rather than behavioral quality.
