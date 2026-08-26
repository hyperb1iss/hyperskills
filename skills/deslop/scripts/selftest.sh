#!/usr/bin/env bash
# Regression gate for slopscan.pl. Every case here is one the scanner got
# wrong at some point. Run it after any edit to the masker.
#
#   ./skills/deslop/scripts/selftest.sh
#
# Exit 0 when every case matches its expected exit code.

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SCAN="$HERE/slopscan.pl"
FIX="$HERE/../references/fixtures"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

# check NAME EXPECTED_EXIT FILE [SURFACE]
check() {
  local name="$1" want="$2" file="$3" surface="${4:-house}"
  perl "$SCAN" --surface "$surface" "$file" >/dev/null 2>&1
  local got=$?
  if [ "$got" = "$want" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf '  FAIL  %-46s want %s, got %s\n' "$name" "$want" "$got"
  fi
}

# grep_check NAME PATTERN FILE  -- the scan output must mention PATTERN
grep_check() {
  local name="$1" pat="$2" file="$3"
  if perl "$SCAN" "$file" 2>&1 | grep -q "$pat"; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf '  FAIL  %-46s expected output to mention %s\n' "$name" "$pat"
  fi
}

printf 'slopscan regression\n'

# ---- the shipped fixtures ------------------------------------------------
check "slop fixture fires"            20 "$FIX/slop.md"
check "protected fixture stays clean"  0 "$FIX/protected.md"
check "clean fixture stays clean"      0 "$FIX/clean.md"

# ---- fence forms ---------------------------------------------------------
printf -- '---\ntitle: t\n---\n\ntext\n\n```\nem dash \xe2\x80\x94 here\n' > "$TMP/unclosed.md"
check "unclosed fence masks to EOF"    0 "$TMP/unclosed.md"

printf '> ```\n> em dash \xe2\x80\x94 in a quoted fence\n> ```\n' > "$TMP/quotefence.md"
check "fence inside blockquote"        0 "$TMP/quotefence.md"

printf '````\nem dash \xe2\x80\x94 and ``` inside\n````\n' > "$TMP/fourtick.md"
check "four-backtick fence"            0 "$TMP/fourtick.md"

printf '````md\n```\nem dash \xe2\x80\x94 nested\n```\n````\n' > "$TMP/nested.md"
check "nested fences"                  0 "$TMP/nested.md"

printf '```\ncode with \xe2\x80\x94 dash\n```not-a-closer\nmore code \xe2\x80\x94 here\n```\n' > "$TMP/faux.md"
check "code line resembling a closer"  0 "$TMP/faux.md"

# a closer indented differently from its opener must still close, and prose
# after it must remain visible
printf '  ```\n  code \xe2\x80\x94 dash\n   ```\n\nvisible prose with an em dash \xe2\x80\x94 here\n' > "$TMP/indentclose.md"
check "closer at a different indent"  20 "$TMP/indentclose.md"
grep_check "prose after closer stays visible" "visible prose" "$TMP/indentclose.md"

# ---- other protected regions --------------------------------------------
printf -- '---\r\ntitle: has an em dash \xe2\x80\x94 here\r\n---\r\n\r\nplain text\r\n' > "$TMP/crlf.md"
check "CRLF frontmatter"               0 "$TMP/crlf.md"

printf 'inline only: `a \xe2\x80\x94 b`' > "$TMP/inline.md"
check "em dash only inside inline code" 0 "$TMP/inline.md"

printf 'a multiline span: `first line\nsecond \xe2\x80\x94 line` done\n' > "$TMP/multiline.md"
check "multiline inline code span"     0 "$TMP/multiline.md"

printf 'see [docs](<https://x.test/a b?utm_source=chatgpt.com>) here\n' > "$TMP/anglelink.md"
check "angle-bracket link target"      0 "$TMP/anglelink.md"

printf 'see [docs][d] here\n\n[d]: https://x.test/a?utm_source=chatgpt.com\n' > "$TMP/reflink.md"
check "reference-style link target"    0 "$TMP/reflink.md"

printf 'visit <https://x.test/a?utm_source=chatgpt.com> now\n' > "$TMP/autolink.md"
check "autolink target"                0 "$TMP/autolink.md"

printf '> quoted line one\n> continues \xe2\x80\x94 here\nlazy continuation \xe2\x80\x94 still quoted\n\nplain\n' > "$TMP/lazyquote.md"
check "lazy blockquote continuation"   0 "$TMP/lazyquote.md"

printf '\n        eight-space indented code \xe2\x80\x94 dash\n' > "$TMP/indent8.md"
check "eight-space indented code"      0 "$TMP/indent8.md"

# ---- degenerate inputs --------------------------------------------------
: > "$TMP/empty.md"
check "empty file"                     0 "$TMP/empty.md"

printf -- '---\ntitle: only frontmatter \xe2\x80\x94 dash\n---\n' > "$TMP/frontonly.md"
check "frontmatter-only file"          0 "$TMP/frontonly.md"

printf 'no trailing newline \xe2\x80\x94 dash' > "$TMP/nonewline.md"
check "no trailing newline still fires" 20 "$TMP/nonewline.md"

perl -e 'print "a" x 2_000_000, "\n"' > "$TMP/longline.md"
check "two-million-character line"     0 "$TMP/longline.md"

# ---- interface contract -------------------------------------------------
check "unreadable input never reports clean" 30 "$TMP/does-not-exist.md"
perl "$SCAN" --surface houes "$FIX/clean.md" >/dev/null 2>&1
if [ $? -ne 0 ]; then pass=$((pass + 1)); else
  fail=$((fail + 1)); printf '  FAIL  %-46s misspelled surface was accepted\n' "surface enum validated"
fi

printf 'a dagger marker\xe2\x80\xa01 here\n' > "$TMP/dagger.md"
check "dagger citation marker"         20 "$TMP/dagger.md"

printf 'the author wrote \xe2\x80\x9cthis\xe2\x80\x9d deliberately\n' > "$TMP/curly.md"
check "curly quotes hard on house"     20 "$TMP/curly.md"
check "curly quotes soft on a sample"  10 "$TMP/curly.md" sample

printf 'an em dash \xe2\x80\x94 in someone else prose\n' > "$TMP/dash.md"
check "dash hard on house"             20 "$TMP/dash.md"
check "dash hard on our agent files"   20 "$TMP/dash.md" agent
check "dash soft on published prose"   10 "$TMP/dash.md" published

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
