# Filming an agent using the product

For a tool built for agents, the agent shot is the demo: a real session, a real prompt, real commands against the demo world. It is also the hardest acceptance test in the reel, because the agent tries every rough edge a new user would, faster, and on camera.

## What agent takes find

Treat each take like any other shot: a stumble is a ledger row.

- **The agent may leave the demo world on purpose.** A careful agent that notices demo mode can decide its answer "would be fiction", unset the demo variable, read the real configuration, and call the real service. Under an auto-approving permission mode nothing stops it. The real-world case in [examples.md](examples.md) caught this live, seconds before the recorder stopped.
- **Manual permission prompts stall the take** and read badly on camera.
- **Rough edges become fixes.** Failed lookups by name, diagnostics missing from demo mode, and guessed JSON field names are product bugs for agent users; each is worth a fix and a reshoot.
- **Keep honest stumbles that are true and short.** An agent saying "the demo doesn't support this command, so I couldn't check" is a fine thing to leave in.

## The sandbox

`scripts/agent-take.sh` builds a set of brakes in one command. It is not isolation: `env -i` does not stop a command from running any system binary by its absolute path, and the OS keychain or secret service is reached by user identity, not HOME. What it sets up:

- **A throwaway studio** as the agent's working directory, holding only the copied skills (links that resolve outside a skill are refused, and the rest are copied as files). Its path shows in the agent's header, so name it with `--dir`.
- **A throwaway HOME** and empty `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME` and `XDG_STATE_HOME`, so neither dotfiles nor XDG config from the real account are there to find.
- **A dedicated login dir** for the agent (`CLAUDE_CONFIG_DIR` for Claude Code, `CODEX_HOME` for Codex), set up once with `--login`, so the agent signs in without the real HOME or its normal config. `--real-home` restores the old behavior with a warning; avoid it.
- **A bin directory with only the allowed binaries** as the whole `PATH`. An agent installed as a script (an npm package starts with `#!/usr/bin/env node`) is run through its interpreter's absolute path; the interpreter never joins `PATH`.
- **`env -i`** with only the terminal variables, `LANG`, the sandbox paths, the demo's variables, and API key variables when set (masked in every printout), plus an empty `ZDOTDIR` so a zsh started by the agent's shell tool skips the user's startup files.
- **A studio prompt** appended to the system prompt: the demo environment is the whole environment, demo mode is intentional, and there is no need to look for other configuration.
- **Cleanup.** The studio and sandbox are deleted when the script exits, on failure and on a signal too, unless `--keep` is given. The agent's own transcripts stay in its login dir; read them before sharing.
- **No `exec`.** The agent runs as a child, so the terminal the camera films survives the agent exiting.

For Claude Code the launcher writes `.claude/settings.json` into the studio and passes the same file with `--settings`. Every key and value type below was checked against the 2.1.306 binary's settings schema, because a misspelled key is ignored silently:

| Setting or flag                                                         | Effect                                                                     |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `permissions.defaultMode: "dontAsk"`, and the flag                      | Allowlisted tools run; everything else is denied without a prompt          |
| `permissions.allow` (from `--tool`)                                     | The allowlist, e.g. `Bash(acme:*)`, `Bash(jq:*)`, `Skill(acme)`            |
| `permissions.deny: ["WebFetch", "WebSearch"]`                           | No web tools, even if a rule would allow them                              |
| `permissions.blockReadsOutsideWorkingDirectories`                       | File tools and recognized file-reading commands stay inside the studio     |
| `permissions.disableBypassPermissionsMode: "disable"`                   | Bypass mode cannot be entered                                              |
| `disableAutoMode: "disable"` (top level and under `permissions`)        | Auto mode cannot be entered                                                |
| `--tools` (from your rules)                                             | Only the tools the rules name exist; without it a session exposed 24 tools |
| `--setting-sources project,local`, `--strict-mcp-config`                | No user settings, hooks, or MCP servers                                    |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | No CLAUDE.md files and no memory from other sessions                       |

Limits of that guard. The read block covers the file tools (Read, Grep, Glob, LSP) and the Bash commands Claude Code recognizes as file reads. A command an allow rule approves can still read outside the studio: `jq . ~/.config/x` passes under `Bash(jq:*)`, so allow only the commands the take needs. Rules also do not cover shell expansions: in a print-mode check, `Bash(echo:*)` did not allow `echo "$PATH"`.

How much of this was exercised: on Claude Code 2.1.306 in print mode, with a stand-in product, `dontAsk` denied an unlisted command without a prompt, `--tools` left exactly Bash and Skill, the studio skill loaded and the user's personal skills did not. A full interactive take and a fresh `--login` were not run while writing this skill; rehearse one take before rolling. Claude Code ignores a project settings file's allow rules in an untrusted folder, so the launcher marks the studio trusted in the login dir's `.claude.json` (`projects[PATH].hasTrustDialogAccepted`, the key 2.1.306 names when it refuses; it never edits the real `~/.claude.json`). A print-mode check confirmed the refusal without it and none with it. A fresh login dir may still show onboarding screens; answer them in a rehearsal take.

For Codex (0.163.0) the launcher uses `-C STUDIO -s read-only -a never` (or `--codex-sandbox workspace-write`), writes the studio prompt to the studio's `AGENTS.md`, and copies skills to `.agents/skills/`. Codex has no per-command allowlist here; its sandbox is the brake. In a check with `codex sandbox` on macOS, the default policy blocked network access and writes outside the workspace but could read files under HOME. Before every take and proof the launcher runs `codex sandbox -- true` and stops with exit 3 if the sandbox cannot start (on Linux, bubblewrap fails on hosts without unprivileged user namespaces). It never falls back to full access.

## Prove it before rolling, with fixtures

```bash
scripts/agent-take.sh --login                    # once per machine, off camera
scripts/agent-take.sh --prove --allow acme --env ACME_DEMO=1 --skill path/to/skills/acme \
  --tool 'Bash(acme:*)' --tool 'Skill(acme)' --probe 'acme config show' --probe-expect 'no config'
```

`--prove` builds the sandbox in a fresh temp studio and reports:

- the agent's launch command resolves without the sandbox `PATH`, and the Codex sandbox starts;
- `PATH` holds only the allowed binaries, every allowed script can find its interpreter, and no common shell, network, or file tool is on `PATH` (absolute paths still run; the allowlist is the guard);
- only the listed variables reach the take, the studio holds no symlinks, and the XDG dirs and throwaway HOME are empty;
- each `--probe`, run inside the sandbox with the demo variables removed (as an escaping agent would), matches `--probe-expect`;
- nothing was written to the XDG dirs or the HOME during the probes. Some CLIs migrate a legacy config file on first run; a probe that triggers that fails the proof, and only the written file names are printed.

Then it deletes what it built. What a passing proof establishes: in this sandbox, with the demo variables removed, the product found no configuration in the places the probes exercised and wrote none. It does not establish that the product cannot reach a keychain, a network service, or a file it reads by absolute path.

Run probes against fixtures: a stand-in product, a fixture HOME, a fake login. Never point a probe at a real account or real configuration; a probe that finds one has already copied it somewhere.

`--dry-run` prints the exact environment, command, and settings file, and a run without either flag launches the take in the current terminal.

## Shooting the take

1. Start the camera on the terminal window, then launch `agent-take.sh` in it.
2. Type the prompt at a human cadence (see [capture.md](capture.md)), the way a customer would ask: a symptom and a goal, not a list of commands.
3. Stop the recorder when the agent is idle on two checks in a row.
4. Read the whole transcript before keeping the take. Did it stay in the world? Did it present demo data honestly? What did it stumble on? Every stumble is a ledger row or a deliberate keep.
5. Delete transcripts that captured anything real.

## In the edit

- Show the real time on every sped-up stretch: `assets/timer.html` renders a real-time pill with the current speed ([edit-render.md](edit-render.md)).
- Land at 1x before and after each speed-up, and hold the answer at 1x for 3.5 to 5 s so it can be read.
- Cut repetition, never reorder steps.
- The caption states what happened ("the agent finds the offline device from one prompt"), not what an agent might do.
