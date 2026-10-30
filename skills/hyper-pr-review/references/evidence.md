# Evidence and limits

Sources behind the guidance in `SKILL.md` and `lenses.md`, with the limits each one carries.

## 2026-09-04 review, revised 2026-10-21

Reviewed on 2026-09-04, revised on 2026-10-21 after a retrospective over 38 agent-authored infrastructure pull requests; the necessity, seam, test-credibility and record guidance comes from the finding classes that recurred there. [Anthropic's evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) distinguishes outcomes, traces, and grader limitations; use all three when assessing a review workflow. [OpenAI's GPT-6 Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) warns that conflicting skill instructions can block work. The practical choice here is explicit scope and evidence requirements, with procedural defaults left adaptable.

For report craft, [Google's reviewer comment guidance](https://google.github.io/eng-practices/review/reviewer/comments.html) supports explaining rationale and distinguishing required changes from suggestions. Its [review standard](https://google.github.io/eng-practices/review/reviewer/standard.html) favors code health and progress over personal perfection. These are practitioner guidelines, not measured guarantees for model output.

The Microsoft field study [Expectations, Outcomes, and Challenges of Modern Code Review](https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/) (Bacchelli and Bird, ICSE 2013) identifies understanding and knowledge transfer alongside defect finding. Its human-team setting does not establish agent-review effectiveness; the application here is to preserve the explanation that makes a finding useful. [GitHub's review documentation](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request) defines the distinct comment, approve, and request-changes actions. These sources were checked on 2026-09-04.

Benchmark results depend on the model, task set, harness, and grader. No published recall percentage establishes a universal ceiling for this skill, and no fixed rejection rate is a target for candidate findings.

## 2026-10-27 review

[GitHub, agent pull request review guidance](https://github.blog/ai-and-ml/generative-ai/agent-pull-requests-are-everywhere-heres-how-to-review-them/) (May 2026): CI weakening blocks the PR; reviewers should also look for duplicated helpers, require a test that fails on the old code, and check for workflow-input injection. The agent-authored pull request lens in `lenses.md` applies these checks.

[arXiv 2609.28090](https://arxiv.org/abs/2609.28090) (2026): on a clean-control benchmark, a prompt stating the code may be clean cut false positives from 20.8% to 0%. The 0% is that benchmark's clean-control result, not a false-positive rate for this skill.

[Anthropic's Opus 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5): prompts saying "only report high-severity" or "be conservative" reduce recall; ask for every finding and filter in a separate pass. Lens agents in `lenses.md` already report every candidate with a proposed falsifier, and the coordinating reviewer filters them.

## 2026-10-30 review corpus

Observed: in one week of review traffic from a platform reviewer on 53 pull requests, 88 of 98 review summaries carried the same four deploy questions, 35% of question instances re-asked a type already raised on that pull request, and the ones without a body answer naming an owner and a moment were re-asked for up to nine rounds. The operator's-four-questions item in `lenses.md` section 7 encodes that rubric. One reviewer, one repository; the rubric is a useful lens, not a measured defect-detection rate.
