# Evidence and limits

Sources behind the guidance in `SKILL.md` and `lenses.md`, with the limits each one carries.

## 2026-09-04 review, revised 2026-10-21

Reviewed on 2026-09-04, revised on 2026-10-21 after a retrospective over 38 agent-authored infrastructure pull requests; the necessity, seam, test-credibility and record guidance comes from the finding classes that recurred there. [Anthropic's evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) distinguishes outcomes, traces, and grader limitations; use all three when assessing a review workflow. [OpenAI's GPT-6 guidance](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md) (link updated 2026-11-20, when the earlier address had moved to a newer model's page) warns that "unclear or conflicting guidance in a skill file may cause the model to pause and block work early." The practical choice here is explicit scope and evidence requirements, with procedural defaults left adaptable.

For report craft, [Google's reviewer comment guidance](https://google.github.io/eng-practices/review/reviewer/comments.html) supports explaining rationale and distinguishing required changes from suggestions. Its [review standard](https://google.github.io/eng-practices/review/reviewer/standard.html) favors code health and progress over personal perfection. These are practitioner guidelines, not measured guarantees for model output.

The Microsoft field study [Expectations, Outcomes, and Challenges of Modern Code Review](https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/) (Bacchelli and Bird, ICSE 2013) identifies understanding and knowledge transfer alongside defect finding. Its human-team setting does not establish agent-review effectiveness; the application here is to preserve the explanation that makes a finding useful. [GitHub's review documentation](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request) defines the distinct comment, approve, and request-changes actions. These sources were checked on 2026-09-04.

Benchmark results depend on the model, task set, harness, and grader. No published recall percentage establishes a universal ceiling for this skill, and no fixed rejection rate is a target for candidate findings.

## 2026-10-27 review

[GitHub, agent pull request review guidance](https://github.blog/ai-and-ml/generative-ai/agent-pull-requests-are-everywhere-heres-how-to-review-them/) (May 2026): CI weakening blocks the PR; reviewers should also look for duplicated helpers, require a test that fails on the old code, and check for workflow-input injection. The agent-authored pull request lens in `lenses.md` applies these checks.

[arXiv 2609.28090](https://arxiv.org/abs/2609.28090) (2026): on a clean-control benchmark, a prompt stating the code may be clean cut false positives from 20.8% to 0%. The 0% is that benchmark's clean-control result, not a false-positive rate for this skill.

[Anthropic's Opus 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5): prompts saying "only report high-severity" or "be conservative" reduce recall; ask for every finding and filter in a separate pass. Lens agents in `lenses.md` already report every candidate with a proposed falsifier, and the coordinating reviewer filters them.

## 2026-10-30 review corpus

Observed: in about a week of review traffic from a single reviewer on roughly fifty pull requests, 88 of 98 review summaries carried deploy questions, and 35% of question instances re-asked a type already raised on that pull request; on four pull requests the same question returned for six to nine rounds. The Rollback and After deploy items in `lenses.md` section 7 encode that rubric. One reviewer, one repository; the rubric is a useful lens, not a measured defect-detection rate.

## 2026-11-06 review

Thariq Shihipar (Claude Code, Anthropic), [Unhobbling Claude: the difficulties and processes of building agents](https://www.youtube.com/watch?v=FlHfhwQaAFM), a talk at a Browserbase event published 2026-09-25, read from the auto-generated transcript on 2026-11-06: in eval transcripts the model finds an edge case the prompt did not cover and makes a judgment call there. The agent-PR lens bullet on undeclared calls follows that; the body-side half is in super-good-pr.

Limits: one engineer's account of the Claude Code harness and of eval transcripts, with no numbers and no controlled comparison. His observation that the Claude 5 models want smaller context and no examples concerns tool descriptions in that harness, not skill prose.

## 2026-11-20 review

Sources opened on 2026-11-20. For the four papers below the abstract was read and the claims here stay at what the abstract states; figures from the paper bodies are left out.

[Anthropic's Code Review documentation](https://code.claude.com/docs/en/code-review) describes its managed reviewer in four stages (several agents find in parallel, a verification step filters, findings are ranked, results are posted). It works "without building or running your code", "never approves or blocks the pull request", and reads review rules "from the base or default branch and never from the pull request's own changes." The line in `SKILL.md` about instruction files a change edits follows that last choice. This is a vendor's description of its own product, with no measurement of the choice.

[GitInject](https://arxiv.org/abs/2606.09935) (version 2, 2026-11-02) ran prompt-injection attacks against live CI workflows from four AI providers. Its abstract reports that every provider fell to at least one high-severity attack in the tested configurations, and that the worst are structural: "attacker-controlled configuration files from an unmerged contribution are loaded as operator-level instructions." The security lens treats such files as untrusted for that reason.

[When AI Agrees Too Much](https://arxiv.org/abs/2603.18740) (version 5, 2026-10-27, to appear at ICSE 2027) studies bias injected through pull request metadata. Its abstract calls the framing effect "a systematic and widespread phenomenon in LLM-based vulnerability detection" across six models, and reports that an attack refined against a local copy of the review pipeline succeeded in 32 of 33 cases against two review tools. The instruction to work out behavior from the code before reading the author's claims follows from this. The study concerns security vulnerabilities and adversarial authors; applying it to ordinary over-confident descriptions is an inference.

[Adaptive Code Revision Attacks on AI Pull Request Reviewers](https://arxiv.org/abs/2610.05399) (2026-10-04) builds a benchmark from 159 disclosed vulnerabilities and has an attacker revise the code using each round's review feedback. Its abstract reports reviewers that "accept repairs of reported problems while overlooking surviving vulnerabilities." The re-review paragraph in `SKILL.md`, which asks that a fixed finding's property hold across the whole change, follows from this.

[CRBugBench](https://arxiv.org/abs/2610.13668) (2026-10-09) pairs 1,800 human-verified bugs with the pull requests that introduced them. Its abstract reports the best agent catching 71.9% of bugs within its top five comments on open-source tasks, sharp drops on proprietary repositories "where project context is more often needed", and agents that "remain less effective on complex changes and bugs requiring non-local reasoning." It measures recall only, with no clean pull requests.

[Anthropic's Opus 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5), cited above for report-then-filter, also says that model "verifies its own work without being told to" and that prompts should not ask it to "use subagents to verify or double-check" its own work. Checking each candidate finding is a different step from re-checking a finished report, and the skill asks only for the first. The lens file now says lens agents start no reviewers of their own.

Local observation: in the review corpus described under 2026-10-30, 161 distinct inline findings were classified. Sixty-three fall in five classes this skill had not named: a wrong number or label at an edge (21), one bad item stopping a batch (12), a failure with no signal (11), unbounded growth (10), and a guard that fails open (9). The question table in `SKILL.md` and the matching bullets in the correctness lens come from that count. One reviewer, one repository, one week.

Local evaluation, 2026-11-20: `evals/cases/review` holds paired synthetic pull requests, each a defect case and a twin believed clean, graded by matching blocking findings to the defect's location. Two current models at low effort found every defect in the small cases (about 150 diff lines, one defect) with or without this skill, so those cases cannot show a skill effect. On two large cases (about 780 diff lines, three defects) the same reviewers typically found two of three. No trial opened `lenses.md`, which is why the questions that find common defects live in the entrypoint. Several twins believed clean drew blocking findings that turned out to be real defects, so blocking findings on a twin need adjudication before they count as false positives.
