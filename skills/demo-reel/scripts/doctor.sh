#!/usr/bin/env bash
# Preflight for a demo reel: ffmpeg and its filters, Node, Playwright with a
# launchable Chromium, free disk, a RAM-backed temp dir, and the agent CLIs.
# Every failure prints the command that fixes it. Changes nothing.

set -u

HERE="$(cd "$(dirname "$0")" && pwd)"

usage() {
  cat <<'EOF'
Usage: doctor.sh [options]

  --out DIR          where takes and renders will be written (default: .)
  --min-free-gb N    free space required under --out (default 20)
  --no-browser       browser capture not needed: Node and Playwright become
                     optional (terminal-only reels)
  --json             print one JSON report on stdout
  -h, --help         show this help

Playwright is looked up from the current directory's node_modules, or from
DEMO_REEL_PLAYWRIGHT (a path to an installed playwright package).

Exit codes: 0 nothing required is missing (warnings allowed),
            1 a required check failed, 2 usage error.
EOF
}

out_dir=.
min_free=20
browser=1
json=0
while [ $# -gt 0 ]; do
  case $1 in
    --out) out_dir=${2:-}; shift 2 || { printf 'doctor: --out needs a value\n' >&2; exit 2; } ;;
    --min-free-gb) min_free=${2:-}; shift 2 || { printf 'doctor: --min-free-gb needs a value\n' >&2; exit 2; } ;;
    --no-browser) browser=0; shift ;;
    --json) json=1; shift ;;
    -h | --help) usage; exit 0 ;;
    *) printf 'doctor: unknown option %s\n' "$1" >&2; exit 2 ;;
  esac
done
case $min_free in '' | *[!0-9]*) printf 'doctor: --min-free-gb takes a whole number\n' >&2; exit 2 ;; esac

os=$(uname -s)
pm=''
if [ "$os" = Darwin ]; then pm=brew
elif command -v apt-get >/dev/null 2>&1; then pm=apt
elif command -v dnf >/dev/null 2>&1; then pm=dnf
elif command -v pacman >/dev/null 2>&1; then pm=pacman
fi
install_cmd() {
  # install_cmd PACKAGE -> the package manager line for this machine
  case $pm in
    brew) printf 'brew install %s' "$1" ;;
    apt) printf 'sudo apt-get update && sudo apt-get install -y %s' "$1" ;;
    dnf) printf 'sudo dnf install -y %s' "$1" ;;
    pacman) printf 'sudo pacman -S --needed %s' "$1" ;;
    *) printf 'install %s with your package manager' "$1" ;;
  esac
}

results=''
fails=0
warns=0
add() {
  # add NAME STATUS DETAIL FIX ; STATUS is ok, warn or fail
  results="$results$1	$2	$3	$4
"
  case $2 in fail) fails=$((fails + 1)) ;; warn) warns=$((warns + 1)) ;; esac
}

# ffmpeg and ffprobe
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  version=$(ffmpeg -hide_banner -version 2>/dev/null | head -1 | awk '{ print $3 }')
  add ffmpeg ok "ffmpeg $version" ''
  filters=$(ffmpeg -hide_banner -filters 2>/dev/null)
  encoders=$(ffmpeg -hide_banner -encoders 2>/dev/null)
  missing=''
  for f in scale setparams blackdetect freezedetect signalstats mpdecimate tile xfade overlay fade concat; do
    printf '%s\n' "$filters" | awk -v f="$f" '$2 == f { found = 1 } END { exit !found }' || missing="$missing $f"
  done
  if [ -z "$missing" ]; then
    add ffmpeg-filters ok 'every filter the recipes use' ''
  else
    add ffmpeg-filters fail "missing:$missing" "$(install_cmd ffmpeg) (a full build; minimal static builds drop filters)"
  fi
  if printf '%s\n' "$filters" | awk '$2 == "drawtext" { found = 1 } END { exit !found }'; then
    add drawtext ok 'available (optional)' ''
  else
    add drawtext ok 'absent; fine: titles, captions and timers come from HTML, not drawtext' ''
  fi
  if printf '%s\n' "$encoders" | awk '$2 == "libx264" { found = 1 } END { exit !found }'; then
    add libx264 ok 'H.264 encoder' ''
  else
    add libx264 fail 'no libx264 encoder' "$(install_cmd ffmpeg) (a build with --enable-libx264)"
  fi
  if printf '%s\n' "$encoders" | awk '$2 == "libx265" || $2 == "hevc_videotoolbox" || $2 == "hevc_nvenc" { found = 1 } END { exit !found }'; then
    add hevc ok 'an HEVC encoder for a 10-bit master' ''
  else
    add hevc warn 'no HEVC encoder; H.264 deliverables still work' "$(install_cmd ffmpeg) (with libx265)"
  fi
else
  add ffmpeg fail 'ffmpeg or ffprobe not on PATH' "$(install_cmd ffmpeg)"
fi

# Node and Playwright
need=fail
[ "$browser" -eq 0 ] && need=warn
if command -v node >/dev/null 2>&1; then
  node_version=$(node --version 2>/dev/null)
  major=$(printf '%s' "$node_version" | sed 's/^v\([0-9]*\).*/\1/')
  if [ "${major:-0}" -ge 18 ] 2>/dev/null; then
    add node ok "node $node_version" ''
  else
    add node "$need" "node $node_version is older than 18" "$(install_cmd node)"
  fi
  pw=$(node "$HERE/capture-web.mjs" --probe 2>/dev/null)
  case $pw in
    '{"playwright":null'*)
      add playwright "$need" 'playwright not found from this directory or DEMO_REEL_PLAYWRIGHT' \
        "npm install --save-dev playwright && npx playwright install chromium (in the project), or outside one: npm install --prefix ~/.cache/demo-reel playwright && npm exec --prefix ~/.cache/demo-reel -- playwright install chromium && export DEMO_REEL_PLAYWRIGHT=~/.cache/demo-reel/node_modules/playwright"
      ;;
    *'"launch":"ok"'*)
      where=$(printf '%s' "$pw" | sed -n 's/.*"version":"\([^"]*\)".*/\1/p')
      add playwright ok "playwright $where, Chromium launches" ''
      ;;
    *'"launch":'*)
      detail=$(printf '%s' "$pw" | sed -n 's/.*"launch":"\([^"]*\)".*/\1/p' | head -c 200)
      deps=''
      [ "$os" = Linux ] && deps=' --with-deps'
      fix="npx playwright install$deps chromium in the project, or npm exec --prefix DIR -- playwright install$deps chromium for a DEMO_REEL_PLAYWRIGHT install"
      add chromium "$need" "Chromium did not launch: $detail" "$fix"
      ;;
    *)
      add playwright "$need" 'could not run the Playwright probe' 'node --version; then rerun doctor.sh'
      ;;
  esac
else
  add node "$need" 'node not on PATH' "$(install_cmd node)"
fi
if command -v bun >/dev/null 2>&1; then
  add bun ok "bun $(bun --version 2>/dev/null) (optional)" ''
fi

# Disk and temp space
if [ -d "$out_dir" ]; then
  free_kb=$(df -Pk "$out_dir" 2>/dev/null | awk 'NR == 2 { print $4 }')
  free_gb=$(( ${free_kb:-0} / 1048576 ))
  if [ "$free_gb" -ge "$min_free" ]; then
    add disk ok "${free_gb} GiB free under $out_dir" ''
  else
    add disk fail "${free_gb} GiB free under $out_dir, need ${min_free}" \
      'free space (build caches are the usual culprit) or pass --out to a roomier disk'
  fi
else
  add disk fail "$out_dir does not exist" "mkdir -p $out_dir"
fi
tmp=${TMPDIR:-/tmp}
fstype=''
if [ "$os" = Linux ]; then
  fstype=$(stat -f -c %T "$tmp" 2>/dev/null)
fi
case $fstype in
  tmpfs | ramfs)
    add tmp warn "$tmp is RAM-backed ($fstype): it shares memory, fills fast, and is wiped on reboot" \
      'keep takes and deliverables on disk; use temp only for scratch you can lose'
    ;;
  *) add tmp ok "$tmp is disk-backed" '' ;;
esac

# Optional tools for terminal and agent takes
for tool in tmux claude codex; do
  if command -v "$tool" >/dev/null 2>&1; then
    if [ "$tool" = tmux ]; then v=$(tmux -V 2>/dev/null); else v=$("$tool" --version 2>/dev/null | head -1); fi
    add "$tool" ok "${v:-present} (optional)" ''
  fi
done

if [ "$json" -eq 1 ]; then
  if [ "$fails" -eq 0 ]; then ok=true; else ok=false; fi
  printf '{"ok": %s, "failures": %s, "warnings": %s, "checks": [' "$ok" "$fails" "$warns"
  printf '%s' "$results" | awk -F'\t' '
    function esc(s) { gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s); return s }
    NF >= 2 { printf "%s{\"name\": \"%s\", \"status\": \"%s\", \"detail\": \"%s\", \"fix\": \"%s\"}", sep, esc($1), $2, esc($3), esc($4); sep = ", " }'
  printf ']}\n'
else
  printf '%s' "$results" | awk -F'\t' '
    NF >= 2 {
      mark = ($2 == "ok") ? "ok  " : (($2 == "warn") ? "warn" : "FAIL")
      printf "%s %-15s %s\n", mark, $1, $3
      if ($4 != "") printf "     fix: %s\n", $4
    }'
  if [ "$fails" -eq 0 ]; then
    printf 'ready (%s warning%s)\n' "$warns" "$([ "$warns" -eq 1 ] || printf s)"
  else
    printf '%s required check%s failed\n' "$fails" "$([ "$fails" -eq 1 ] || printf s)"
  fi
fi
[ "$fails" -eq 0 ]
