#!/usr/bin/env bash
# Tile stills from a video into one PNG for review. Needs ffmpeg and
# ffprobe only (no drawtext): the tile-to-timestamp map is printed and
# written beside the PNG as OUT.json instead of being burned in.

set -u

usage() {
  cat <<'EOF'
Usage: contact-sheet.sh [options] IN.mp4 OUT.png

Frames (default: 9 frames, one from the middle of each ninth):
  --at LIST         comma-separated times: 12, 12.5, 1:05, 0:01:05.250
  --every S         one frame every S seconds, starting at 0
Layout:
  --cols N          tiles per row (default: 3, or 4 above 12 tiles)
  --tile-width PX   width of each tile (default 640; height keeps aspect)
Output:
  --json            print the tile map as JSON on stdout
  -h, --help        show this help

Times past the end are clamped to the last frame and reported as clamped.
OUT.json always records which tile shows which time, row by row.

Exit codes: 0 sheet written, 2 usage error, 3 ffmpeg or ffprobe missing,
            4 the input could not be read or a frame could not be extracted.
EOF
}

at=''
every=''
cols=''
tile_width=640
json=0
in=''
out=''

need_value() {
  if [ $# -lt 2 ] || [ -z "$2" ]; then
    printf 'contact-sheet: %s needs a value\n' "$1" >&2
    exit 2
  fi
}

while [ $# -gt 0 ]; do
  case $1 in
    --at) need_value "$@"; at=$2; shift 2 ;;
    --every) need_value "$@"; every=$2; shift 2 ;;
    --cols) need_value "$@"; cols=$2; shift 2 ;;
    --tile-width) need_value "$@"; tile_width=$2; shift 2 ;;
    --json) json=1; shift ;;
    -h | --help) usage; exit 0 ;;
    -*) printf 'contact-sheet: unknown option %s\n' "$1" >&2; exit 2 ;;
    *)
      if [ -z "$in" ]; then in=$1
      elif [ -z "$out" ]; then out=$1
      else printf 'contact-sheet: unexpected argument %s\n' "$1" >&2; exit 2
      fi
      shift
      ;;
  esac
done
if [ -z "$in" ] || [ -z "$out" ]; then usage >&2; exit 2; fi
if [ -n "$at" ] && [ -n "$every" ]; then
  printf 'contact-sheet: use --at or --every, not both\n' >&2
  exit 2
fi
case $tile_width in '' | *[!0-9]*) printf 'contact-sheet: --tile-width takes pixels\n' >&2; exit 2 ;; esac
case $cols in *[!0-9]*) printf 'contact-sheet: --cols takes a number\n' >&2; exit 2 ;; esac
case $every in *[!0-9.]*) printf 'contact-sheet: --every takes seconds\n' >&2; exit 2 ;; esac

for tool in ffprobe ffmpeg; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'contact-sheet: %s not found; run doctor.sh for the install command\n' "$tool" >&2
    exit 3
  fi
done
if [ ! -r "$in" ] || [ -d "$in" ]; then
  printf 'contact-sheet: cannot read %s\n' "$in" >&2
  exit 4
fi

# Prefer the video stream's duration: the container can run longer when an
# audio track outlasts the picture.
duration=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=nw=1:nk=1 "$in" 2>/dev/null)
case $duration in '' | N/A) duration=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$in" 2>/dev/null) ;; esac
rate=$(ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of default=nw=1:nk=1 "$in" 2>/dev/null)
case $duration in '' | N/A) printf 'contact-sheet: no duration for %s\n' "$in" >&2; exit 4 ;; esac
# Seek a frame and a half before the end so rounding cannot step past the
# last frame; a seek past the end writes nothing and reports no error.
last=$(awk -v d="$duration" -v r="$rate" 'BEGIN { n = split(r, p, "/"); f = (n == 2 && p[2] > 0 && p[1] > 0) ? p[2] / p[1] : 1 / 30; t = d - 1.5 * f; if (t < 0) t = 0; printf "%.3f", t }')

to_seconds() {
  awk -v t="$1" 'BEGIN {
    n = split(t, p, ":"); s = 0
    for (i = 1; i <= n; i++) { if (p[i] !~ /^[0-9]+(\.[0-9]+)?$/) { print "bad"; exit } s = s * 60 + p[i] }
    printf "%.3f", s }'
}

times=''
if [ -n "$at" ]; then
  old_ifs=$IFS
  IFS=,
  for raw in $at; do
    raw=$(printf '%s' "$raw" | tr -d ' ')
    [ -z "$raw" ] && continue
    s=$(to_seconds "$raw")
    if [ "$s" = bad ]; then IFS=$old_ifs; printf 'contact-sheet: bad time %s\n' "$raw" >&2; exit 2; fi
    times="$times $s"
  done
  IFS=$old_ifs
elif [ -n "$every" ]; then
  times=$(awk -v d="$duration" -v e="$every" 'BEGIN { if (e <= 0) exit; for (t = 0; t < d; t += e) printf " %.3f", t }')
else
  times=$(awk -v d="$duration" 'BEGIN { for (i = 0; i < 9; i++) printf " %.3f", (i + 0.5) * d / 9 }')
fi
set -- $times
count=$#
if [ "$count" -eq 0 ]; then
  printf 'contact-sheet: no frames selected\n' >&2
  exit 2
fi
if [ -z "$cols" ] || [ "$cols" -lt 1 ]; then
  if [ "$count" -gt 12 ]; then cols=4; else cols=3; fi
fi
[ "$cols" -gt "$count" ] && cols=$count
rows=$(( (count + cols - 1) / cols ))

work=$(mktemp -d "${TMPDIR:-/tmp}/contact-sheet.XXXXXX")
trap 'rm -rf "$work"' EXIT

map=''
index=0
for t in "$@"; do
  index=$((index + 1))
  clamped=false
  if awk -v t="$t" -v l="$last" 'BEGIN { exit !(t > l) }'; then t=$last; clamped=true; fi
  tile=$(printf '%s/%03d.png' "$work" "$index")
  ffmpeg -nostdin -v error -y -ss "$t" -i "$in" -frames:v 1 \
    -vf "scale=${tile_width}:-2:flags=lanczos" "$tile" 2>"$work/err.txt"
  if [ ! -s "$tile" ]; then
    # Seek imprecision near the end: decode the final second and keep the
    # last frame it yields.
    back=$(awk -v l="$last" 'BEGIN { t = l - 1; if (t < 0) t = 0; printf "%.3f", t }')
    ffmpeg -nostdin -v error -y -ss "$back" -i "$in" -vf "scale=${tile_width}:-2:flags=lanczos" \
      -update 1 "$tile" 2>>"$work/err.txt" && clamped=true
  fi
  if [ ! -s "$tile" ]; then
    printf 'contact-sheet: no frame at %ss: %s\n' "$t" "$(head -c 300 "$work/err.txt")" >&2
    exit 4
  fi
  row=$(( (index - 1) / cols + 1 ))
  col=$(( (index - 1) % cols + 1 ))
  map="$map$index $row $col $t $clamped
"
done

mkdir -p "$(dirname "$out")"
if ! ffmpeg -nostdin -v error -y -framerate 1 -start_number 1 -i "$work/%03d.png" \
  -vf "tile=${cols}x${rows}:padding=8:margin=8:color=0x101014" -frames:v 1 -update 1 "$out"; then
  printf 'contact-sheet: tiling failed\n' >&2
  exit 4
fi

json_str() {
  local s=$1
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  printf '"%s"' "$s"
}
report=$(printf '{"input": %s, "output": %s, "cols": %s, "rows": %s, "tile_width": %s, "tiles": [' \
  "$(json_str "$in")" "$(json_str "$out")" "$cols" "$rows" "$tile_width")
report="$report$(printf '%s' "$map" | awk 'NF == 5 { printf "%s{\"index\": %s, \"row\": %s, \"col\": %s, \"t\": %s, \"clamped\": %s}", sep, $1, $2, $3, $4, $5; sep = ", " }')]}"
printf '%s\n' "$report" >"${out%.*}.json"

if [ "$json" -eq 1 ]; then
  printf '%s\n' "$report"
else
  printf '%s (%sx%s tiles, map in %s)\n' "$out" "$cols" "$rows" "${out%.*}.json"
  printf '%s' "$map" | awk 'NF == 5 { printf "  r%sc%s  %ss%s\n", $2, $3, $4, ($5 == "true" ? " (clamped to the last frame)" : "") }'
fi
