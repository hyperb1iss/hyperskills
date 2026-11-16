# Coding, traces, and clarification experiments

The runner now supports shell execution in Docker, visible action traces, scripted clarification, and exact-section subtraction. These are reusable experiment mechanisms. Synthetic oracle runs and mocked Docker tests do not establish skill efficacy or prove a live deployment's isolation.

## Shell execution

The container transport supplies Bash alongside the file tools. Agent and grader execute in separate containers. The grader has no network or provider credentials. The agent has provider network access and only explicitly named credential variables. Neither container receives the host repository, ambient HOME, Docker socket, or other trials. The future scripted replies stay outside model-visible mounts.

Supply a clean image containing Python 3, Bash, the pinned Claude CLI, and the dependencies required by the fixture. The included Dockerfile builds a minimal image explicitly:

```sh
docker build --build-arg CLAUDE_VERSION=2.1.319 \
  -t hyperskills-eval:local evals/container
# Use the returned immutable ID in container_image.
docker image inspect --format '{{.Id}}' hyperskills-eval:local
```

The build example uses the CLI version inspected on 2026-11-06. Choose and verify a version for each experiment. The base tag and package repositories are resolved during the build; the resulting image ID pins the execution environment. The runner never builds or pulls an image automatically. Trial HOME is fresh, so a Docker endpoint selected only in personal Docker configuration is not inherited. Set `DOCKER_HOST` explicitly when the engine does not use the default socket.

Replace the suite configuration with the container adapter:

```json
{
  "id": "claude-shell",
  "model": "<pinned model id>",
  "harness": "Claude Code 2.1.319; Docker shell catalog",
  "adapter": ["python3", "../scripts/eval_container.py"],
  "adapter_inputs": ["../scripts/eval_claude.py", "../scripts/eval_trace.py"],
  "settings": {
    "container_image": "sha256:<64 lowercase hex characters>",
    "claude_version": "2.1.319 (Claude Code)",
    "expected_served_models": ["<served model id>"],
    "credential_env": ["ANTHROPIC_API_KEY"],
    "effort": "high"
  }
}
```

Paths assume a manifest under `evals/`. Set the named credential in the environment before running; its value is never placed in the manifest or Docker argv. Use experiment-scoped credentials: shell code can read its own container environment, and the agent network is not an egress filter. OAuth experiments can name `CLAUDE_CODE_OAUTH_TOKEN` instead. No credentials are copied from personal configuration files.

A configuration with `container_image` also routes grading through the same pinned image with networking disabled. Python graders must declare imported helpers and fixture directories in `grader_inputs`. The transport preserves their relative layout. Graders should write scratch files under the container's temporary directory, since the submitted workspace is read-only.

Before an empirical run, verify the real engine, image, provider authentication, tool execution, and mount boundaries with a disposable case. The normal file adapter remains a distinct configuration; its results should not be pooled with shell results.

## Action traces

Each invocation saves provider JSONL while it runs, stderr, the effective prompt, and normalized `actions-N.json`. Normalized traces retain visible assistant text, tool requests, tool results, and observed successful skill-file reads. They omit hidden thinking. Raw provider logs may contain additional private data; keep them in ignored run directories.

A read request alone does not establish a successful read. A successful read does not establish comprehension or causal use. Explicit preload is recorded separately. Use traces to inspect where a successful and failed trial diverged, then test the resulting hypothesis on another task.

For resumed Claude sessions, cost is the final available session-cumulative estimate; turn costs must not be summed. Token usage is accumulated only when its scope is declared. Missing receipts remain unknown. Every invocation remains available in `result.json` under `attempts`.

## Scripted clarification

The bundled `evals/clarification.json` uses three versions of an export task. One omits a material preference, one states it, and one puts it in repository documentation. The default adapter is a synthetic oracle for plumbing checks.

```sh
python3 scripts/skill_eval.py plan evals/clarification.json \
  --output evals/runs/questions-plan.json --repeats 1
python3 scripts/skill_eval.py run evals/runs/questions-plan.json \
  --output evals/runs/questions
python3 scripts/skill_eval.py report evals/runs/questions
```

A task's `interaction` field names a private JSON packet:

```json
{"max_turns": 3, "response": "The team prefers JSON."}
```

The agent writes `clarification.json` with a nonempty `question` and ends its turn. The host records the question and current workspace changes, then supplies the fixed reply to the same trial session. The packet is never placed in the model request. Repeated questions consume the declared turn budget; exhausting it is a task failure, not an excluded infrastructure failure.

The grader receives the host-written receipt through `EVAL_INTERACTION_LOG`. Outcome correctness, question count, unnecessary questions, and asking before implementation are separate checks. Workspace changes are observed at turn boundaries; the receipt cannot prove that a file was never temporarily edited and restored. The grader does not match exact question wording. The finite script is suitable for this fixture; it does not simulate arbitrary stakeholders or prove that every question was relevant.

## Subtraction experiment

Prepare a candidate skill tree without changing the installed library:

```sh
python3 scripts/eval_subtract.py prepare --source skills \
  --output evals/runs/implement-candidate \
  --experiment evals/experiments/implement-self-review.json
```

The recipe removes exactly the named self-review section and records the hypothesis, source hashes, candidate hashes, removed-content hash, and changed path. The hypothesis is that the section may impose unnecessary process on small tasks; no benefit is assumed. The candidate deliberately lacks guidance that might help on complex changes, so include preservation cases as well as small tasks.

Use identical suite inputs for incumbent and candidate, changing only `skills_root` to the copied tree. Freeze both plans, run them, then use `skill_eval.py compare`. A public synthetic oracle can verify this flow but cannot choose the winning skill. Keep the source library unchanged until held-out outcomes support the change.
