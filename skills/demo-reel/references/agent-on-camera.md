# Filming an agent using the product

For a tool built for agents, the agent shot is the demo: a real session, a real prompt, real commands against the demo world. It is also the hardest acceptance test in the reel, because the agent will try every rough edge a new user would, faster, and on camera.

## What the agent takes found

Unifly's maintainer asked for exactly this shot ("what i really want is to see an agent using unifly") and five takes of a real Claude Code session followed. Each take was a test:

- **Take one escaped demo mode.** The agent ran `env -u UNIFI_DEMO_FLEET`, read the real config, and made one read-only call to a real controller, because it judged that a report from demo data "would be fiction". Auto permission mode let every call through. The maintainer caught it live, seconds before the recorder stopped. Secrets printed masked only because the agent chose table output.
- **Take two ran with manual permission prompts.** The maintainer objected within seconds: prompts stall the take and do not belong on camera.
- **Take three** was the first clean sandboxed run. It also showed the agent stumbling: a device lookup by name failed, two diagnostics were unavailable in demo mode, and it guessed JSON field names. Those became a fix PR (name and MAC lookup, demo answers, a JSON field guide).
- **Take four** could not inspect switch ports, which became another fix PR, dispatched 40 seconds after the take went idle.
- **Take five** is in the video: 62 seconds of agent work, one skill load and 13 shell calls, cut to 16 seconds on screen. One honest stumble stayed in ("the demo fleet doesn't support settings commands"), because it was true.

## The sandbox

`scripts/agent-take.sh` builds what the unifly takes ended up with, as one command:

- A throwaway studio directory as the agent's working directory, holding only the copied skills. Its path shows in the agent's header, so name it for the demo world (unifly's window read `claude · ~/neon-harbor`).
- A sandbox bin directory with only the allowed binaries, as the whole `PATH`.
- Empty `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`, `XDG_DATA_HOME` and `XDG_STATE_HOME`, so XDG-respecting products find no real configuration.
- `env -i`, passing only `HOME` (the agent's login lives there), the terminal variables, `LANG`, the sandbox paths, the demo's variables, and known auth variables when set (masked in every printout).
- An empty `ZDOTDIR`, so a zsh started by the agent's shell tool does not load the user's startup files.
- A studio prompt, appended to the system prompt: the demo environment is the whole environment, demo mode is intentional, and there is no need to look for other configuration. This was the maintainer's idea after take one ("a stealth addition to its system prompt").
- The agent runs as a child process, never with `exec`.

For Claude Code it adds, with every flag checked against `claude --help` (2.1.306):

| Flag or variable                       | Why                                                                                       |
| -------------------------------------- | ----------------------------------------------------------------------------------------- |
| `--permission-mode dontAsk`            | Allowlisted tools run; everything else is denied without a prompt. No auto, no bypass     |
| `--tools Bash,Skill` (from your rules) | Only the tools the rules name exist; without it a session exposed 24 tools, Read included |
| `--allowedTools RULE...`               | The allowlist, e.g. `Bash(unifly:*)`, `Bash(jq:*)`, `Skill(unifly)`                       |
| `--setting-sources project,local`      | No user settings, so no user hooks, plugins, or permissions                               |
| `--strict-mcp-config`                  | No MCP servers unless passed with `--mcp-config`                                          |
| `--append-system-prompt`               | The studio prompt                                                                         |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`     | No user or project CLAUDE.md                                                              |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`    | No memory from other sessions                                                             |

A live check of this setup on Claude Code 2.1.306 (print mode, a stand-in product): the session logged in, the allowlisted product ran with its demo variable, `cat /etc/hosts` was denied with "running in don't ask mode", the session exposed exactly Bash and Skill, and it loaded the studio's skill but none of the user's personal skills. One limit showed up: `Bash(echo:*)` did not cover `echo "$PATH"`, so commands with shell expansions are denied even when the command name matches a rule. Agents piping product output into `jq` need `Bash(jq:*)` too; unifly's take allowed exactly the product, `jq`, and the product's skill.

For Codex (0.163.0) the launcher uses `-C STUDIO -s read-only -a never` (or `--codex-sandbox workspace-write`) and writes the studio prompt to the studio's `AGENTS.md`, where Codex reads project instructions. Project skills go to `.agents/skills/`, the path the Codex binary lists. Codex has no per-command allowlist here. In a check with `codex sandbox` on macOS, its default policy blocked network access and writes outside the workspace but could read dotfiles under HOME, and user-level instructions under `CODEX_HOME` still load. Use the product's demo mode plus `--prove` probes to cover the rest.

## Prove it before rolling

```bash
scripts/agent-take.sh --prove --dir ~/neon-harbor --skill path/to/skills/unifly \
  --allow unifly --allow jq --env UNIFI_DEMO_FLEET=1 \
  --tool 'Bash(unifly:*)' --tool 'Bash(jq:*)' --tool 'Skill(unifly)' \
  --probe 'unifly config show' --probe-expect 'No profiles configured'
```

`--prove` builds the sandbox and checks that `PATH` holds only the allowed binaries, that no shell, network, or file tool resolves, that only the listed variables reach the take, and that the XDG directories are empty. Each `--probe` runs inside the sandbox with the demo variables removed, the way an agent escaping demo mode would run it, and must match `--probe-expect`. Unifly's version of this proof was the product reporting "No profiles configured" with demo mode stripped.

Read the notes `--prove` prints. HOME is real, so a product that reads a dotfile directly under HOME (not under an XDG directory) still finds it; a probe catches that, and the fix is in the product or a different `--home` with API-key auth. `PATH` is a soft brake, because the agent's shell may add system directories at startup; the allowlist is the hard one.

Then `--dry-run` prints the exact environment and command for the take, and a run without either flag launches it in the current terminal.

## Shooting the take

1. Start the camera on the terminal window, then launch `agent-take.sh` in it.
2. Type the prompt at a human cadence (see [capture.md](capture.md)). Write it the way a customer would: unifly's was "the crew says wifi on the roof deck keeps dropping, and dailies uploads crawl whenever the render farm syncs. dig into the studio network with unifly and give me the top five fixes, one line each".
3. Stop the recorder when the agent is idle on two checks in a row.
4. Read the whole transcript before keeping the take. Did it stay in the world? Did it present demo data honestly? What did it stumble on? Every stumble is a ledger row or a deliberate keep.
5. After the shoot, read and delete take transcripts that captured anything real (unifly deleted all five; one held the real controller's hostname), plus the studio and sandbox directories.

## In the edit

- Show the real time on every sped-up stretch: `assets/timer.html` renders a real-time pill with the current speed ([edit-render.md](edit-render.md)).
- Land at 1x before and after each speed-up, and hold the answer at 1x for 3.5 to 5 s so it can be read.
- Keep honest stumbles that are true and short. Cut repetition, never reorder steps.
- The caption states what happened ("Claude Code diagnoses the demo studio network, end to end"), not what the agent might do.
