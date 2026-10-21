# Gotchas

Traps that real reels paid for, plus the ones this skill's scripts were built around.

## The machine

- **Chromium renderer memory at 4K.** Posting each frame out of the page with `fetch` kept every POST body in renderer memory until garbage collection (about 33 MB a frame at 4K, 16 GB by frame 2000), and Chromium crashed; the orphaned renderer needed `SIGKILL`. Stream frames over a channel that does not retain them (screenshots or a WebSocket with one-at-a-time acknowledgement), and watch renderer memory on the first long render.
- **Removed iframes keep GPU buffers.** The second master failed near frame 2100 when effect iframes, removed from the page, kept their GPU buffers and filled a 12 GB card. Release GPU resources explicitly when a shot ends, and sample GPU memory during the first full render.
- **tmpfs makes fsync free,** so an A/B of anything that writes durably shows no difference there. Benchmark on the disk the product uses.
- **RAM-backed `/tmp` loses deliverables and fills fast.** Parallel verifier builds can fill a 32 GB tmpfs until tool output fails with ENOSPC. Keep takes, renders, and receipts on disk.
- **Build caches fill the disk.** A shared incremental build cache can grow to hundreds of GB over a shoot with parallel lanes. Check free space before a render (`doctor.sh` does) and after a day of parallel builds.
- **Protect the live system.** Five parallel compile lanes pushed load to 60 on 28 cores and dropped the live daemon from 60 to 45 FPS during a rehearsal. Run builds and renders at `nice -n 19` when the product under test shares the machine.
- **A shared build cache can link the wrong worktree's build,** producing a false test failure.

## Processes and shells

- **`pgrep -f` and `pkill -f` match your own shell.** A watch loop can wait forever on its own command line, and a `pkill -f` can kill the shell that ran it. Match on an exact PID file or a name that only the target has.
- **`exec` takes the window with it.** A take launched with `exec` closed the capture window and terminal instance when it exited.
- **ffmpeg reads standard input.** Without `-nostdin` it consumes the rest of a script, a heredoc, or a `while read` loop.
- **`-t` after `-i` limits the output.** In a speed change, it sped up the whole rest of the take.
- **Seeking past the end writes nothing and reports no error.** `contact-sheet.sh` clamps to the last frame and says so.
- **zsh autocorrect** can prompt before a take starts; launch takes from a clean shell.
- **Bash 3.2 on macOS** cannot parse a `case` statement inside `$( )`; scripts that must run under `/bin/bash` move that logic into a function. Run `/bin/bash scripts/selftest.sh` to prove it.
- **`gh pr merge --delete-branch` deletes the local worktree** for that branch, including any build output a capture depended on.

## Capture

- **Playwright's installed clock keeps flowing** until `pauseAt`, and its faked `performance.now()` and rAF timestamps drifted 0 to 2 ms from `Date.now()` between runs. `capture-web.mjs` pauses the clock and owns rAF and `performance.now()`.
- **CSS and Web Animations ignore the fake clock.** Pin them to film time after every step.
- **The first raster after pinning** differed by a sub-pixel between runs; discard one pre-roll frame.
- **A cold GPU process blanks canvases.** A canvas created while Chromium's GPU process is still starting showed as a white box for its first frames. Warm the GPU with a WebGL readback before loading the page.
- **Playwright's `recordVideo` is small and real-time.** It defaults to the viewport scaled to fit 800x800.
- **tmux text capture cannot show kitty-graphics images.** Film a real terminal window.
- **A TUI may drop the first keypress** after launch; send a throwaway key.
- **Hiding with `display: none` collapses layout;** use `visibility: hidden` to blank an element in place.
- **A 4K overlay on a 1080p clip lands off the frame** without an error. Render overlays at the edit's size.

## Agents on camera

- **Auto permission mode let an agent escape demo mode,** read real configuration, and call a real controller. Use an allowlist with Claude Code's `dontAsk` mode, and prove the sandbox first.
- **Manual permission prompts stall the take** and read badly on camera.
- **An allowlist rule does not cover shell expansions.** `Bash(echo:*)` did not allow `echo "$PATH"` in dontAsk mode.
- **Demo variables are a convention, not a wall.** `env -u DEMO_VAR` removes them; make the real configuration unreachable instead.
- **Take transcripts persist outside the studio.** Claude Code saves them under the real home; read them and delete any that captured something real.
- **An agent's helper lanes can touch the real system too.** A fix lane may run one quick command against the real service to check its work. Brief every lane to use the demo world and mocked tests only.
- **A proof can copy what it proves absent.** Pointing a probe at a real account lets a CLI migrate its legacy config, keys included, into the sandbox's XDG dir. Prove with fixtures and stand-in tools; `agent-take.sh --prove` fails on any write during probes, names files without printing them, and deletes its dirs.
- **npm-installed agents are scripts.** `#!/usr/bin/env node` fails with exit 127 when node is not on the take's PATH. `agent-take.sh` runs the interpreter by absolute path instead of adding it to PATH.
- **Codex's sandbox needs platform support.** On Linux, bubblewrap fails without unprivileged user namespaces ("No permissions to create a new namespace"). Preflight with `codex sandbox -- true` and stop; never fall back to full access. In 0.163.0, `codex sandbox -C DIR` also demands `--permission-profile`, and macOS has `/usr/bin/true` but no `/bin/true`.

## Edit and delivery

- **Untagged intermediates shift color** when mixed with tagged ones; use one color chain everywhere.
- **`-color_primaries` and `-color_trc` alone did not tag the stream** in testing; `setparams` does.
- **A camera move stepped at 24 Hz on a 60 fps timeline judders,** and effects stepping mid-shutter read as glitches.
- **GitHub's README video preview is frame 0,** and README videos play only when uploaded through GitHub's web editor.
- **Browser cache can show the old README assets** when file names did not change; check in a private window before assuming an upload failed.
