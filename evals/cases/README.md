# Development seed cases

These four public, synthetic cases exercise the evaluation pipeline. They are
not a representative workload sample or a held-out evaluation set. All are
marked `development`; do not relabel them as holdouts after reading or tuning
against them.

The pilot configuration uses a deterministic oracle, not a model. Its results
prove the runner can pass artifacts to graders. They cannot establish skill
benefit, routing quality, cost, or model reliability. Replace the configuration
with a verified model adapter before measuring those properties.

Only each case's `fixture/` directory belongs in the agent workspace. Prompts
are task instructions. Keep `grade.py` and `oracle_adapter.py` outside the
agent's readable sandbox when running an actual evaluation. Directory separation
alone does not prevent an unrestricted local agent from reading answers. The
atomic-export grader runs candidate code in a child with a temporary HOME and
working directory and a scrubbed environment. Candidate stdout cannot supply
the parent verdict. The tiny atomic-export fixture has a declared 10-second
candidate execution budget; exceeding it fails grading. This budget is specific
to these small local IO checks, not a generic model-task deadline. The process
boundary prevents stdout spoofing, not hostile same-user filesystem tampering.
The child still imports untrusted Python; run grading in a
separate isolated environment without private worker credentials or writable
access to the grading source.

| Case | Deterministic checks | Additional acceptance evidence |
| --- | --- | --- |
| Atomic export | Success, Unicode and empty input; interruption before and during iteration; original exception identity; destination and unrelated-file preservation; temporary-file cleanup; encoding-failure preservation | A concurrency/consumer test is needed to establish reader-visible atomicity beyond these fixtures |
| Review boundary | Source preservation; one finding at the defective condition; no finding on the clean module | Blind reviewer verifies that the stated trigger and impact identify the actual false-cache-miss defect |
| Prose preservation | Original preserved, selected required strings present, output changed | Blind human checks every fact, scope, uncertainty, readability, and absence of invented claims |
| Research release | Highest stable semantic version, correct evidence file, original packet preserved, limitation supplied | Blind reviewer checks whether the limitation actually distinguishes frozen evidence from current live state |

A deterministic `passed` result means only these checks passed. It is not the
full human acceptance verdict. In particular, a word-salad prose artifact can
retain every protected string. Every seed case reports `requires_human_review: true`. Numeric-string presence
does not establish the failed-file count (the command also contains `7`).
Keep human ratings separate from executable
pass rates and do not claim writing quality from the latter.

The research packet uses reserved `.invalid` URLs and is intentionally offline.
The task measures evidence interpretation, not browsing performance. The review
fixture supplies its contract explicitly so its grader does not impose an
unstated preference.

Run the grader regression checks with:

```sh
python3 evals/cases/test_graders.py
```
