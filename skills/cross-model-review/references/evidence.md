# Evidence and limits

Sources behind the guidance in `SKILL.md`, with the limits each one carries. A source here informs a review strategy; none of them measures an accuracy gain for this library.

## 2026-09-04 review

As checked on 2026-09-04, [Claude's CLI reference](https://code.claude.com/docs/en/cli-reference) distinguishes available tools from preapproved tools. [OpenAI's non-interactive documentation](https://developers.openai.com/codex/noninteractive) documents captured execution outputs. Verify both against the installed versions before dispatch.

The recommendation to examine outcomes and traces separately follows [Anthropic's agent evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). Cross-family diversity is a useful review strategy, not a measured guarantee for this library. No universal false-positive rate or accuracy improvement is claimed here.

## 2026-10-27 review

[arXiv 2607.27030](https://arxiv.org/abs/2607.27030) (Jul 2026): one pass from each of four model families found 68 CVEs, while four passes of the best single model found 65, and 62% of hits appeared in only 1 to 3 of 4 identical passes. The authors call the analysis exploratory.

[arXiv 2506.07962](https://arxiv.org/abs/2506.07962) (ICML 2025): when two models both answer wrong, they agree about 60% of the time, more often within one provider.

Application here: within that one exploratory study, repeat passes of a single model and a multi-family pass found similar totals, so repeat passes and distinct lenses count as review diversity alongside a second family. The result is scoped to vulnerability finding and does not establish equivalence for specifications, diagnoses, or fact checks. Correlated wrong answers mean agreement among reviewers raises investigation priority without confirming a finding.
