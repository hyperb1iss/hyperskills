# Edit and render

The default pipeline is Playwright for anything rendered from HTML (titles, captions, timers, camera moves over stills) and ffmpeg for everything else. Every recipe below ran on ffmpeg 9.0.2 without the `drawtext` filter; text comes from HTML pages rendered with `scripts/capture-web.mjs`.

Remotion is an option for a code-driven edit, but it is not free for every user: its license requires a paid Company License for a for-profit organization with more than 3 employees (individuals, non-profits, and companies of up to 3 employees use it free; [Remotion LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md), checked 2026-10-21). Nothing here depends on it.

## One color chain, everywhere

Use the same tail on every encode, from the first cut to the master:

```bash
C='scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv'
# 10-bit master: format=yuv420p10le in place of format=yuv420p
```

The `scale` converts RGB sources (screenshots, PNG cards) with the BT.709 matrix instead of ffmpeg's BT.601 default. The `setparams` writes the color tags into the stream; in testing, the `-color_primaries` and `-color_trc` output options alone left primaries and transfer unset. Mixing an untagged BT.601 intermediate with a BT.709 one in a crossfade shifts the colors of one side, so tag intermediates too. Hypercolor's first 4K master shipped to its verifier without in-stream tags; the verifier failed it.

Intermediates below use `M='-c:v libx264 -preset veryfast -crf 12 -pix_fmt yuv420p'`: near-lossless, fast, the same size and frame rate for every piece so they join without surprises. Always pass `-nostdin`: ffmpeg otherwise reads standard input and eats the rest of a script or a `while read` loop.

## Cuts

```bash
# Trim: seek before -i for speed; re-encoding makes the cut frame-accurate.
ffmpeg -nostdin -ss 12.5 -t 4 -i take.mp4 -an -vf "fps=60,$C" $M seg-03.mp4

# Normalize a 1080p take into a 4K edit.
ffmpeg -nostdin -i take.mp4 -vf "fps=60,scale=3840:2160:flags=lanczos,setsar=1,$C" $M seg-04.mp4
```

## Speed-ups with a real-time timer

Speed changes need `-ss` and `-t` before `-i`. After `-i`, `-t` limits the output, so the whole rest of the take is sped up: a 30 s piece at 20x came out 1.93 s long instead of 1.5 s.

Build a ramp as pieces (land at 1x, run fast, land at 1x), then join them:

```bash
ffmpeg -nostdin -ss 0    -t 1.5 -i take.mp4 -an -vf "fps=60,$C" $M p1.mp4
ffmpeg -nostdin -ss 1.5  -t 30  -i take.mp4 -an -vf "setpts=PTS/20,fps=60,$C" $M p2.mp4
ffmpeg -nostdin -ss 31.5 -t 1.5 -i take.mp4 -an -vf "fps=60,$C" $M p3.mp4
printf "file 'p1.mp4'\nfile 'p2.mp4'\nfile 'p3.mp4'\n" > pieces.txt
ffmpeg -nostdin -f concat -safe 0 -i pieces.txt -c copy sped.mp4   # 4.5 s
```

Then render the timer for the same map (film seconds to real seconds at each joint) and lay it over the clip:

```bash
node scripts/capture-web.mjs --transparent --fps 60 --seconds 4.5 --scale 2 \
  --url 'assets/timer.html#map=0:0,1.5:1.5,3:31.5,4.5:33' --frames timer/
ffmpeg -nostdin -i sped.mp4 -framerate 60 -i timer/%05d.png \
  -filter_complex "[0]scale=3840:2160:flags=lanczos[v];[v][1]overlay=0:0,$C" $M -t 4.5 timed.mp4
```

The pill shows elapsed real time and the speed (`20x`), and drops the multiplier at 1x. Checked against a test pattern with its own burned-in clock: at film 2.25 s the pill read 0:16 over a source frame stamped 16.65 s. For a Claude Code take, the session's own "Cooked for 1m 2s" line is a second, independent clock; keep it on screen.

## Transitions

```bash
# Crossfade: offset is the first clip's length minus the fade.
ffmpeg -nostdin -i a.mp4 -i b.mp4 \
  -filter_complex "[0][1]xfade=transition=fade:duration=0.5:offset=2.5,$C" $M ab.mp4
# A dip through black: transition=fadeblack.
```

`xfade` needs both inputs at the same size, frame rate, and pixel format, which the intermediates guarantee.

## Zooms

Keep them shallow (1.1 to 1.3x) and rare, and only to make a small element readable.

```bash
# Video: 1.0x to 1.15x over 4 s, centered. Even widths keep the crop centered
# on whole pixels; crop's own size cannot change per frame.
ffmpeg -nostdin -ss 8 -t 4 -i take.mp4 -an \
  -vf "scale=w='trunc(1920*(1+0.15*min(t/4\,1))/2)*2':h=-2:eval=frame:flags=lanczos,crop=1920:1080,setsar=1,$C" \
  $M zoom.mp4
```

For a still (a gallery screenshot), do the camera move in HTML: an `<img>` with a CSS transform animation, rendered by `capture-web.mjs`, moves by sub-pixels and is deterministic. Unifly's promo used the same idea (sub-pixel Ken Burns moves over 2800x1700 stills, rendered in code) for every TUI segment.

## Titles and captions

```bash
# A title card still, at 4K.
node scripts/capture-web.mjs --still card.png --at 1200 \
  --url 'assets/card.html#kicker=unifly&title=Your%20network.%20Your%20terminal.'
ffmpeg -nostdin -loop 1 -framerate 60 -t 3 -i card.png -vf "$C" $M card.mp4

# An animated card straight to video.
node scripts/capture-web.mjs --out card-in.mp4 --seconds 3 \
  --url 'assets/card.html#title=Every%20light.&sub=One%20engine.'

# A caption over a 4K clip, fading in at 0.5 s and out by 4.2 s.
node scripts/capture-web.mjs --still cap.png --at 900 --transparent \
  --url 'assets/card.html#mode=caption&kicker=Agents&title=The%20agent%20finds%20the%20offline%20AP'
ffmpeg -nostdin -i clip-4k.mp4 -loop 1 -framerate 60 -t 4.5 -i cap.png -filter_complex \
  "[1]format=rgba,fade=t=in:st=0.5:d=0.3:alpha=1,fade=t=out:st=3.9:d=0.3:alpha=1[c];[0][c]overlay=0:0:enable='between(t,0.5,4.2)',$C" \
  $M -t 4.5 captioned.mp4
```

Render overlays at the edit's size: `capture-web.mjs` defaults to 3840x2160, so a 1080p edit needs `--scale 1`. A 4K caption laid over a 1080p clip lands entirely off the frame, and ffmpeg reports no error.

Copy `assets/card.html` into the project and restyle it there: palette and fonts are CSS variables, and local font files load offline. Fonts carry the brand; hypercolor's first cut went back partly because "these fonts suck".

## Final encodes

```bash
# H.264, the compatibility deliverable (players, social, slides).
ffmpeg -nostdin -i cut.mp4 -vf "$C" -c:v libx264 -preset slow -crf 16 -profile:v high \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart reel-4k.mp4

# 10-bit HEVC master. hvc1 lets Apple players open it.
ffmpeg -nostdin -i cut.mp4 \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p10le,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v libx265 -preset slow -crf 14 -tag:v hvc1 -c:a aac -b:a 320k -ar 48000 -movflags +faststart reel-4k-hevc10.mp4

# 1080p social cut from the master.
ffmpeg -nostdin -i reel-4k.mp4 -vf "scale=1920:1080:flags=lanczos,$C" -c:v libx264 -preset slow \
  -crf 18 -c:a copy -movflags +faststart reel-1080p.mp4
```

Hardware encoders (`hevc_videotoolbox`, `hevc_nvenc`) are much faster for drafts and masters alike; hypercolor's 60 s 4K master went through `hevc_nvenc` Main 10. Run `verify-mp4.sh` on every deliverable whatever the encoder.

Rendering offline frame by frame scales well: pipe frames straight into ffmpeg's standard input with no intermediate files (hypercolor rendered 3,600 4K frames in 203 s that way), and keep each frame a pure function of film time so a re-render is the same film.

## Audio

Silent is fine; captions carry the words. A music bed:

```bash
ffmpeg -nostdin -i score.wav -i cut.mp4 \
  -filter_complex "[0]afade=t=in:d=0.5,afade=t=out:st=55:d=5,loudnorm=I=-16:TP=-1.5:LRA=11[a]" \
  -map 1:v -map "[a]" -c:v copy -c:a aac -b:a 320k -ar 48000 -shortest cut-audio.mp4
```

Music drives the edit when there is a score: hypercolor's was synthesized from code at 128 BPM, its cue sheet set the edit's bar grid, and a test checked that a second synthesis was bit-identical. Use only music you have the rights to.

## Open on a picture

GitHub, most players, and chat unfurls show frame 0 as the preview. Open on a composed title card, not a fade from black: unifly's first README cut faded in from black (frame 0 mean luma 18 of 255), and the fix composed the card from frame 0 (luma 32). `verify-mp4.sh` checks frame 0 by default. GitHub plays a README video only when the file was uploaded through its web editor (drag the MP4 into an issue or comment box and paste the resulting link).
