#!/usr/bin/env bash
# Offline end-to-end proof for the demo-reel scripts. Synthesizes clips with
# ffmpeg's testsrc2, checks that verify-mp4 passes a good clip and fails bad
# ones, builds contact sheets, exercises the agent-take sandbox without an
# agent, and, when Playwright resolves, proves two web captures are identical.
#
#   bash skills/demo-reel/scripts/selftest.sh
#   /bin/bash skills/demo-reel/scripts/selftest.sh   # also proves bash 3.2
#
# Every script runs under the interpreter running this file. Needs ffmpeg.
# Browser cases need node and Playwright (from the current directory or
# DEMO_REEL_PLAYWRIGHT); without them they are reported as skipped, and
# DEMO_REEL_REQUIRE_BROWSER=1 turns that skip into a failure.
# Exit 0 when every case that ran passed.

set -u
case ${1:-} in
  -h | --help)
    sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
esac
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(cd "$HERE/.." && pwd)"
SH=${BASH:-bash}
pass=0
fail=0
skip=0
TMP="$(mktemp -d "${TMPDIR:-/tmp}/demo-reel-selftest.XXXXXX")"
TMP="$(cd "$TMP" && pwd -P)"
# Keep the work dir when something failed, so the frames can be inspected.
finish() {
  if [ "$fail" -eq 0 ]; then rm -rf "$TMP"; else printf 'work dir kept: %s\n' "$TMP"; fi
}
trap finish EXIT

ok() { pass=$((pass + 1)); }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; }

# expect NAME WANT_EXIT COMMAND... ; output goes to $TMP/last.out
expect() {
  local name=$1 want=$2
  shift 2
  "$@" >"$TMP/last.out" 2>&1
  local got=$?
  if [ "$got" = "$want" ]; then ok; else bad "$name (want exit $want, got $got)"; sed 's/^/        /' "$TMP/last.out" | head -8; fi
}
contains() {
  if grep -q -- "$2" "$TMP/last.out"; then ok; else bad "$1 (output lacks $2)"; fi
}
lacks() {
  if grep -q -- "$2" "$TMP/last.out"; then bad "$1 (output contains $2)"; else ok; fi
}
valid_json() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import json, sys; json.load(open(sys.argv[1]))' "$TMP/last.out" 2>/dev/null && ok || bad "$1 (not JSON)"
  elif command -v node >/dev/null 2>&1; then
    node -e 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))' "$TMP/last.out" 2>/dev/null && ok || bad "$1 (not JSON)"
  else
    skip=$((skip + 1))
  fi
}
size_of() {
  ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$1" 2>/dev/null
}

printf 'demo-reel selftest (%s)\n' "$("$SH" -c 'echo "bash $BASH_VERSION"')"

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  printf '  FAIL  ffmpeg and ffprobe are required; run scripts/doctor.sh for the install command\n'
  exit 1
fi

# ---- doctor -----------------------------------------------------------------
expect "doctor runs without a browser" 0 "$SH" "$HERE/doctor.sh" --no-browser --min-free-gb 0 --json --out "$TMP"
valid_json "doctor prints JSON"
expect "doctor rejects a bad option" 2 "$SH" "$HERE/doctor.sh" --bogus

# ---- clips ------------------------------------------------------------------
tags='setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv'
mk() { ffmpeg -nostdin -v error -y "$@"; }
mk -f lavfi -i "testsrc2=s=1280x720:r=30:d=3" \
  -vf "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,$tags" \
  -c:v libx264 -preset veryfast -crf 20 -movflags +faststart "$TMP/good.mp4"
mk -f lavfi -i "testsrc2=s=1280x720:r=30:d=3" -vf format=yuv420p \
  -c:v libx264 -preset veryfast -crf 20 "$TMP/untagged.mp4"
mk -f lavfi -i "color=c=black:s=1280x720:r=30:d=1.5" -f lavfi -i "testsrc2=s=1280x720:r=30:d=1.5" \
  -filter_complex "[0][1]concat=n=2:v=1,format=yuv420p,$tags" \
  -c:v libx264 -preset veryfast -crf 20 "$TMP/blackstart.mp4"
mk -f lavfi -i "testsrc2=s=1280x720:r=30:d=1" \
  -vf "tpad=stop_mode=clone:stop_duration=2,format=yuv420p,$tags" \
  -c:v libx264 -preset veryfast -crf 20 "$TMP/frozen.mp4"
for clip in good untagged blackstart frozen; do
  [ -s "$TMP/$clip.mp4" ] && ok || bad "synthesize $clip.mp4"
done

# ---- verify-mp4 -------------------------------------------------------------
V="$HERE/verify-mp4.sh"
expect "good clip passes every expectation" 0 "$SH" "$V" --expect-size 1280x720 --expect-fps 30 \
  --expect-codec h264 --expect-pix-fmt yuv420p --expect-duration 3 --expect-audio no \
  --max-freeze 1 --min-unique 0.95 "$TMP/good.mp4"
expect "good clip JSON report" 0 "$SH" "$V" --json --expect-fps 30 "$TMP/good.mp4"
valid_json "verify prints JSON"
contains "JSON says ok" '"ok": true'
expect "missing color tags fail" 1 "$SH" "$V" "$TMP/untagged.mp4"
contains "the failing check is named" 'FAIL color_tags'
expect "black first frame fails" 1 "$SH" "$V" "$TMP/blackstart.mp4"
contains "first frame is the reason" 'FAIL first_frame'
contains "black stretch is the other reason" 'FAIL black'
expect "black start passes when allowed" 0 "$SH" "$V" --allow-black-start --max-black none "$TMP/blackstart.mp4"
expect "wrong frame rate fails" 1 "$SH" "$V" --expect-fps 60 "$TMP/good.mp4"
expect "wrong size fails" 1 "$SH" "$V" --expect-size 3840x2160 "$TMP/good.mp4"
expect "duration out of tolerance fails" 1 "$SH" "$V" --expect-duration 4 "$TMP/good.mp4"
expect "a frozen tail fails --max-freeze" 1 "$SH" "$V" --max-freeze 1.5 "$TMP/frozen.mp4"
expect "repeated frames fail --min-unique" 1 "$SH" "$V" --min-unique 0.8 "$TMP/frozen.mp4"
contains "unique ratio is reported" 'unique_frames'
expect "usage error" 2 "$SH" "$V" --expect-size huge "$TMP/good.mp4"
expect "unreadable input" 4 "$SH" "$V" "$TMP/nope.mp4"

# ---- contact-sheet ----------------------------------------------------------
C="$HERE/contact-sheet.sh"
expect "sheet every second" 0 "$SH" "$C" --every 1 --cols 3 --tile-width 320 "$TMP/good.mp4" "$TMP/sheet.png"
[ "$(size_of "$TMP/sheet.png")" = "992x196" ] && ok || bad "sheet is 3 tiles of 320 plus margins (got $(size_of "$TMP/sheet.png"))"
[ -s "$TMP/sheet.json" ] && ok || bad "sheet writes its tile map"
expect "times past the end are clamped" 0 "$SH" "$C" --at 0,1.5,0:09 --json "$TMP/good.mp4" "$TMP/clamp.png"
valid_json "sheet prints JSON"
contains "the clamp is reported" '"clamped": true'
expect "default sheet has nine tiles" 0 "$SH" "$C" "$TMP/good.mp4" "$TMP/nine.png"
contains "nine tiles in a 3x3 grid" '3x3 tiles'
expect "bad time is a usage error" 2 "$SH" "$C" --at soon "$TMP/good.mp4" "$TMP/x.png"

# ---- agent-take -------------------------------------------------------------
A="$HERE/agent-take.sh"
mkdir -p "$TMP/home/.config/democtl" "$TMP/prod" "$TMP/skill/democtl"
printf 'token=real\n' >"$TMP/home/.config/democtl/config"
printf -- '---\nname: democtl\ndescription: Inspect the demo fleet with democtl.\n---\nRun democtl.\n' \
  >"$TMP/skill/democtl/SKILL.md"
cat >"$TMP/prod/democtl" <<'EOF'
#!/bin/sh
# Stand-in product: demo data under DEMO_FLEET=1, otherwise real config.
if [ "${DEMO_FLEET:-}" = 1 ]; then echo "demo fleet: Neon Harbor"; exit 0; fi
if [ -f "${XDG_CONFIG_HOME:-$HOME/.config}/democtl/config" ]; then echo "real config found"; exit 0; fi
if [ -f "$HOME/.democtlrc" ]; then echo "real config found in HOME"; exit 0; fi
echo "no config"; exit 3
EOF
chmod +x "$TMP/prod/democtl"
take() {
  "$SH" "$A" --home "$TMP/home" --agent-bin /usr/bin/true --allow "$TMP/prod/democtl" \
    --env DEMO_FLEET=1 "$@"
}
export DEMO_REEL_CANARY_OUTER=should-not-leak
expect "dry run prints the command" 0 take --tool 'Bash(democtl:*)' --tool 'Skill(democtl)' \
  --skill "$TMP/skill/democtl" --dry-run
contains "starts from an empty environment" 'env -i'
contains "dontAsk permission mode" 'dontAsk'
contains "setting sources" 'project\\,local'
contains "strict MCP config" 'strict-mcp-config'
contains "the demo variable reaches the take" 'DEMO_FLEET=1'
lacks "a parent variable does not" 'DEMO_REEL_CANARY_OUTER'
lacks "never auto mode" 'permission-mode auto'
lacks "never bypass" 'dangerously'
ANTHROPIC_API_KEY=sk-selftest-secret expect "dry run JSON" 0 take --tool 'Bash(democtl:*)' --dry-run --json
valid_json "dry run JSON parses"
lacks "auth secrets are masked" 'sk-selftest-secret'
expect "codex dry run" 0 take --agent codex --dry-run
contains "codex read-only sandbox" 'read-only'
contains "codex never asks" 'never'
expect "prove holds" 0 take --tool 'Bash(democtl:*)' --skill "$TMP/skill/democtl" \
  --dir "$TMP/studio-a" --prove --probe democtl --probe-expect '^no config'
contains "the probe saw no config" 'no config'
proved=$(sed -n 's/^studio \([^,]*\), sandbox.*/\1/p' "$TMP/last.out")
[ -f "$proved/.claude/skills/democtl/SKILL.md" ] && ok || bad "the skill is copied into the studio"
[ ! -e "$TMP/studio-a" ] && ok || bad "a proof leaves --dir free for the take"
printf 'secret\n' >"$TMP/home/.democtlrc"
expect "prove catches a config read straight from HOME" 1 take --tool 'Bash(democtl:*)' \
  --dir "$TMP/studio-b" --prove --json --probe democtl --probe-expect '^no config'
valid_json "prove prints JSON"
contains "the leak is shown" 'real config found in HOME'
rm -f "$TMP/home/.democtlrc"
expect "Claude takes need a tool rule" 2 take
expect "Codex takes refuse tool rules" 2 take --agent codex --tool 'Bash(x)'
expect "the launcher owns PATH" 2 take --tool 'Bash(x)' --env PATH=/usr/bin
mkdir -p "$TMP/used" && : >"$TMP/used/notes.txt"
expect "a used studio dir is refused" 4 take --tool 'Bash(x)' --dir "$TMP/used"
expect "a missing agent binary" 3 "$SH" "$A" --agent-bin "$TMP/no-such-agent" --tool 'Bash(x)' --dry-run

# ---- capture-web (browser) --------------------------------------------------
W="$HERE/capture-web.mjs"
browser=0
if command -v node >/dev/null 2>&1; then
  case $(node "$W" --probe 2>/dev/null) in *'"launch":"ok"'*) browser=1 ;; esac
fi
if [ "$browser" -eq 1 ]; then
  cat >"$TMP/anim.html" <<'EOF'
<!doctype html><html><head><meta charset="utf-8"><style>
body { margin: 0; background: #0a0812; color: #fff; font: 700 48px sans-serif }
.box { position: absolute; top: 120px; left: 80px; width: 160px; height: 160px; background: #e135ff;
       animation: slide 2s ease-in-out infinite alternate }
@keyframes slide { to { transform: translateX(1200px) rotate(180deg) } }
.late { position: absolute; top: 420px; left: 80px; width: 120px; height: 120px; background: #80ffea;
        opacity: 0; transition: opacity 600ms linear, transform 600ms ease-out }
.late.on { opacity: 1; transform: translateX(600px) }
canvas { position: absolute; top: 620px; left: 80px }
</style></head><body><div id="t"></div><div class="box"></div><div class="late"></div>
<canvas id="c" width="1600" height="360"></canvas><script>
const dots = Array.from({ length: 40 }, () => [Math.random() * 1600, Math.random() * 360, Math.random() * 360])
const t0 = performance.now(), c = document.getElementById('c').getContext('2d')
setTimeout(() => document.querySelector('.late').classList.add('on'), 500)
function tick(ts) {
  const t = performance.now() - t0
  document.getElementById('t').textContent = (t / 1000).toFixed(2) + 's'
  c.clearRect(0, 0, 1600, 360)
  for (const [x, y, h] of dots) { c.fillStyle = `hsl(${(h + ts / 10) % 360} 90% 60%)`; c.fillRect((x + t / 5) % 1600, y, 18, 18) }
  requestAnimationFrame(tick)
}
requestAnimationFrame(tick)
</script></body></html>
EOF
  digest() { sed -n 's/.*"digest":"\([0-9a-f]*\)".*/\1/p' "$TMP/last.out"; }
  expect "first web capture" 0 node "$W" --url "$TMP/anim.html" --frames "$TMP/run-a" \
    --seconds 1 --fps 30 --scale 1 --json
  first=$(digest)
  expect "second web capture" 0 node "$W" --url "$TMP/anim.html" --frames "$TMP/run-b" \
    --seconds 1 --fps 30 --scale 1 --json
  second=$(digest)
  [ -n "$first" ] && [ "$first" = "$second" ] && ok || bad "two captures give identical frames ($first vs $second)"
  # A determinism check that passes on a page that never moved proves nothing.
  if cmp -s "$TMP/run-a/00000.png" "$TMP/run-a/00029.png"; then bad "the captured page moved"; else ok; fi
  # A slow GPU process start once left a canvas blank for its first frames.
  # Delay the GPU launch on purpose: the frames must still match.
  printf '#!/bin/sh\nsleep 2\nexec "$@"\n' >"$TMP/slow-gpu.sh"
  chmod +x "$TMP/slow-gpu.sh"
  if node "$W" --url "$TMP/anim.html" --frames "$TMP/run-slow" --seconds 1 --fps 30 --scale 1 --json \
    --browser-arg="--gpu-launcher=$TMP/slow-gpu.sh" >"$TMP/last.out" 2>&1; then
    slow=$(digest)
    [ "$slow" = "$first" ] && ok || bad "a slow GPU start changes the frames ($slow vs $first)"
  else
    skip=$((skip + 1))
    printf '  skip  slow GPU case: Chromium would not launch with a GPU launcher here\n'
  fi
  expect "capture to MP4" 0 node "$W" --url "$TMP/anim.html" --out "$TMP/web.mp4" --seconds 1 --fps 30 --scale 1
  expect "captured MP4 meets its contract" 0 "$SH" "$V" --expect-size 1920x1080 --expect-fps 30 \
    --expect-duration 1 --min-unique 0.9 "$TMP/web.mp4"
  expect "title card still at 4K" 0 node "$W" --still "$TMP/card.png" --at 900 \
    --url "$SKILL/assets/card.html#kicker=selftest&title=Every%20shot%20is%20a%20test."
  [ "$(size_of "$TMP/card.png")" = "3840x2160" ] && ok || bad "card renders at 3840x2160"
  expect "timer overlay frames" 0 node "$W" --transparent --fps 10 --seconds 1 --scale 0.5 \
    --url "$SKILL/assets/timer.html#map=0:0,1:20" --frames "$TMP/timer"
  [ -s "$TMP/timer/00009.png" ] && ok || bad "timer writes one PNG per frame"
  expect "transparent MP4 is refused" 2 node "$W" --url "$TMP/anim.html" --out "$TMP/x.mp4" --transparent
else
  if [ "${DEMO_REEL_REQUIRE_BROWSER:-0}" = 1 ]; then
    bad "browser cases required but Playwright or Chromium is unavailable"
  else
    skip=$((skip + 1))
    printf '  skip  browser cases: Playwright with a launchable Chromium not found (see doctor.sh)\n'
  fi
fi

printf '\n%d passed, %d failed, %d skipped\n' "$pass" "$fail" "$skip"
[ "$fail" -eq 0 ]
