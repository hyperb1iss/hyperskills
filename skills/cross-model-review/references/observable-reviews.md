# Observable Claude Reviews

Use the optional runner when a Claude CLI review needs progress visibility and durable recovery artifacts. A native host with adequate progress reporting can use its own tools. The runner requires Python 3.11 or newer and an installed Claude CLI.

## Launch and Observe

Write the complete brief to a file. Include the original request, exact scope, captured diff or revision, relevant project constraints, and permitted actions. Safe mode disables automatic project instruction discovery; the brief must carry the constraints the reviewer needs.

```bash
python3 <skill-dir>/scripts/run_claude_review.py \
  --prompt-file /absolute/path/review-brief.md \
  --cwd /absolute/path/repo --label cancellation-review \
  --auth-mode inherit
```

Choose authentication deliberately. The default `inherit` mode preserves the configured environment for API, proxy, or existing subscription authentication. Use `--auth-mode subscription` when the intended route is local subscription credentials and inherited `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` would select another route. That mode removes those variables only from the child environment; it does not configure or guarantee a subscription login.

The runner prints its review directory and status path before fingerprinting file contents or starting Claude. Retain the original shell session or process handle. Poll that handle using the host's supported wait parameters, and inspect saved activity separately:

```bash
python3 <skill-dir>/scripts/review_status.py /absolute/path/review-dir
python3 <skill-dir>/scripts/review_status.py /absolute/path/review-dir --json
```

The status describes the last observed event. An unchanged event count is not a failure verdict, and a saved `running` state is not proof the process remains alive. Check the original process and stderr before deciding it is stuck. Never start another reviewer solely because the host yielded or final text has not appeared.

## Scope and Freshness

By default, compare the entire Git worktree. For a narrower review, repeat `--scope` with literal repository-relative file or directory paths (no glob or Git pathspec expansion):

```bash
python3 <skill-dir>/scripts/run_claude_review.py \
  --prompt-file /absolute/path/review-brief.md --cwd /absolute/path/repo \
  --scope src/cancellation.py --scope tests/test_cancellation.py
```

The selected scope must cover the actual evidence the reviewer uses, including relevant callers and configuration. Scope selection controls change detection, not filesystem access. Absolute paths and paths escaping the worktree are rejected. Preserve the reviewed artifact while the reviewer reads it; independent work outside a deliberately scoped packet can continue.

The fingerprint includes staged content, unstaged content, and non-ignored untracked files. It compares launch and completion snapshots. Equal endpoints cannot prove files were unchanged between them, and ignored files, submodule contents, or external inputs need separate evidence. Unknown Git freshness is disclosed as unknown. Losing a previously available snapshot invalidates the result.

## Artifacts and Completion

The runner uses a unique private directory outside the worktree. A caller-supplied `--review-dir` must be empty and outside that tree. The directory is restricted to its owner.

| File           | Purpose                                                                                    |
| -------------- | ------------------------------------------------------------------------------------------ |
| `prompt.md`    | Copy of the actual submitted brief                                                         |
| `meta.json`    | Launch context, prompt digest, process identity, authentication mode, and initial snapshot |
| `events.jsonl` | Raw event stream retained for diagnosis                                                    |
| `status.json`  | Atomically replaced activity and terminal state                                            |
| `stderr.log`   | Startup, permission, authentication, and transport diagnostics                             |
| `final.md`     | Nonempty text from a successful terminal result event                                      |

A usable result requires successful child completion and a successful, non-error result event. Missing or malformed results cannot become approval. Interpret wrapper status before consuming a saved final file:

| Wrapper outcome          | Action                                                                                 |
| ------------------------ | -------------------------------------------------------------------------------------- |
| Exit 0, state `complete` | Read the report and its limitations; process completion is not reviewer approval       |
| Exit 90, state `stale`   | Compare the artifact delta and obtain the required new review                          |
| Exit 91, state `failed`  | Inspect the child exit/result error; no usable completed result was obtained           |
| Exit 127                 | Resolve the startup failure before relaunching                                         |
| Interrupt or termination | Confirm the owned process group stopped; retain partial evidence without granting PASS |

On POSIX systems, cancellation targets the owned process group even if its leader has exited. Other platforms support direct-child termination only; use a host supervisor when descendant cleanup is required.

The reviewer receives only Read, Glob, and Grep, with noninteractive permission denial. Safe mode, restricted tools, and explicit MCP denial remove common side effects; they are not a filesystem or network sandbox. The runner preserves configured model selection and disables resumable session persistence. Raw external logs still exist and may contain source excerpts or reasoning blocks. Use compact activity for routine updates, never expose hidden reasoning, and apply the project's retention policy after disposition.

The helper's deterministic tests use a fake Claude executable. They verify lifecycle and protocol handling, not a model's review quality. For a live check, observe activity before completion, reap the original process, inspect terminal status, and compare the saved prompt and final artifact with the intended request.

The [Claude CLI reference](https://code.claude.com/docs/en/cli-reference) and [programmatic usage guide](https://code.claude.com/docs/en/headless) document the streaming and permission surfaces. Flags were checked against local Claude Code 2.1.261 on 2026-09-04; inspect current help when the installed CLI differs.
