# Reviewer CLI Flag Reference

Lookup material for scoping what a reviewer can read, write, and execute. SKILL.md carries the defaults you should reach for; this file carries the full surface for the cases the defaults don't cover.

**The installed CLI outranks this file.** Version-pinned flags are the fastest-rotting content a skill can carry, and a documented `--sandbox` form was already rejected by a newer codex build in the field. When `--help` disagrees with a table here, the CLI wins; flag the skill for a patch.

## Codex sandbox modes

`codex exec` and `codex review` accept `--sandbox <mode>`:

| Mode                 | Read | Write    | Network | Use for                                 |
| -------------------- | ---- | -------- | ------- | --------------------------------------- |
| `read-only`          | ✓    | ✗        | ✗       | Pure review (default for review work)   |
| `workspace-write`    | ✓    | cwd only | ✗       | Review + apply suggested fixes          |
| `danger-full-access` | ✓    | ✓        | ✓       | Last resort; explicit user request only |

## Codex flags worth knowing (as of Jul 2026)

| Flag                                         | When                                                                                     |
| -------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `--skip-git-repo-check`                      | Running from `/tmp` or any non-repo dir (trips the git trust check)                      |
| `--add-dir <DIR>`                            | Extend read access to another path                                                       |
| `-C <DIR>` / `--cd <DIR>`                    | Run in another worktree without `cd`                                                     |
| `--ephemeral`                                | One-shot session, no persistence                                                         |
| `--full-auto`                                | Alias for `--ask-for-approval never --sandbox workspace-write`; only when applying fixes |
| `--dangerously-bypass-approvals-and-sandbox` | Last resort; explicit user request only                                                  |
| `--json` / `--output-last-message`           | Capture the verdict; read-only sandboxes silently fail to write a requested report file  |
| `-c model_reasoning_effort="xhigh"`          | Spec/RFC review only (see SKILL.md, Effort Override Policy)                              |

Scope flags for `codex review` itself (`--base`, `--commit`, `--uncommitted`) are non-optional and live in SKILL.md, not here.

## Claude permission flags (`claude -p`)

| Flag                                          | When                                            |
| --------------------------------------------- | ----------------------------------------------- |
| `--allowedTools "Read,Glob,Grep,Bash(git *)"` | Standard read-only review toolset (recommended) |
| `--add-dir <PATH>`                            | Read access outside cwd                         |
| `--no-session-persistence`                    | Sanity pings; one-shot calls                    |
| `--output-format text` / `json`               | Capture for parsing                             |
| `--dangerously-skip-permissions`              | Last resort; explicit user request only         |

Add `Bash(rg:*)` when the reviewer needs grep across files. Resist write tools unless the review explicitly applies fixes.

**One guarded write opt-in is field-proven.** The brief may allow "do not modify files unless you find a real defect and can fix it surgically; if you do edit, list exact files changed" — real defect, surgical fix, disclosed in the verdict. Anything looser turns a reviewer into an unsupervised second author.
