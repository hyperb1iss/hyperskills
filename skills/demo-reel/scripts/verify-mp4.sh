#!/usr/bin/env bash
# Check a rendered video against its delivery contract: size, frame rate,
# codec, pixel format, color tags, duration, black and frozen stretches,
# and optionally the share of frames that are not repeats.
#
# Needs ffprobe and ffmpeg (blackdetect, freezedetect, signalstats,
# mpdecimate). Reads the file only; writes nothing.

set -u

usage() {
  cat <<'EOF'
Usage: verify-mp4.sh [options] FILE

Checks (an expectation is only enforced when given, except where noted):
  --expect-size WxH        exact frame size, e.g. 3840x2160
  --expect-fps N           nominal and average frame rate (within 0.5%)
  --expect-codec NAME      ffprobe codec name: h264, hevc, prores, ...
  --expect-pix-fmt NAME    e.g. yuv420p, yuv420p10le
  --expect-color NAME      primaries, transfer and matrix tags (default bt709;
                           "any" disables)
  --expect-range tv|pc     color range (default tv; yuvj* formats count as pc)
  --expect-duration S      duration in seconds
  --tolerance S            duration tolerance in seconds (default 0.1)
  --expect-audio yes|no    whether an audio stream must exist
  --max-black S            fail on a black stretch of S seconds or more
                           (default 1.0; "none" disables)
  --first-frame-min-luma N fail when frame 0's mean luma (8-bit scale) is
                           below N (default 24; a black first frame makes a
                           black preview on GitHub and most players)
  --allow-black-start      skip the first-frame check
  --max-freeze S           fail on a frozen stretch of S seconds or more
                           (default none: deliberate holds are frozen too)
  --min-unique R           fail when fewer than R (0..1) of the frames differ
                           from the frame before (extra decode pass)
  --json                   print one JSON report on stdout
  -h, --help               show this help

Exit codes: 0 every check passed, 1 a check failed, 2 usage error,
            3 ffmpeg or ffprobe missing, 4 unreadable or not a video.
EOF
}

json_str() {
  local s=$1
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  s=${s//$'\n'/\\n}
  s=${s//$'\r'/\\r}
  s=${s//$'\t'/\\t}
  printf '"%s"' "$s"
}

json_num() {
  case $1 in
    '' | N/A | unknown) printf 'null' ;;
    *[!0-9.eE+-]*) json_str "$1" ;;
    *) printf '%s' "$1" ;;
  esac
}

is_number() {
  case $1 in
    '' | *[!0-9.]* | *.*.*) return 1 ;;
    *) return 0 ;;
  esac
}

file=''
expect_size=''
expect_fps=''
expect_codec=''
expect_pix=''
expect_color='bt709'
expect_range='tv'
expect_duration=''
tolerance='0.1'
expect_audio=''
max_black='1.0'
min_luma='24'
check_start=1
max_freeze=''
min_unique=''
json=0

need_value() {
  if [ $# -lt 2 ] || [ -z "$2" ]; then
    printf 'verify-mp4: %s needs a value\n' "$1" >&2
    exit 2
  fi
}

while [ $# -gt 0 ]; do
  case $1 in
    --expect-size) need_value "$@"; expect_size=$2; shift 2 ;;
    --expect-fps) need_value "$@"; expect_fps=$2; shift 2 ;;
    --expect-codec) need_value "$@"; expect_codec=$2; shift 2 ;;
    --expect-pix-fmt) need_value "$@"; expect_pix=$2; shift 2 ;;
    --expect-color) need_value "$@"; expect_color=$2; shift 2 ;;
    --expect-range) need_value "$@"; expect_range=$2; shift 2 ;;
    --expect-duration) need_value "$@"; expect_duration=$2; shift 2 ;;
    --tolerance) need_value "$@"; tolerance=$2; shift 2 ;;
    --expect-audio) need_value "$@"; expect_audio=$2; shift 2 ;;
    --max-black) need_value "$@"; max_black=$2; shift 2 ;;
    --first-frame-min-luma) need_value "$@"; min_luma=$2; shift 2 ;;
    --allow-black-start) check_start=0; shift ;;
    --max-freeze) need_value "$@"; max_freeze=$2; shift 2 ;;
    --min-unique) need_value "$@"; min_unique=$2; shift 2 ;;
    --json) json=1; shift ;;
    -h | --help) usage; exit 0 ;;
    --) shift; break ;;
    -*) printf 'verify-mp4: unknown option %s\n' "$1" >&2; exit 2 ;;
    *)
      if [ -n "$file" ]; then
        printf 'verify-mp4: one file per run\n' >&2
        exit 2
      fi
      file=$1
      shift
      ;;
  esac
done
if [ -z "$file" ] && [ $# -gt 0 ]; then file=$1; fi
if [ -z "$file" ]; then usage >&2; exit 2; fi

case $expect_size in '' | [0-9]*x[0-9]*) ;; *) printf 'verify-mp4: --expect-size takes WxH\n' >&2; exit 2 ;; esac
case $expect_range in tv | pc) ;; *) printf 'verify-mp4: --expect-range takes tv or pc\n' >&2; exit 2 ;; esac
case $expect_audio in '' | yes | no) ;; *) printf 'verify-mp4: --expect-audio takes yes or no\n' >&2; exit 2 ;; esac
for pair in "fps:$expect_fps" "duration:$expect_duration" "tolerance:$tolerance" "luma:$min_luma" \
  "freeze:$max_freeze" "unique:$min_unique"; do
  value=${pair#*:}
  if [ -n "$value" ] && ! is_number "$value"; then
    printf 'verify-mp4: %s must be a number, got %s\n' "${pair%%:*}" "$value" >&2
    exit 2
  fi
done
if [ "$max_black" != none ] && ! is_number "$max_black"; then
  printf 'verify-mp4: --max-black takes seconds or none\n' >&2
  exit 2
fi

for tool in ffprobe ffmpeg; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'verify-mp4: %s not found; run doctor.sh for the install command\n' "$tool" >&2
    exit 3
  fi
done
if [ ! -r "$file" ] || [ -d "$file" ]; then
  printf 'verify-mp4: cannot read %s\n' "$file" >&2
  exit 4
fi

probe() {
  # probe SELECTOR ENTRIES -> key=value lines
  ffprobe -v error -select_streams "$1" -show_entries "$2" -of default=nw=1 "$file" 2>/dev/null
}
field() {
  printf '%s\n' "$1" | awk -F= -v k="$2" '$1 == k { sub(/^[^=]*=/, ""); print; exit }'
}

vinfo=$(probe v:0 stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_frames,color_primaries,color_transfer,color_space,color_range,bit_rate)
if [ -z "$(field "$vinfo" codec_name)" ]; then
  printf 'verify-mp4: no video stream in %s\n' "$file" >&2
  exit 4
fi
finfo=$(ffprobe -v error -show_entries format=duration,bit_rate,size -of default=nw=1 "$file" 2>/dev/null)
ainfo=$(probe a:0 stream=codec_name,sample_rate,channels)

codec=$(field "$vinfo" codec_name)
profile=$(field "$vinfo" profile)
width=$(field "$vinfo" width)
height=$(field "$vinfo" height)
pix_fmt=$(field "$vinfo" pix_fmt)
r_rate=$(field "$vinfo" r_frame_rate)
avg_rate=$(field "$vinfo" avg_frame_rate)
frames=$(field "$vinfo" nb_frames)
primaries=$(field "$vinfo" color_primaries)
transfer=$(field "$vinfo" color_transfer)
matrix=$(field "$vinfo" color_space)
range=$(field "$vinfo" color_range)
vbitrate=$(field "$vinfo" bit_rate)
duration=$(field "$finfo" duration)
size_bytes=$(field "$finfo" size)
acodec=$(field "$ainfo" codec_name)
arate=$(field "$ainfo" sample_rate)
achannels=$(field "$ainfo" channels)

rate_decimal() {
  awk -v r="$1" 'BEGIN { n = split(r, p, "/"); if (n == 2 && p[2] > 0) printf "%.6f", p[1] / p[2]; else if (r + 0 > 0) printf "%.6f", r; }'
}
fps=$(rate_decimal "$r_rate")
avg_fps=$(rate_decimal "$avg_rate")

# Detector pass: black and frozen intervals in one decode. A frame counts as
# black only when 99.5% of its pixels are; dark title cards stay legal.
detect=$(ffmpeg -nostdin -hide_banner -v info -i "$file" -an \
  -vf "blackdetect=d=0.05:pic_th=0.995:pix_th=0.10,freezedetect=n=-60dB:d=0.5" \
  -f null - 2>&1)
if [ $? -ne 0 ]; then
  printf 'verify-mp4: ffmpeg could not decode %s\n' "$file" >&2
  exit 4
fi
black_list=$(printf '%s\n' "$detect" | sed -n 's/.*black_start:\([0-9.e+-]*\) black_end:\([0-9.e+-]*\) black_duration:\([0-9.e+-]*\).*/\1 \2 \3/p')
freeze_list=$(printf '%s\n' "$detect" | awk -v total="${duration:-0}" '
  /lavfi.freezedetect.freeze_start:/ { start = $NF; open = 1 }
  /lavfi.freezedetect.freeze_end:/ { if (open) { printf "%s %s %.6f\n", start, $NF, $NF - start; open = 0 } }
  END { if (open) printf "%s %s %.6f\n", start, total, total - start }')

first_luma=''
if [ "$check_start" -eq 1 ]; then
  first_luma=$(ffmpeg -nostdin -hide_banner -v error -i "$file" -an \
    -vf "select=eq(n\,0),format=yuv420p,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" \
    -frames:v 1 -f null - 2>/dev/null | sed -n 's/^lavfi.signalstats.YAVG=//p' | head -1)
fi

unique_ratio=''
unique_frames=''
if [ -n "$min_unique" ]; then
  unique_frames=$(ffmpeg -nostdin -hide_banner -v error -progress pipe:1 -nostats -i "$file" -an \
    -vf mpdecimate -f null - 2>/dev/null | sed -n 's/^frame=//p' | tail -1)
  if is_number "$frames" && is_number "$unique_frames" && [ "$frames" != 0 ]; then
    unique_ratio=$(awk -v u="$unique_frames" -v n="$frames" 'BEGIN { printf "%.4f", u / n }')
  fi
fi

# Checks: name|ok|expected|actual
checks=''
add_check() {
  checks="${checks}$1|$2|$3|$4
"
}
failed=0
record() {
  # record NAME CONDITION_OK EXPECTED ACTUAL
  if [ "$2" = 1 ]; then add_check "$1" true "$3" "$4"; else add_check "$1" false "$3" "$4"; failed=1; fi
}

if [ -n "$expect_size" ]; then
  [ "${width}x${height}" = "$expect_size" ] && ok=1 || ok=0
  record size "$ok" "$expect_size" "${width}x${height}"
fi
if [ -n "$expect_fps" ]; then
  ok=$(awk -v a="$fps" -v b="$avg_fps" -v e="$expect_fps" 'BEGIN {
    tol = e * 0.005; da = a - e; db = b - e; if (da < 0) da = -da; if (db < 0) db = -db
    print (a != "" && b != "" && da <= tol && db <= tol) ? 1 : 0 }')
  record fps "$ok" "$expect_fps" "nominal ${fps:-?}, average ${avg_fps:-?}"
fi
if [ -n "$expect_codec" ]; then
  [ "$codec" = "$expect_codec" ] && ok=1 || ok=0
  record codec "$ok" "$expect_codec" "$codec"
fi
if [ -n "$expect_pix" ]; then
  [ "$pix_fmt" = "$expect_pix" ] && ok=1 || ok=0
  record pix_fmt "$ok" "$expect_pix" "$pix_fmt"
fi
if [ "$expect_color" != any ]; then
  [ "$primaries" = "$expect_color" ] && [ "$transfer" = "$expect_color" ] && [ "$matrix" = "$expect_color" ] && ok=1 || ok=0
  record color_tags "$ok" "$expect_color for primaries, transfer and matrix" "primaries ${primaries:-none}, transfer ${transfer:-none}, matrix ${matrix:-none}"
fi
actual_range=$range
case $pix_fmt in yuvj*) actual_range=pc ;; esac
case $actual_range in tv | pc) ;; *) actual_range="${range:-unknown}" ;; esac
[ "$actual_range" = "$expect_range" ] && ok=1 || ok=0
record range "$ok" "$expect_range" "$actual_range"
if [ -n "$expect_duration" ]; then
  ok=$(awk -v d="${duration:-}" -v e="$expect_duration" -v t="$tolerance" 'BEGIN {
    if (d == "") { print 0; exit } x = d - e; if (x < 0) x = -x; print (x <= t) ? 1 : 0 }')
  record duration "$ok" "${expect_duration}s within ${tolerance}s" "${duration:-unknown}s"
fi
if [ -n "$expect_audio" ]; then
  if [ -n "$acodec" ]; then have_audio=yes; else have_audio=no; fi
  [ "$have_audio" = "$expect_audio" ] && ok=1 || ok=0
  record audio "$ok" "$expect_audio" "$have_audio${acodec:+ ($acodec)}"
fi
if [ "$max_black" != none ]; then
  longest=$(printf '%s\n' "$black_list" | awk 'NF == 3 && $3 > m { m = $3 } END { printf "%.3f", m + 0 }')
  ok=$(awk -v l="$longest" -v m="$max_black" 'BEGIN { print (l < m) ? 1 : 0 }')
  record black "$ok" "no black stretch of ${max_black}s or more" "longest ${longest}s"
fi
if [ "$check_start" -eq 1 ]; then
  ok=$(awk -v y="${first_luma:-}" -v m="$min_luma" 'BEGIN { print (y != "" && y + 0 >= m) ? 1 : 0 }')
  record first_frame "$ok" "mean luma >= $min_luma" "mean luma ${first_luma:-unknown}"
fi
if [ -n "$max_freeze" ]; then
  longest=$(printf '%s\n' "$freeze_list" | awk 'NF == 3 && $3 > m { m = $3 } END { printf "%.3f", m + 0 }')
  ok=$(awk -v l="$longest" -v m="$max_freeze" 'BEGIN { print (l < m) ? 1 : 0 }')
  record freeze "$ok" "no frozen stretch of ${max_freeze}s or more" "longest ${longest}s"
fi
if [ -n "$min_unique" ]; then
  ok=$(awk -v r="${unique_ratio:-}" -v m="$min_unique" 'BEGIN { print (r != "" && r + 0 >= m) ? 1 : 0 }')
  record unique_frames "$ok" "at least $min_unique of frames unique" "${unique_ratio:-unknown} (${unique_frames:-?} of ${frames:-?})"
fi

intervals_json() {
  printf '%s\n' "$1" | awk 'NF == 3 { printf "%s{\"start\": %s, \"end\": %s, \"duration\": %s}", sep, $1, $2, $3; sep = ", " }'
}

if [ "$json" -eq 1 ]; then
  if [ "$failed" -eq 0 ]; then okword=true; else okword=false; fi
  printf '{"file": %s, "ok": %s,\n' "$(json_str "$file")" "$okword"
  printf ' "probe": {"codec": %s, "profile": %s, "width": %s, "height": %s, "pix_fmt": %s,' \
    "$(json_str "$codec")" "$(json_str "$profile")" "$(json_num "$width")" "$(json_num "$height")" "$(json_str "$pix_fmt")"
  printf ' "fps": %s, "avg_fps": %s, "frames": %s, "duration": %s, "video_bit_rate": %s, "size_bytes": %s,' \
    "$(json_num "$fps")" "$(json_num "$avg_fps")" "$(json_num "$frames")" "$(json_num "$duration")" "$(json_num "$vbitrate")" "$(json_num "$size_bytes")"
  printf ' "color_primaries": %s, "color_transfer": %s, "color_space": %s, "color_range": %s,' \
    "$(json_str "$primaries")" "$(json_str "$transfer")" "$(json_str "$matrix")" "$(json_str "$range")"
  if [ -n "$acodec" ]; then
    printf ' "audio": {"codec": %s, "sample_rate": %s, "channels": %s}},\n' \
      "$(json_str "$acodec")" "$(json_num "$arate")" "$(json_num "$achannels")"
  else
    printf ' "audio": null},\n'
  fi
  printf ' "first_frame_luma": %s, "unique_ratio": %s,\n' "$(json_num "$first_luma")" "$(json_num "$unique_ratio")"
  printf ' "black": [%s], "freeze": [%s],\n' "$(intervals_json "$black_list")" "$(intervals_json "$freeze_list")"
  printf ' "checks": ['
  printf '%s' "$checks" | awk -F'|' '
    function esc(s) { gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s); return s }
    NF >= 4 { printf "%s{\"name\": \"%s\", \"ok\": %s, \"expected\": \"%s\", \"actual\": \"%s\"}", sep, esc($1), $2, esc($3), esc($4); sep = ", " }'
  printf ']}\n'
else
  printf '%s\n' "$file"
  printf '  %s %s, %sx%s, %s fps, %s frames, %ss, %s/%s/%s, range %s%s\n' \
    "$codec" "${profile:-}" "$width" "$height" "${fps:-?}" "${frames:-?}" "${duration:-?}" \
    "${primaries:-none}" "${transfer:-none}" "${matrix:-none}" "$actual_range" "${acodec:+, audio $acodec ${arate}Hz}"
  printf '%s' "$checks" | awk -F'|' 'NF >= 4 { printf "  %-4s %-14s expected %s, got %s\n", ($2 == "true" ? "PASS" : "FAIL"), $1, $3, $4 }'
  printf '%s\n' "$black_list" | awk 'NF == 3 { printf "  note black  %ss to %ss (%ss)\n", $1, $2, $3 }'
  printf '%s\n' "$freeze_list" | awk 'NF == 3 { printf "  note frozen %ss to %ss (%ss)\n", $1, $2, $3 }'
  if [ "$failed" -eq 0 ]; then printf '  ok\n'; else printf '  FAILED\n'; fi
fi
exit "$failed"
