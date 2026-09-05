# Hyperskills Review: September 2026

Version 3.11.0 contained 14 skills. The Tilt skill was subsequently retired in 3.12.0; this report records the audit before that removal. The four Astral skills were removed at the user's direction, and the retained workflows were revised around decisions, evidence, and operational details that still earn their context cost. The review started from commit `63dc003` and covered all 18 original skill entrypoints, their references, the prose scanner, and repository metadata.

The central problem was accumulated instruction conflict. Useful lessons had become universal rules: prescribed fleet sizes, approval pauses after an already authorized request, fixed confidence thresholds, and claims that a second model's agreement established correctness. Some copied tool examples were also wrong. The changes preserve the useful operational constraints while removing those defaults.

## Findings and Changes

| Surface            | Finding in the original library                                                                                                     | Result                                                                                                                 |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Brainstorm         | Clear implementation could trigger a design ceremony and another approval question                                                  | Exploration applies to unresolved direction; explicit requirements and authorization survive composition               |
| Plan               | File-count thresholds and separate test tasks displaced dependency reasoning                                                        | Tasks follow contracts and uncertainty; the behavior owner also owns its verification                                  |
| Research           | Quick facts could require multiple agents; wave and source quotas encouraged unnecessary work                                       | A decisive primary source can settle a fact; further research follows material evidence gaps                           |
| Orchestrate        | Fixed fleets, stale host arguments, and review decay by task number                                                                 | Partition actual independent work, identify shared resources, and preserve explicit incomplete verdicts                |
| Implement          | Activity ratios, fixed edit cadence, and false-green checks stood in for behavior                                                   | Verify the consumer-visible result; preserve errors, cache provenance, and causal baseline comparisons                 |
| Cross-model review | Five-minute initial waits ignored host limits; tool preapproval was described as read-only isolation                                | Discover current schemas, poll the existing handle, restrict available tools, and separate review from execution proof |
| Hyper PR review    | CI-detectable failures were suppressed; outdated recall figures justified abandoning coverage                                       | Report supported failures, track coverage, and distinguish incomplete review from approval                             |
| Git                | Partial staging advice contradicted a recommendation to use path-based commits; lease guidance could adopt an unreviewed remote tip | Commit intended index content without path arguments and retain the inspected remote expectation                       |
| Image delegation   | Authentication was treated as capability evidence; external destinations conflicted with child permissions                          | Inspect the actual tool contract and use a verified workspace-to-parent handoff                                        |
| Deslop             | Rewrite examples invented facts; unvalidated thresholds could strip legitimate uncertainty and voice                                | Preserve truth conditions, use stylistic signals as prompts for judgment, and remove unsupported quotas                |
| Dream              | Hidden reasoning and stale transcript assumptions became evidence; broad harvesting risked scope leakage                            | Use visible, scoped evidence with provenance, redaction, current-state checks, and applied write receipts              |
| PR descriptions    | Every new SHA invalidated all evidence; fixed body structure conflicted with templates and human ownership                          | Compare content, refresh relevant claims, and distinguish drafting from publishing authorization                       |
| Tilt               | Fallback and run examples described incompatible routes; restart/readiness shortcuts obscured runtime requirements                  | Make file routes explicit, respect initial-sync ordering, and separate evaluation from observed live behavior          |
| TUI design         | Environment hints became capability guarantees; lifecycle and async state handling were underdeveloped                              | Add terminal restoration, input ownership, stale-result handling, Unicode width, and accessible fallback behavior      |

The deleted Astral references contained concrete errors, including uv environment-file autoloading, reversed index priority, conflicting TOML examples, obsolete Ruff rules, and blanket type-check suppression. Those findings support the maintenance decision, but they do not establish that every model knows every current tool feature. Current help and primary documentation remain the right source when behavior is uncertain.

The unreferenced security-market survey was also removed. Its broad vendor recommendations and unsupported headline statistics did not serve a maintained skill. Security review guidance stays with the relevant review lenses and current primary-source checks.

## Research That Changed the Design

[OpenAI's GPT-6 Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) explicitly identifies conflicting skill instructions as a cause of premature pauses. The contributor guide and process skills now make user precedence and existing authorization clear. The guidance was checked on 2026-09-04; host capabilities still come from the actual runtime.

[Anthropic's harness-design report](https://www.anthropic.com/engineering/harness-design-long-running-apps) describes retiring scaffolding after model improvements. The useful implication is to retest a workaround's purpose when models change. The report is a case study, not evidence that every task needs its particular agent arrangement.

The updated [Evaluating AGENTS.md paper](https://arxiv.org/abs/2602.11988) studies repository context files and reports limited general success gains with added inference cost in its evaluated settings. The paper also identifies value in nonstandard project guidance. The review uses that distinction to favor operational knowledge over copied manuals; it does not treat the paper as an evaluation of Hyperskills or Astra.

[Anthropic's agent evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) separates outcomes, traces, and graders. The new evaluation cases follow that distinction. Syntax checks establish packaging, executable fixtures establish specific behavior, and independent review adds another opportunity to catch mistakes. None supports a model-performance claim by itself.

The tool-specific corrections use the official [Claude CLI reference](https://code.claude.com/docs/en/cli-reference), [Git push](https://git-scm.com/docs/git-push) and [commit](https://git-scm.com/docs/git-commit) manuals, and [Tilt Live Update contract](https://docs.tilt.dev/live_update_reference.html). These sources resolved actual command and ordering ambiguities. Local CLI availability was checked rather than inferred from the host name.

Terminal guidance draws on the [Crossterm event contract](https://docs.rs/crossterm/latest/crossterm/event/index.html), [Unicode grapheme rules](https://unicode.org/reports/tr29/), and [NO_COLOR convention](https://no-color.org/). State identity and cancellation guidance are engineering synthesis, not guarantees made by those protocols.

The prose evidence catalog retains relevant corpus research, including [Reinhart et al.](https://arxiv.org/html/2410.16107v2), while separating model-specific observations from editing rules. A recurring linguistic pattern is not an authorship verdict, and an editing pass must not change a claim's certainty merely to reduce a stylistic signal.

## Verification and Limits

The new validator parses YAML rather than checking only the opening delimiter. It checks required names and descriptions, duplicate keys, version syntax, entrypoint size, and concrete bundled references. Regression fixtures prove that an invalid early directory remains a failure after a valid later directory. The SemVer cases cover prereleases, build metadata, leading zeros, and non-ASCII digits.

The scanner now distinguishes valid empty files from unreadable inputs. Directory inputs, malformed UTF-8, and mixed valid/invalid inputs cannot report a clean run. Existing protected-region behavior remains covered by its regression suite.

Validation completed during the audit:

- All 14 retained skills pass manifest, frontmatter, and bundled-reference checks.
- All 10 validator tests pass, including parameterized malformed-metadata and version cases.
- All 89 prose-scanner regression cases pass.
- Independent reviewers checked each retained skill group and resolved the findings they raised.
- Selected behavior probes cover direct-fix routing, decisive-source research, shared build state, review-process polling, failed-CI review, semantic preservation, and scoped memory extraction.
- Disposable Tilt fixtures evaluate successfully, including the initial-sync ordering correction.

The skill entrypoints and immediate Markdown references decreased from about 80,900 words to about 40,700 words. The count excludes fixtures, scripts, and repository documentation. Reduction is a maintenance result, not proof of improved agent accuracy.

The audit did not deploy workloads, run a TUI application in a PTY, generate paid images, harvest private conversation histories, or publish PR comments. A corrected Tiltfile evaluating successfully does not prove live reload works. The full [behavior-case matrix](../evals/README.md) is available for future trials; selected walkthroughs do not constitute a controlled benchmark.

## Keeping the Library Useful

Retain instructions that prevent a demonstrated failure or teach a non-obvious operation. Prefer one owner for a procedure, with references for conditional detail. When the same instruction repeatedly causes a pause or scope expansion, test the composed workflow before adding another exception.

The next useful measurement is a small set of repeatable real tasks run with and without the changed skills under the same model and harness. Until that comparison exists, describe this release by its verified corrections and clearer contracts, not by an invented performance gain.
