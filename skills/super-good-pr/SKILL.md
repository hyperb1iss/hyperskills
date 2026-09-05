---
name: super-good-pr
description: Use this skill when writing or maintaining a pull request description or responding to review feedback. Activates on mentions of write a PR, PR description, draft a PR, open a pull request, polish this PR, make this PR good, banger PR, PR body, refresh the PR body, review reply, or describe these changes.
---

# Super Good PR Descriptions

Give reviewers the context they need to evaluate the final change. Lead with the concrete problem and resulting behavior, explain the design choices that matter, and support validation claims with actual evidence. The body should work for someone who did not watch the session.

A small fix may need two paragraphs and validation. A migration may need ordering, compatibility, and rollout detail. Match the explanation to reviewer uncertainty; a long section checklist does not make a small PR more credible.

## Establish the source of truth

Read the live PR body, title, base branch, head commit, and repository template before an update. Read the actual diff against that base; do not assume every PR targets `main`. For an existing PR:

```bash
gh pr view NUMBER --json title,body,baseRefName,headRefName,headRefOid,url
```

Fetch or refresh the relevant refs before deriving the local diff. A three-dot comparison uses the merge base and matches the usual PR comparison model. A stacked PR targets its preceding branch, so a diff against `main` would describe other layers too. GitHub documents these distinctions in its [PR reference](https://docs.github.com/en/pull-requests/reference/pull-requests).

Gather the original requirement, final behavior, decisive files, and checks that actually ran. Separate observed evidence from expected behavior. Avoid universal claims such as "safe" or "fully covered" when the evidence establishes only a narrower property.

## Make the title and opening carry the change

Name the behavior or design decision in the title. A reader scanning the PR list should distinguish this change from other work in the same subsystem. Prefer "Keep export retries attached to the original request" to "Improve export reliability." Follow the repository's title convention, including a Conventional Commit prefix when required; avoid packing internal symbols into the title at the expense of meaning.

Open with the situation that makes the change necessary and what the reader can expect afterward. Connect the mechanism to that result when it helps explain the fix. For a refactor, name the engineering constraint it removes and the behavior it preserves; do not invent a user-facing defect. These are relationships to explain, not three mandatory sentences or headings.

Keep the causal chain intact: trigger, consequence, changed behavior, reason the mechanism works. A list of edited files cannot supply that chain. Keep internal identifiers out of the opening until the reader knows what they represent.

Describe the final system. Leave routine development history in the commits and conversation. A rejected approach belongs in the body only when explaining its trade-off helps evaluate the chosen design. After a squash, retain that design rationale without recreating a session diary.

State boundaries that affect adoption or review. Do not enumerate untouched files or hypothetical alternatives just to fill a blast-radius section. If necessary work is unfinished and authorized, finish it. A draft PR can still be useful for early design feedback or external validation; label its incomplete work and readiness accurately. Do not expand the implementation scope while writing a description merely to avoid disclosing a gap.

## Shape the body

Use the repository template first. Preserve required metadata and checkboxes. An unavailable value gets the template's accepted "not applicable" or an explanation; never invent an issue ID or silently remove a required field.

Without a template, let the opening stand on its own and add headings when they help a reader find a different kind of information. Use a semantic emoji on headings you add under the house style. A body does not need every heading, an extra H1 repeating its title, or a context blockquote for a standalone fix. Prefer a specific heading such as `## 🛠️ Accept before processing` when it communicates more than a generic label.

| Section              | When it helps                                                             |
| -------------------- | ------------------------------------------------------------------------- |
| `## 💡 What changes` | Explain the problem and result                                            |
| `## 🛠️ How it works` | Explain a mechanism reviewers cannot infer from a small diff              |
| `## 🎯 Invariant`    | Identify the specific property the design must preserve                   |
| `## 🚦 Rollout`      | State deployment order, compatibility, safe stopping points, and recovery |
| `## 🧪 Validation`   | Record evidence and material limitations                                  |
| `## 🔍 Review focus` | Direct attention to actual uncertainty or difficult surfaces              |
| `## 📌 Follow-ups`   | Name deliberate deferred work and what blocks readiness                   |
| `## 🔁 Review delta` | Help returning reviewers find changes since their review                  |

Keep explanations in prose and use tables for comparisons or enumerable facts. A numbered sequence is useful when operation order matters. Preserve semantic emoji and other deliberate formatting during a prose cleanup pass; follow a repository's stricter template when it conflicts with house defaults.

Give the body a reading path: the opening explains the change; the visible sections explain the decision, evidence, and adoption concerns; optional detail supports a closer inspection. Keep a failed integration check, a required migration, or an unresolved correctness question visible. A `<details>` block can hold long command output or supplemental measurements, with a summary that says what the reader will find. It must not hide a condition that changes whether the PR is ready.

Use review guidance to connect a question to its evidence: "Start with the transaction in `accept_delivery`; its commit must precede the acknowledgment." Link the decisive code when a stable link is available. Omit inventories of every touched file and requests to "review carefully" without a concrete concern. Put a limitation next to the claim it qualifies, even when fuller receipts live in Validation.

## Validation evidence

Record the command or named CI job, outcome, and what it establishes. "Tests pass" leaves the reader guessing whether the changed path ran. "The retry regression passes with a simulated lost acknowledgment; delivery to the live provider was not exercised" identifies both the evidence and its limit. Use counts when the tool reports meaningful counts. A linter's successful exit does not need an invented test count. Identify skipped tests and a failing prerequisite when either limits the claim.

For a regression fix, a failing-before and passing-after reproduction can be the decisive evidence. For a deployed migration, show the relevant compatibility or state transition when available. Prefer the narrow check that exercises the changed behavior to a long inventory of unrelated green suites.

Keep receipts tied to the tested revision and relevant environment. A changed SHA requires checking what changed; it does not automatically invalidate every result:

| Change since verification                                          | Required action                                                                                    |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Source, dependency, configuration, or relevant environment changed | Run affected checks again; broaden when interactions changed                                       |
| Rebase incorporates a changed base or resolves conflicts           | Verify the integrated result and required CI for the new head                                      |
| Commit-message amend with an identical tree                        | Preserve applicable local evidence, identify the tested tree, and follow required head-specific CI |
| Squash with an identical final tree                                | Preserve applicable content evidence; rerun checks dependent on history or the new head            |
| Live external behavior is the claim                                | Recheck when external state may have changed                                                       |

Do not claim CI passed for a new head because an earlier run passed. GitHub's merge requirements and repository rules still govern. A content-equivalence check can justify reusing local evidence; it cannot waive required checks.

After a push that changes the described behavior, refresh an agent-owned body within the authorized scope. Update claims that actually changed. If the user froze the description, put factual drift in the session handoff and wait for authorization to edit the frozen artifact.

## Diagrams and visual evidence

Use a diagram when it resolves reviewer uncertainty about request flow, state, trust boundaries, or deployment order. Use a screenshot or clip for a visual behavior change. Skip diagrams that merely restate a trivial call chain.

GitHub supports Mermaid fenced blocks; its [diagram documentation](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams) explains supported rendering and version inspection. Keep labels and syntax compatible with the renderer, and verify the rendered result when available.

| Change                    | Useful visual                                                          |
| ------------------------- | ---------------------------------------------------------------------- |
| Request path or topology  | Small flowchart; before/after if the changed edge is otherwise unclear |
| Protocol or call ordering | Sequence diagram                                                       |
| State transitions         | State diagram                                                          |
| Schema relationships      | Entity relationship diagram                                            |
| UI behavior               | Screenshot or short clip showing the relevant state                    |

A diagram is a factual claim. Draw only verified components and ordering. Include a legend when needed rather than hiding meaningful distinctions. Do not place secrets, customer data, or private operational details in public attachments.

## Edit and publish without losing human work

Writing a draft and posting it are different actions. Publish only when the user has authorized the relevant external action. A request to open a PR authorizes creating that PR; a request to draft its body does not. Sending review replies needs its own applicable authorization.

Human-authored bodies, titles, and drafts remain read-only until the user authorizes editing them. An explicit request to polish an existing human-authored body supplies that authorization within its stated scope. A freeze remains binding. Do not interpret routine branch maintenance as permission to rewrite human prose.

For authorized edits, work from a captured live body and preserve unrelated content. Re-fetch before writing. If another person changed it, merge your intended edits into the new version; do not overwrite their revision with the stale draft. A wholesale rewrite is appropriate only when authorized and needed to reflect the final design.

Prefer a file to shell-interpolated prose:

```bash
gh pr edit NUMBER --body-file /path/to/reviewed-pr-body.md
```

Use a securely quoted heredoc or an editing tool to create that file. Backticks and `$()` inside a double-quoted shell string can execute before GitHub receives the text. Structured connector arguments are also suitable.

Read back the saved body after a write. Inspect rendering when available to catch broken diagrams, literal escape sequences, link errors, and formatting drift. API readback confirms saved text; it does not by itself prove visual rendering. Report a rendering limitation when it matters.

## Answering reviews

When replies are authorized, give each substantive finding a clear disposition: fixed with a commit or test, no action with a reason, deferred with a concrete follow-up, or stale with evidence. A reply can cover related comments without spamming one message per sentence.

Explain what changed and why it addresses the concern. Credit useful catches. Take valid nits when they fit the request, but inspect automated suggestions instead of accepting them mechanically. Answer the thread and leave resolution to the reviewer unless the user or repository explicitly authorizes resolving it.

Use the project voice and required attribution. Under the Bliss/Nova contract, final PR comment replies end on their own final line with:

```text
~ via nova ⚡
```

A generated-by footer in a PR body can stay; do not remove attribution as part of prose cleanup.

Put the disposition first, then the causal reason and supporting check. For an unresolved design choice, state the recommendation and the trade-off the reviewer is deciding. A reply should answer the original concern without requiring the reviewer to infer the answer from a commit link or an unrelated green suite.

## Voice and prose cleanup

Use plain, complete sentences. Lead with the English noun before a path or SHA, keep the subject near its verb, and explain consequences in the order the reader needs them. Preserve calibrated uncertainty; remove empty hedges and inflated significance.

No em or en dashes in house-authored prose. The ban is a house convention, not evidence that punctuation identifies AI authorship. Avoid house jargon such as "load-bearing" in a PR body. Words used to describe the desired quality in chat, such as "banger" or "cinematic," are not copy for the artifact.

Run the relevant `deslop` prose checks without removing meaningful emoji, required headers, or evidence. Keep the body as short as its explanation permits and as detailed as review requires. Do not compress causal reasoning into fragments or add sections to make a small change appear substantial.

Read the draft as a reviewer returning cold: can the title and opening explain the result, can the visible body support a readiness decision, and can the detailed evidence guide inspection? Repair the missing connection or remove the redundant passage. Do not add a section simply because the draft looks short.

## Stacked PRs

Use a small navigation block naming the current layer, its base, and adjacent PRs. The body says what this layer contributes and what belongs to later layers. Confirm status before marking a predecessor merged or claiming a rebase onto the current base.

Split by coherent review and verification boundaries. A description should clarify the chosen stack, not prescribe universal PR-size limits or force an unrelated branch restructuring. Stack mechanics belong to `git` and `plan`.

## Anti-Patterns

| Mistake                                           | Correction                                                      |
| ------------------------------------------------- | --------------------------------------------------------------- |
| Paste a changelog as the explanation              | Explain the problem, behavior, and design                       |
| Fill every heading for a small fix                | Keep only sections that help review                             |
| Repeat old green CI against a new head            | Check which evidence remains applicable and run required checks |
| Assume the base is `main`                         | Read the PR's actual base                                       |
| Overwrite a human's latest edit                   | Re-read and merge only authorized changes                       |
| Turn a limitation into unsolicited implementation | Complete authorized requirements and state real boundaries      |
| Publish because drafting finished                 | Check the action is authorized                                  |

## Worked examples and basis

Consult [worked examples](references/worked-examples.md) when choosing the shape of a small fix, explaining an asynchronous correctness boundary, or making a scoped template edit. Each example starts with its complete factual packet; the output cannot claim more than that packet establishes.

The examples also link the primary guidance behind these choices. Google and GitHub describe useful engineering practices and supported formatting, not a measured universal optimum for PR length, heading count, or model output quality.

## What This Skill is NOT

- A fixed twelve-section template or a changelog generator.
- Permission to overwrite human prose, post messages, merge, or deploy.
- A substitute for implementation review or validation.
- A reason to enlarge a small change or conceal unfinished work.
