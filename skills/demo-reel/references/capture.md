# Capture

Choose the camera by what the shot must prove, then make each take repeatable and keep it.

## Choose the camera

| Surface                                   | Camera                                                                | Why                                                                                        |
| ----------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Web page or app with animation            | `scripts/capture-web.mjs`: stepped screenshots at device scale 2      | Every frame is a function of film time, so takes repeat and 4K costs nothing in smoothness |
| Web app whose point is live timing        | Real-time screenshots or screencast, measured                         | A latency claim must be shown at the real speed                                            |
| Plain-text CLI or TUI                     | A real terminal window, screenshot loop; or a terminal renderer       | Fonts, colors, and box drawing look like the user's terminal                               |
| TUI with terminal graphics (kitty images) | A real terminal window and a screenshot loop, never tmux text capture | Text capture cannot see images, so a chart drawn as an image vanishes from the take        |
| An agent using the product                | A real terminal, `scripts/agent-take.sh`, screenshot loop             | See [agent-on-camera.md](agent-on-camera.md)                                               |
| Hardware (LEDs, devices)                  | A physical camera, or a render driven by the engine's real output     | A render from the engine's real layout data stays true and repeatable                      |

## Browser takes at 4K

Use a 1920x1080 CSS viewport at device scale factor 2: screenshots come out 3840x2160 and the layout is the one people see at 1080p. Playwright's own `recordVideo` is the wrong camera for a reel: its size defaults to the viewport scaled down to fit 800x800 ([Playwright video docs](https://playwright.dev/docs/videos), checked 2026-10-21), and real-time recording at 8 megapixels drops frames on heavy pages.

```bash
node scripts/capture-web.mjs --url http://localhost:3000/dashboard \
  --seconds 8 --fps 60 --out takes/dashboard-01.mp4 --json
# 3840x2160 H.264 by default; --scale 1 for a 1080p draft, --frames DIR for PNGs.
```

The output is H.264 yuv420p with bt709 tags written into the stream. It is written to a hidden sibling file and renamed onto the target only when the capture completes, so an interrupted capture (SIGINT or SIGTERM, even twice) leaves no short file at the target path. On this skill's test Mac the capture ran at about 12 frames per second at 4K, so a 60 s shot at 60 fps takes about 5 minutes. Playwright resolves from the current project, or from `DEMO_REEL_PLAYWRIGHT`; `scripts/doctor.sh` prints the install commands.

## Deterministic web animation

A take repeats when every frame is a pure function of film time. Two clocks have to be controlled:

- **JavaScript time.** Playwright's `page.clock.install()` fakes `Date`, timers, `performance` and `requestAnimationFrame`, but an installed clock keeps flowing with real time until `page.clock.pauseAt()`; page load speed then leaks into motion. Its faked `performance.now()` and rAF timestamps also sat 0 to 2 ms away from the paused `Date.now()`, differently on each run. The capture script pauses the clock and takes over `requestAnimationFrame` and `performance.now()` itself: rAF callbacks run once per captured frame with the film time as their timestamp.
- **Compositor time.** CSS animations, transitions and Web Animations run on the compositor's real clock, which the fake does not touch, so frames differ run to run. After every clock step the script pauses each animation in `document.getAnimations()` the first time it appears, records the film time it was first seen, and sets `currentTime = filmNow - firstSeen`.

`Date.now()` is always `--time` plus film time, and timers fire on that same paused clock. The init script also seeds `Math.random`. It is registered after the clock is installed, so its rAF and `performance.now()` replace the fake's. The page loads one frame before film zero; that frame is captured and discarded, because the first raster after an animation is pinned differed by a sub-pixel between runs even when the animation state matched.

**Wait for the GPU before loading the page.** Twice, the first capture after a few idle minutes showed a canvas as a blank white box for its first 20 or so frames. Delaying Chromium's GPU process start (`--browser-arg=--gpu-launcher=` pointing at a script that sleeps, then execs) reproduced it every time: a canvas created while the GPU process is still starting stays unpresented until it arrives. The script now does a WebGL readback on `about:blank` first, which blocks until the GPU channel is up; with the delay in place, every capture then matched the normal frames.

Record of the check: on Playwright 1.59.1 and headless Chromium on macOS, a page with a CSS keyframe animation, a transition started by `setTimeout`, a rAF-driven canvas, and `Math.random` positions produced byte-identical frames across about 80 captures, under heavy CPU load, and with a deliberately slow GPU start; 4K MP4s from three runs were identical files. Compare the digest the script prints (`--json`) across two runs before a long render anyway: pages differ, and the check costs one extra run. An earlier version without the rAF takeover matched on CSS-only pages but drifted on canvas pages, which is why a CSS-only check is not enough.

Not covered: `<video>` and `<audio>` playback, cross-origin iframes, and timers inside Web Workers. For a clip inside a page, cut it in the edit instead of filming it playing.

Other browser traps:

- **Hide with `visibility: hidden`, not `display: none`,** when blanking an element whose size holds the layout open; `display: none` collapses a hero and moves everything.
- **Autoplaying carousels** call `scrollIntoView` and fight the camera. Stop or hide them.
- **Wait for the real thing.** A screenshot of a page that "loaded" before its data did is a pass measured on a half-loaded page.

## Real-time takes

When the shot proves timing (an ack, a live update, an agent working), record real time and measure what the recorder actually captured. A real-time recorder that cannot keep up encodes repeats to hold its nominal frame rate, which reads as judder; compare captured against encoded frames, or run `verify-mp4.sh --min-unique 0.9` on the file. [examples.md](examples.md) has a cut where the receipts showed this.

For heavy pages at 4K, hold still on each view and move the camera in the edit; a slow paint rate makes scrolling read as a slideshow.

## Terminals

- **Use a real terminal window** for anything with images or careful typography. Run a private instance with its own window class and a capture config (font, size, theme, no cursor blink) so the user's own terminals are untouched (most terminals can start with their default config files disabled).
- **Size the grid for the target pixels,** then crop exactly: measure the window once, then crop every frame to the same box, such as a 2830x1704 screenshot cropped to 2800x1700. For an agent session that must read at 1080p, grow the font until the grid is about 130x30.
- **Record with a screenshot loop** that saves each frame with a timestamp, and let the edit replay the real timing. A frame every 0.25 s (closer to 2.4 fps in practice) is plenty for a terminal that will be sped up.
  - macOS: `screencapture -x -R100,80,1600,900 frame.png` captures a screen rectangle (x,y,w,h) without a sound.
  - Linux on X11: `ffmpeg -f x11grab -video_size WxH -i :0.0+X,Y` records a region directly.
  - Linux on Wayland: `grim -g "X,Y WxH" frame.png`.
  - Check each tool's help on the machine; window-ID capture differs by platform and terminal.
- **Type like a person.** Send text through the terminal's automation (for example kitty's `kitten @ send-text`, WezTerm's `wezterm cli send-text`, or `tmux send-keys` when the camera films a tmux pane in a real window) in chunks of about three characters, 40 ms apart.
- **Send one throwaway key after launching a TUI.** Some TUIs drop the first keypress after launch.
- **Let history fill before the hero frame.** A live chart needs a minute or more of data before it reads as a chart.
- **Stop on idle, not on a timer.** Poll the agent's busy indicator (for Claude Code, the "esc to interrupt" hint, readable with `tmux capture-pane -p` even when images are not) and stop when it is gone on two consecutive checks.
- **Start from a clean shell.** A zsh autocorrect prompt ("Correct 'qclear' to 'clear'?") left over from quitting a TUI can stall a take before it begins.
- **Never `exec` the take.** A take launched with `exec` closes the window the camera is filming when it exits. `agent-take.sh` runs the agent as a child.
- **Detach long takes** (tmux, or the terminal's own background windows) so a dropped SSH session does not end the take.

## Keep and name takes

Write takes to a disk-backed directory in the project, never to a RAM-backed `/tmp`: it shares memory with everything else, fills fast (parallel build directories alone can do it), and is wiped on reboot. Number takes (`agent-01`, `agent-02`); keep failures, because a failed take is the evidence for its ledger row.
