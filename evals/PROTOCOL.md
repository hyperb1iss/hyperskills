# Measuring and improving Hyperskills

The experiment estimates the additional value of a particular skill revision for a specified task population, model, harness, and budget. Packaging checks and synthetic harness tests do not establish model efficacy.

## Experimental contract

Freeze the question before collecting results: target skill, task population, primary outcome, minimum useful effect, acceptable cost, and stopping rule. Keep user and repository instructions identical between conditions. Our Nova contract overlaps with skill guidance, so results under that contract measure incremental value for our workflow. A neutral-contract experiment answers a separate question about new adopters.

Compare baseline, explicitly loaded relevant skills, and normal discovery of the library. The explicit condition tests available content; discovery tests the deployed combination of routing and composition. Record actual reads where the adapter supports them. An unobserved read is unknown, not proof that a skill was ignored.

Pin model, harness version, settings, fixture, skill content, and grader. Use fresh sessions and working state; never fork an already exposed conversation. Randomize condition order. Count every attempt, failed launches, missing metrics, and delegated-agent spend. Keep failures distinct from invalid infrastructure trials; retain both and decide exclusions before looking at the treatment effect.

## Task selection and grading

Sample ordinary work as well as historical failures. Include clean reviews, easy edits, and requests outside a skill's scope. Synthetic traps are regression evidence, not a representative workload. Public development cases cannot be called private holdouts.

Keep graders and reference answers outside the agent's accessible environment. A separate directory and a fresh HOME are configuration hygiene, not security isolation. Real runs require an adapter/environment that prevents access to grader sources, repository history containing answers, other trials, personal memory, installed skills, and external state beyond the experiment's declared tools. Record the effective instruction and tool configuration.

Grade observable outcomes. Hidden behavioral checks settle coding requirements; clean and defective changes measure review precision and recall. Research needs supported conclusions, not citation counts. Prose needs protected-fact checks plus blind human preference. Planning needs downstream implementation outcomes. A deterministic prose preservation pass alone does not establish better writing.

Validate graders against a known good artifact, the original failure, and plausible wrong answers. The implementer cannot edit the grader during a trial. Model judges need blind randomized ordering and calibration against human judgments; keep their assessments separate from executable correctness.

## Improvement loop

1. Run the frozen development comparison and retain artifacts and traces.
2. Inspect discordant pairs: where skills rescue a failure or break a previously successful task. Classify content, routing, unavailable tools, excess process, or grader defects using observed evidence.
3. Write one revision hypothesis with the failure it should fix and the behavior it must preserve. Change the smallest useful part of the skill. Avoid adding another rule when deletion or a narrower trigger resolves the cause.
4. Compare candidate and incumbent on the same development tasks and budgets. The no-skill baseline remains the reference for whether either version earns its cost. Use separate versioned plans and retain both sets of receipts.
5. Confirm the chosen revision on untouched task families. Once a holdout informs an edit, retire it into development and replace it. Record every candidate tried, including unsuccessful revisions.
6. Keep, narrow, simplify, or retire the skill using the predeclared outcome and cost criteria. Recheck when models or harnesses change.

For each revision record: hypothesis, source run/trial IDs, failure class, skill diff hash, expected improvement, preservation checks, development result, held-out result, cost, and decision. Do not automatically rewrite or publish skills from benchmark scores.

## Interpreting results

Report each model/harness and family separately. Average repeat trials within task before estimating paired differences. Bootstrap whole tasks for uncertainty; related variants should share a task-family sampling unit in larger studies. Repeated attempts are not additional independent tasks. Tiny suites can produce misleadingly narrow intervals, including degenerate intervals when all outcomes match.

An interval spanning zero is inconclusive, not equivalence. To conclude that a skill lacks worthwhile benefit, the upper bound must exclude the predeclared useful effect with adequate coverage. Choose confirmation sample size from pilot variance and the target effect. Do not repeatedly peek and stop at the first favorable result.

Report total spend and latency alongside success, including unsuccessful attempts. Missing spend is unknown, never zero. Compare equal-budget outcomes when a skill gains quality by adding reviewers or additional attempts. Keep quality, preference, workflow fidelity, and safety errors separate rather than hiding them in one score.

## Initial scope

The bundled seed suite exercises implementation, review, research, and prose. It validates the measurement plumbing and supplies development regressions. It is deliberately smaller than the proposed 24-task empirical pilot. Expand from sampled real work after verifying the runner and graders, then execute model trials in isolated environments. No live efficacy result exists until those runs finish.

Primary methodological references: [SkillsBench](https://arxiv.org/html/2602.12670v4) and [Anthropic's agent evaluation guidance](https://www.anthropic.com/research/demystifying-evals-for-ai-agents), inspected 2026-11-06. Neither evaluates this library.

## Execution boundary

The supplied Claude adapter is a controlled file-task harness. It uses safe mode and restricted file tools, exposes an explicit catalog for discovery, and cannot run shell commands, network requests, or delegated agents. Its results describe that harness only. They cannot establish the benefit of native skill routing or a full coding workflow. A later native CLI/container adapter must prove equivalent tool availability and isolation across conditions before those broader claims are made.

Grading may execute candidate code. Run model trials and graders inside disposable environments without personal credentials or production access; keeping a grader outside the workspace does not make executing candidate code safe. The bundled synthetic oracle is trusted test code and exercises no model.
