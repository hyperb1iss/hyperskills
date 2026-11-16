# Changelog

## 3.13.4

- implement now says a bug fix ships its regression test: one that fails on the unfixed code and passes on the fix. On ten held-out replays of real fix commits, the share of trials shipping such a test rose from 5 of 20 to 14 of 20 with correctness unchanged. Its self-review table also names a record the request says to skip, so a deliberate skip still leaves a trace.
- Skills surface judgment calls and ask for unsaid constraints, answer deploy questions before requesting review, and self-review first. Reviews no longer request changes for red CI alone.
- Correct stale facts and scope two rules after an audit against Claude Fable 5.2: the pinned-lease force push in git, demo-reel's verifier requirement, and several outdated paths, exit codes, and version stamps.
- Add an eval harness for measuring whether a skill changes outcomes: container trials with the network off, a failure-class screen, and replays of real fix commits graded by the tests those commits shipped. The READMEs record each result with its limits, including the runs that showed no effect.

## 3.13.3

- Encode recurring maintainer corrections across seven skills: implement names the ship state before adding a flag or fallback and finds the nearest existing pattern first; plan records ship state and keeps requirements distinct from preferences; super-good-pr defaults to one PR split only by review domain; brainstorm treats a supplied reference as the specification; git keeps ticket references out of code; orchestrate watch loops yield to user messages; hyper-pr-review recommends restructuring when a finding class recurs.

## 3.13.2

- Fan out by default: orchestrate and research now treat parallel subagents as the normal path for independent work and limit by shared resources rather than agent count.

## 3.13.1

- Compress the five process skills (brainstorm, plan, research, implement, orchestrate) to the guidance that still changes a decision for current models, keeping every table, worked example, and gotcha.
- Move dated citations out of every entrypoint into references/evidence.md so they stop loading at invocation; the contributor guide names the convention.
- Trigger independent verification by consequence and run length instead of by file count, make one review pass the default, and sharpen the verifier brief: the code may be clean, residual risk on PASS, smallest fix on FAIL.
- Add a hyper-pr-review lens for agent-authored pull requests and count repeat passes and distinct lenses as review diversity in cross-model-review.
- Record the October 2026 library review in docs.

## 3.13.0

- Add demo-reel, a skill that films the real product end to end and treats the reel as its acceptance test. The shot list doubles as the test plan, and every failed take becomes a fix before the whole reel is reshot. Bundled scripts handle deterministic 4K browser capture, sandboxed agent takes, contact sheets, and MP4 verification.
- Add two hyper-pr-review lenses: Necessity and Ownership, which runs first on platform work, and Seams and Test Credibility, for layer boundaries tested only against fakes. Existing lenses gain checks for unknown outcomes, hand-maintained mirrors that drift, and "dark" claims that are false on default paths. A new section keeps review evidence, approvals, and reply threads inspectable.
- Generate skill counts, the inventory, and marketplace metadata from source, and fail CI on drift. Each version now ships from a verified release PR, and an interrupted release can be rerun safely.

Releases prepared by the release workflow are recorded here. Earlier changes are documented in the repository history and the [September 2026 audit](docs/library-review-2026-09.md).
