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

- **Color tags.** Hypercolor's Codex-built software cut was full-range `yuvj420p` with a BT.470BG matrix and no primaries or transfer tags. Its rebuilt first master also lacked in-stream tags until an independent verifier failed it.
- **Repeated frames.** That software cut was nominally 60 fps, but its recorder captured 3,409 frames for 6,425 encoded ones, so nearly half the encoded frames had to be repeats, which reads as judder. `--min-unique` measures this on any file.
- **A black preview.** Unifly's first README video faded in from black, so GitHub's preview was a black box; frame 0 measured mean luma 18 of 255.

## Every frame is fit to show

Before every long render, and again on the delivered file, build contact sheets and read them:

```bash
scripts/contact-sheet.sh --at 0,2,10.4,13.45,15.4,21.6,27,33,41,51.7 reel-4k.mp4 review/cuts.png
scripts/contact-sheet.sh --every 5 --cols 4 reel-4k.mp4 review/every-5s.png
```

Put a tile at every cut, every caption, every zoom, and the first and last frames. The sheet's `.json` sidecar maps each tile to its timestamp. Then look, at full size where it matters, for:

- text clipped by the frame, a caption over the thing it describes, or a caption up too briefly to read;
- private data: real names in avatars and account footers, hostnames, emails, tokens, customer data (hypercolor cropped every UI pane above the footer that showed the account name);
- placeholders, spinners, empty states, or a half-loaded chart in a shot whose claim is the loaded state;
- stale labels from an earlier cut (one hypercolor still kept a "132 KEYS" label after the copy changed);
- upscaled or soft footage at 4K (hypercolor's first pass stretched logo petals 2.7x until its verifier caught it);
- a flash frame at a cut: extract the frames either side of each cut with `ffmpeg -ss T -frames:v 2`.

Hypercolor reviewed 1080p preview stills and contact sheets before every 4K master, then frame-checked the delivered files. A stills pass takes seconds; a bad 4K render takes many minutes and sometimes ships.

## Everything on screen is true

Every caption, number, and logo is a claim. List them from the edit and check each against its source:

| On screen             | Check                                             | Outcome on hypercolor                                           |
| --------------------- | ------------------------------------------------- | --------------------------------------------------------------- |
| "EVERY BRAND."        | The supported-device list                         | False: three brands unsupported. Became "12 BRANDS."            |
| "12 BRANDS."          | Will it stay true?                                | The list keeps growing; the count was removed, the names stayed |
| "132 KEYS"            | What the number counts                            | It counted LEDs, not keys                                       |
| "881 LEDS · 22 ZONES" | Computed from the real case layout at render time | Kept: the edit computes it, so it cannot drift                  |

Prefer claims the pipeline computes from the product's own data over typed numbers. Keep a performance claim only when the measurement behind it is in the ledger, and keep the shot's real-time timer honest (see [edit-render.md](edit-render.md)).

## Check what the pass measured

Every pass states what it measured and when. Then make sure the check could have failed:

- **A pass on a half-loaded page is not a pass.** A readiness wait must be on the data the shot claims, not on `load`.
- **The harness can be the bug.** Hypercolor's first rehearsal reported a 2.2 s first cut; the runner had matched the outgoing layer's health event across two clocks, and the real number was about 71 ms.
- **The bench can hide the effect.** A commit-cost A/B on tmpfs, where fsync is free, showed no difference; the real disk did.
- **A determinism check needs motion.** Two identical captures of a page that never moved prove nothing; the selftest also requires frame 0 and the last frame to differ.
- **Mutation check the fix.** Revert it, watch the new test or the shot fail, restore it.
- **A pass proves the build it ran on.** Unifly's kept agent take ran on a binary built from a fix branch before that fix merged. Record which build every take used, and reshoot if the shipped build differs.

## A second opinion

The implementer cannot certify its own work. For the pipeline, each fix lane, and the finished reel, hand an independent verifier the original request, the shot list, the changed files, the deliverables, and the receipts, and ask it to try to fail them. Use a different model family where available (see the `cross-model-review` skill). Hypercolor's rebuilt pipeline failed its first independent verification on three real defects (missing color tags, upscaled hero shots, and a camera shake stepping at 24 Hz on a 60 fps timeline); the session killed the master in progress rather than deliver it.

Then show a human. They are the final acceptance test.
