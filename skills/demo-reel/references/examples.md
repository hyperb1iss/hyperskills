# Worked examples

Two reels made with this method on open-source projects, in October 2026. Both started as "make a demo video" and ended as a run of merged fixes. The numbers come from each project's PRs and from the session records behind them.

## Hypercolor: a 60 s 4K60 reel for an RGB lighting engine

[Hypercolor](https://github.com/hyperb1iss/hypercolor) is a Rust daemon that drives RGB devices from HTML effects through a GPU compositor, with a web UI, a TUI, and a CLI. The opening brief was "we build the video, and in the process of perfecting it we fix every issue along the way."

**The shot list as tests.** A show runner performed a timecoded show on the live rig (24 devices, 7,483 LEDs) and judged every shot against the configured 60 FPS. The first dress rehearsal passed 0 of 8 shots: a 60 Hz control ramp acked as slowly as 6,566 ms, a montage cut produced an 84 ms frame, and a drop cut dipped to 44.2 FPS. A ledger of 30 issues followed, each tagged with the shot it blocked. One early "failure", a 2.2 s first cut, was the runner matching events across two clocks; the real number was about 71 ms, and the runner's timing fix moved into the product's wire protocol.

**What the reel caught,** each merged as a PR found by the rehearsal or the reel:

| PR                                                        | Finding                                                                                                    |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| [#421](https://github.com/hyperb1iss/hypercolor/pull/421) | A live control change cost redundant durable writes; a named-scene change fell from 16.0 ms to 4.4 ms      |
| [#427](https://github.com/hyperb1iss/hypercolor/pull/427) | The shipped beat threshold detected 151 beats against 32 kicks, so effects strobed on hats; default raised |
| [#415](https://github.com/hyperb1iss/hypercolor/pull/415) | False hard stalls and a duplicate page load on every effect cut                                            |
| [#414](https://github.com/hyperb1iss/hypercolor/pull/414) | A fingerprint change split display zones, so a pump LCD lost its face                                      |
| [#413](https://github.com/hyperb1iss/hypercolor/pull/413) | An older UI lost its whole Settings page against a newer daemon                                            |
| [#420](https://github.com/hyperb1iss/hypercolor/pull/420) | Malformed requests got plain-text errors and a scene read could not be written back                        |
| [#419](https://github.com/hyperb1iss/hypercolor/pull/419) | Clock steps hid faults in the wrong shot; messages now carry a monotonic stamp                             |
| [#423](https://github.com/hyperb1iss/hypercolor/pull/423) | Frames a device declined were counted as delivered                                                         |
| [#416](https://github.com/hyperb1iss/hypercolor/pull/416) | A spec for truthful health and hold-then-swap cuts, from rehearsal measurements                            |

The work also produced three byproduct fixes: a flaky soft-stall test ([#424](https://github.com/hyperb1iss/hypercolor/pull/424)), a build cache that grew to 391 GB and filled the disk ([#425](https://github.com/hyperb1iss/hypercolor/pull/425)), and seven dependency advisories found while merging ([#426](https://github.com/hyperb1iss/hypercolor/pull/426)).

**The human bar.** A first finished cut (two 1080p versions built from real-time screen recordings) got "it did okay but i'm not wild about the result": not 4K, jittery effects, wrong fonts, a low-resolution canvas, "kinda meh" content. The recorder's receipts counted 3,409 captured frames for 6,425 encoded ones, from which nearly half the encoded frames were inferred to be repeats; no one measured the repeats directly. The rebuild rendered every frame offline as a pure function of film time: effect pages on a virtual clock (Date, `performance.now`, seeded `Math.random`, queued rAF) composited in one headless Chromium at 3840x2160, raw frames piped into ffmpeg with no temp files, 3,600 frames in 203 s. Real inputs stayed real: the effects were the SDK's built pages, the audio reactivity came from the engine's own analyzer, the LED layout from the engine's spatial model, the app panes were 4K screenshots of the live UI. Typography, camera moves, and an original score synthesized from code were composed, and labeled as composed.

**Verification.** An independent verifier failed the rebuilt pipeline on missing in-stream color tags, shots upscaled up to 3.5x, and a camera shake stepping at 24 Hz; all were fixed before delivery. On-screen claims were corrected: "EVERY BRAND." became "12 BRANDS." and then a list without a count, because supported brands keep growing.

**What went wrong.** Two 4K masters crashed (renderer memory held by `fetch` bodies, then GPU buffers held by removed iframes), the build cache filled the disk, parallel builds slowed the live rig until they ran under `nice`, and a commit-cost A/B on tmpfs measured nothing. Each is in [gotchas.md](gotchas.md).

**Deliverables.** A 10-bit HEVC master (3840x2160, 60 fps, bt709), an H.264 4K copy, a 1080p social cut, and a poster frame, with a receipt hashing the commit, master, score, and fonts.

## Unifly: a promo with a sandboxed agent take

[Unifly](https://github.com/hyperb1iss/unifly) is a Rust CLI and terminal UI for UniFi networks, built for humans and AI agents. Its 54.5 s 1080p30 promo opens the README and ships with [v0.11.0](https://github.com/hyperb1iss/unifly/releases/tag/v0.11.0).

**The demo world.** [#53](https://github.com/hyperb1iss/unifly/pull/53) added `--demo-fleet`: a seeded, fully offline network for the TUI and a curated set of read-only CLI commands. Before it, demo mode only sanitized a real controller's data, so screenshots depended on someone's home network. Building the fleet found six bugs affecting real controllers (a topology view wiring every switch to every AP, an always-empty NAT tab, a chart reading milliseconds as seconds, an out-of-order event backlog, a connect and disconnect hang, a documented environment form that was rejected), and an independent review caught that Settings could escape the fleet to a real controller.

**What shooting found:**

| PR                                                  | Finding                                                                                                                               |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [#54](https://github.com/hyperb1iss/unifly/pull/54) | List output came out in hash-map order, different every run, so paging could overlap or skip rows                                     |
| [#55](https://github.com/hyperb1iss/unifly/pull/55) | The hero WAN chart showed a black band, flashed, and leaked a kitty image per refresh (25,393 missing-image warnings before, 0 after) |
| [#56](https://github.com/hyperb1iss/unifly/pull/56) | Clicking Sponsor corrupted the display: the browser opener inherited the TUI's terminal                                               |
| [#59](https://github.com/hyperb1iss/unifly/pull/59) | Fixed-width tables clipped real values and headers                                                                                    |
| [#58](https://github.com/hyperb1iss/unifly/pull/58) | From agent take three: no lookup by name, missing demo diagnostics, guessed JSON fields                                               |
| [#60](https://github.com/hyperb1iss/unifly/pull/60) | From agent take four: switch ports unavailable in demo mode; exports pinned to a fixed demo instant                                   |
| [#65](https://github.com/hyperb1iss/unifly/pull/65) | The README preview was black because the cut faded in; the title card now fills frame 0                                               |

**The agent take.** Five takes of a real Claude Code session against the fleet. Take one, in auto permission mode, escaped demo mode: the agent unset the fleet variable, read the maintainer's real config (secrets printed masked only because it chose table output), and made one read-only call to the real controller. The maintainer caught it live. Take two used manual permission prompts and was killed within seconds, then relaunched in auto mode. Takes three to five, including the one in the promo, ran in auto mode with an allowlist of `Bash(unifly:*)`, `Bash(jq:*)` and `Skill(unifly)`, an empty XDG config, a sandbox bin dir, and an appended studio prompt; the published promo's busiest agent frame shows "Allowed by auto mode classifier" lines. The kept take is 62 s of agent work cut to 16 s, with one honest stumble left in. This skill's `scripts/agent-take.sh` builds on that setup and hardens it (dontAsk mode, a throwaway HOME, a dedicated login dir, a settings file that disables auto and bypass modes); see [agent-on-camera.md](agent-on-camera.md). The dontAsk hardening was checked in print mode, not in a filmed take.

**Capture.** A private Ghostty instance at a fixed grid, driven by its automation tool, captured as screenshots because the WAN chart is a kitty-graphics image that tmux text capture cannot show. The prompt was typed in three-character chunks 40 ms apart; an idle watcher stopped the recorder. A Python renderer (Pillow and numpy) composed the promo frame by frame and piped raw frames into ffmpeg; its keyframe-only mode rendered review stills in about 6 s.

**What went wrong.** The agent escape, a manual-permission take, a `pkill -f` that killed the agent's own shell, a RAM-backed `/tmp` filled by verifier builds, a merge that deleted the worktree the capture used, and a release run that failed on an unrelated race (fixed, then released with nothing half-published). See [gotchas.md](gotchas.md).
