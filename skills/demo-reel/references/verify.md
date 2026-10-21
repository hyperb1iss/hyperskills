# Verify

A finished reel is three claims at once: the file meets its delivery contract, every frame is fit to show, and everything on screen is true. Check each one with evidence, and check that each check could have failed.

## The file meets its contract

Run `scripts/verify-mp4.sh` on every deliverable with the expectations written down in the shot list:

```bash
scripts/verify-mp4.sh --expect-size 3840x2160 --expect-fps 60 --expect-codec hevc \
  --expect-pix-fmt yuv420p10le --expect-duration 60 --expect-audio yes reel-4k-hevc10.mp4
scripts/verify-mp4.sh --json --expect-size 1920x1080 --expect-fps 60 --min-unique 0.9 reel-1080p.mp4
```

It always checks bt709 primaries, transfer and matrix tags (`--expect-color any` to skip), TV range (a full-range `yuvj420p` file fails unless `--expect-range pc`), no black stretch of a second or more, and a first frame that is not black. `--max-freeze` and `--min-unique` are opt-in, because a deliberate hold is a frozen stretch too. Exit 0 means every check passed; the JSON report lists each check with its expected and actual value, plus every black and frozen interval.

What it caught on real reels:

- **Color tags.** Screen recorders often produce full-range `yuvj420p` with a BT.470BG matrix and no primaries or transfer tags, and a hand-built encode can lack in-stream tags entirely.
- **Repeated frames.** A real-time recording at a nominal 60 fps can hold far fewer distinct frames, which reads as judder. `--min-unique` measures this on any file.
- **A black preview.** A video that fades in from black previews as a black box on GitHub and in most players.

## Every frame is fit to show

Before every long render, and again on the delivered file, build contact sheets and read them:

```bash
scripts/contact-sheet.sh --at 0,2,10.4,13.45,15.4,21.6,27,33,41,51.7 reel-4k.mp4 review/cuts.png
scripts/contact-sheet.sh --every 5 --cols 4 reel-4k.mp4 review/every-5s.png
```

Put a tile at every cut, every caption, every zoom, and the first and last frames. The sheet's `.json` sidecar maps each tile to its timestamp. Then look, at full size where it matters, for:

- text clipped by the frame, a caption over the thing it describes, or a caption up too briefly to read;
- private data: real names in avatars and account footers, hostnames, emails, tokens, customer data (crop app panes above any footer that shows the account name);
- placeholders, spinners, empty states, or a half-loaded chart in a shot whose claim is the loaded state;
- stale labels from an earlier cut, still on screen after the copy changed;
- upscaled or soft footage at 4K (a source drawn at 2x or 3x its size reads soft even when the file is 4K);
- a flash frame at a cut: extract the frames either side of each cut with `ffmpeg -ss T -frames:v 2`.

Review 1080p preview stills and contact sheets before every 4K master, then frame-check the delivered files. A stills pass takes seconds; a bad 4K render takes many minutes and sometimes ships.

## Everything on screen is true

Every caption, number, and logo is a claim. List them from the edit and check each against its source:

| On screen             | Check                                             | What the check can find                                         |
| --------------------- | ------------------------------------------------- | --------------------------------------------------------------- |
| "EVERY BRAND."        | The supported-device list                         | False: three brands unsupported. Became "12 BRANDS."            |
| "12 BRANDS."          | Will it stay true?                                | The list keeps growing; the count was removed, the names stayed |
| "132 KEYS"            | What the number counts                            | It counted LEDs, not keys                                       |
| "881 LEDS · 22 ZONES" | Computed from the real case layout at render time | Kept: the edit computes it, so it cannot drift                  |

Prefer claims the pipeline computes from the product's own data over typed numbers. Keep a performance claim only when the measurement behind it is in the ledger, and keep the shot's real-time timer honest (see [edit-render.md](edit-render.md)).

## Check what the pass measured

Every pass states what it measured and when. Then make sure the check could have failed:

- **A pass on a half-loaded page is not a pass.** A readiness wait must be on the data the shot claims, not on `load`.
- **The harness can be the bug.** A runner that matches events across two clocks can report a 2 s stall that was really 70 ms. Check the measurement before chasing the product.
- **The bench can hide the effect.** A commit-cost A/B on tmpfs, where fsync is free, showed no difference; the real disk did.
- **A determinism check needs motion.** Two identical captures of a page that never moved prove nothing; the selftest also requires frame 0 and the last frame to differ.
- **Mutation check the fix.** Revert it, watch the new test or the shot fail, restore it.
- **A pass proves the build it ran on.** A take shot on a binary from an unmerged fix branch proves that branch. Record which build every take used, and reshoot if the shipped build differs.

## A second opinion

The implementer cannot certify its own work. For the pipeline, each fix lane, and the finished reel, hand an independent verifier the original request, the shot list, the changed files, the deliverables, and the receipts, and ask it to try to fail them. Use a different model family where available (see the `cross-model-review` skill). Expect real defects (missing color tags, upscaled shots, a camera shake stepping at 24 Hz on a 60 fps timeline), and stop a render in progress rather than deliver one the verifier failed. [examples.md](examples.md) has a pipeline that failed its first verification on exactly those three.

Then show a human. They are the final acceptance test.
