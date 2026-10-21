---
name: demo-reel
description: Use this skill when making a demo reel, demo video, product video, promo reel, or screen recording of an app, especially when the reel should double as an acceptance test of the real product. Activates on mentions of demo reel, demo video, product video, promo reel, promo video, record a demo, film the app, film an agent using the product, screen recording for a demo, shot list, use the demo to test, acceptance test by video, 4K render, contact sheet, or verify the MP4. Covers shot lists as acceptance tests, seeded demo worlds, deterministic browser and terminal capture, sandboxed agent takes, ffmpeg editing without drawtext, and output verification. Skip it for a one-off trim, conversion, or GIF of an existing clip.
---

# Demo Reel

Use the act of making a demo reel to test the product. A reel shows what a customer would see, shot by shot, on the real thing; shooting it end to end is an acceptance test a mock cannot pass. Every failed shot is a bug to chase, not noise to retry past. The finished reel is the evidence and the promo at once.

[references/examples.md](references/examples.md) tells the story of two reels made this way and the fixes they found.

## Pointed here by URL?

If this skill is not installed, fetch it; every script resolves its own paths. The skill lives on the repository's `main` branch.

```bash
DR="$(mktemp -d)/hyperskills"
git clone --depth 1 --branch main https://github.com/hyperb1iss/hyperskills "$DR"
DR="$DR/skills/demo-reel"
bash "$DR/scripts/doctor.sh"        # every failure prints its fix
bash "$DR/scripts/selftest.sh"      # offline proof the toolkit works here
```

To install it instead: `npx skills add hyperb1iss/hyperskills --skill demo-reel`, or the hyperskills Claude Code plugin. Installed copies keep the same layout; resolve `scripts/`, `assets/`, and `references/` relative to this file. Keep takes and renders in the user's project, never in the clone or a RAM-backed `/tmp`.

The only system dependency is ffmpeg (with ffprobe). Browser capture needs Node 18+ and Playwright with Chromium; `scripts/doctor.sh` prints the install commands for this machine. Nothing needs ffmpeg's `drawtext`, and nothing needs Remotion (its license requires a paid company license for for-profit organizations with more than 3 employees).

## The loop

1. **Write the shot list:** what a customer would see, shot by shot. Every shot is an acceptance test with a budget a script can judge (frame time against the target FPS, ack latency, a correct answer).
2. **Shoot it on the real thing:** the whole product, end to end, nothing mocked.
3. **A shot fails:** a failed take is a finding. Log it in the failure ledger with the footage and numbers before anything else.
4. **A fix lane:** one agent owns one failure until the cause is proven.
5. **The fix, with evidence:** footage and commands a reviewer can rerun.
6. **Reshoot:** the whole reel again, not only the fixed shot, until a full take passes.

[references/method.md](references/method.md) has the shot-list format, the ledger, a lane's definition of done, and the reshoot policy.

## Steal this

- **Write the shot list.** Every shot is an acceptance test; a script judges each against its budget.
- **Shoot it on the real thing.** Composed elements are fine when labeled; faked product behavior is not.
- **Build the world the demo needs.** Seeded, offline, reproducible demo data, the same every take ([references/demo-world.md](references/demo-world.md)).
- **Cameras on every run.** The footage is the evidence and the promo; keep every take.
- **Every failed shot starts a lane.** Root cause, a fix with evidence, then reshoot.
- **Check what the pass measured.** A "pass" measured on a half-loaded page is not a pass ([references/verify.md](references/verify.md)).
- **A second opinion.** Independent verifier agents, a different model family where available.
- **Brakes, and a human bar.** A sandbox for any agent on camera; a human who can say "not wild about the result".

## Pipeline

Each stage has an exit check. Re-enter an earlier stage when one fails.

| Stage                   | Do                                                                                                                                    | Exit check                                                           |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| 1. Preflight            | `scripts/doctor.sh`; `scripts/selftest.sh` once per machine                                                                           | No failures; the browser cases ran if the reel needs a browser       |
| 2. Storyboard           | The shot list: shot, claim, pass condition, how it is measured, every on-screen fact and its source                                   | Every shot has a measurable pass and every caption has a source      |
| 3. Demo world           | Seeded, offline data built into the product; isolate live state                                                                       | Two launches with one seed match; nothing real on screen             |
| 4. Shots                | One script per shot: browser steps, terminal keystrokes, or an agent prompt                                                           | A rehearsal runs end to end and records its own measurements         |
| 5. Takes                | Shoot the whole list ([references/capture.md](references/capture.md), [references/agent-on-camera.md](references/agent-on-camera.md)) | Every shot judged against its budget; takes numbered and kept        |
| 6. Ledger and fix lanes | One row per failed shot; one owner per row; fix with evidence; independent check                                                      | Every row fixed and reshot, or parked with a named decision          |
| 7. Edit                 | Cut on the passing full take ([references/edit-render.md](references/edit-render.md))                                                 | Pacing rules hold; every sped-up stretch carries the real-time timer |
| 8. Stills check         | `scripts/contact-sheet.sh` at every cut, caption, and zoom, before any long render                                                    | Nothing clipped, stale, private, half-loaded, or untrue              |
| 9. Render               | 4K masters through one color chain                                                                                                    | Render finished; frames streamed, no temp-file pile-up               |
| 10. Verify              | `scripts/verify-mp4.sh` per deliverable; contact sheets of the files; an independent verifier                                         | Exit 0 with the written expectations; the verifier tried to fail it  |
| 11. Deliver             | Masters, a 1080p cut, a poster, the contact sheet, a receipt of what was checked, to the user's chosen place                          | A human watched it and the ledger is closed                          |

## Commands

Paths are relative to this skill's directory (`$DR` after the clone above). Run from the user's project with full paths, so takes and renders land there.

```bash
scripts/doctor.sh [--out DIR] [--no-browser] [--json]
scripts/selftest.sh                                  # 0 when every case that ran passed

# Browser takes and HTML-rendered titles, captions and timers: deterministic, 4K by default.
node scripts/capture-web.mjs --url URL --seconds 8 --fps 60 --out take.mp4 --json
node scripts/capture-web.mjs --still card.png --at 1200 --url 'assets/card.html#title=Every%20light.'
node scripts/capture-web.mjs --transparent --frames timer/ --seconds 16 \
  --url 'assets/timer.html#map=0:0,1.5:1.5,6:46.5,16:56.5'

# An agent on camera, sandboxed. Sign in once, prove with fixtures, dry-run, then shoot.
scripts/agent-take.sh --login                     # once: a login dir just for takes
scripts/agent-take.sh --prove --allow acme --env ACME_DEMO=1 --skill path/to/skills/acme \
  --tool 'Bash(acme:*)' --tool 'Skill(acme)' --probe 'acme config show' --probe-expect 'no config'
scripts/agent-take.sh --dry-run ...   # same options; prints env, argv and settings
scripts/agent-take.sh --dir ~/example-studio ...  # launches in this terminal

# Review and verify.
scripts/contact-sheet.sh --at 0,2,10.4,15 reel.mp4 review/cuts.png
scripts/verify-mp4.sh --expect-size 3840x2160 --expect-fps 60 --expect-duration 60 --max-freeze 6 reel.mp4
```

`acme` stands for the user's product: its CLI, its demo variable, its skill. Prove the sandbox with fixtures and stand-in tools, never by pointing a probe at a real login or real configuration. A maximum freeze longer than the longest deliberate hold catches a reel that stalls.

Every script takes `--help`, prints JSON with `--json` where an agent loops on it, and uses stable exit codes: 0 ok, 1 a check failed, 2 usage, 3 a dependency is missing, 4 bad input or a failed step (`capture-web.mjs` adds 5 for an encoder failure). `scripts/agent-take.sh` uses only flags checked against Claude Code 2.1.306 and Codex 0.163.0 `--help`, and settings keys checked against the Claude Code binary's settings schema; recheck on newer versions.

## House taste

- **4K and sharp.** 3840x2160, each rendered frame a function of film time; 1080p is the social cut, not the master.
- **Real footage, real clock.** Every sped-up run shows a real-time timer; never reorder events, never splice two runs under one timer.
- **Sections breathe.** A caption stays up at least 1 s plus a third of a second per word. Land at 1x for about 1.5 s before and after a speed-up. Hold payoffs 3.5 s or more. Nothing shorter than about 1.2 s except a deliberate flash.
- **Zooms are rare and shallow,** about 1.1 to 1.3x, only to make something readable.
- **Claims on screen are measured,** or computed from the product's own data.
- **Nothing private on screen:** fictional demo data, persona accounts, no hostnames, tokens, or real customers.
- **Open on a composed title card,** because frame 0 is the preview.
- **Fonts and color carry the brand;** tag the stream bt709 so the colors survive players.

## References

| File                                                           | Read it for                                                                                  |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| [references/method.md](references/method.md)                   | The loop in depth, shot-list and ledger formats, a fix lane's definition of done, reshooting |
| [references/demo-world.md](references/demo-world.md)           | Seeded offline demo data, demo writes, live hardware, web apps, keeping the agent inside     |
| [references/capture.md](references/capture.md)                 | Choosing a camera, 4K browser takes, deterministic web animation, terminals, typing, idling  |
| [references/agent-on-camera.md](references/agent-on-camera.md) | Filming an agent: the sandbox, the flags, the proof, shooting and cutting the take           |
| [references/edit-render.md](references/edit-render.md)         | Tested ffmpeg recipes: color chain, cuts, speed with a timer, fades, zooms, cards, encodes   |
| [references/verify.md](references/verify.md)                   | File contracts, stills review, true claims, checking what a pass measured, second opinions   |
| [references/gotchas.md](references/gotchas.md)                 | Traps worth knowing before the first take, by area                                           |
| [references/examples.md](references/examples.md)               | Two real reels as stories: what each caught, with links to the PRs                           |

## What This Skill is NOT

- Not a video editor tutorial. A trim, a format conversion, or a GIF of an existing clip needs plain ffmpeg and no shot list.
- Not permission to fake the product. Composed titles, music, and renders of real data are fine; staged product behavior is not.
- Not a substitute for the product's test suite. The reel finds what suites miss; the fixes still land with tests.
- Not a way around the user's authority. Publishing, merging fixes, or posting the reel follows the user's normal approvals; filming an agent never means loosening its permissions.
