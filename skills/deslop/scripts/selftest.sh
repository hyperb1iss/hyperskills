#!/usr/bin/env bash
# Regression gate for slopscan.pl. Cases cover preservation, candidate
# classification, and interface behavior. Run after changing the scanner.
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

# compare_check NAME EXPECTED_EXIT ORIGINAL REVISED [SURFACE]
compare_check() {
  local name="$1" want="$2" orig="$3" rev="$4" surface="${5:-house}"
  perl "$SCAN" --compare "$orig" "$rev" --surface "$surface" >/dev/null 2>&1
  local got=$?
  if [ "$got" = "$want" ]; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf '  FAIL  %-46s want %s, got %s\n' "$name" "$want" "$got"
  fi
}

# compare_grep NAME PATTERN ORIGINAL REVISED [SURFACE] -- output must mention PATTERN
compare_grep() {
  local name="$1" pat="$2" orig="$3" rev="$4" surface="${5:-house}"
  if perl "$SCAN" --compare "$orig" "$rev" --surface "$surface" 2>&1 | grep -qF -- "$pat"; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf '  FAIL  %-46s expected output to mention %s\n' "$name" "$pat"
  fi
}

# absent_check NAME PATTERN FILE -- the scan output must not mention PATTERN
absent_check() {
  local name="$1" pat="$2" file="$3"
  if perl "$SCAN" "$file" 2>&1 | grep -qF -- "$pat"; then
    fail=$((fail + 1))
    printf '  FAIL  %-46s output unexpectedly mentions %s\n' "$name" "$pat"
  else
    pass=$((pass + 1))
  fi
}

# suppressed_check NAME FILE -- the advisory must fire, so an over-mask is visible
suppressed_check() {
  local name="$1" file="$2"
  if perl "$SCAN" "$file" 2>&1 | grep -q "masking suppressed"; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf '  FAIL  %-46s expected a masking-suppressed advisory\n' "$name"
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

# ---- CommonMark forms a round-3 review broke ----------------------------
printf '\n    first indented code line\n    second line with an em dash \xe2\x80\x94 here\n    third line\n' > "$TMP/indentmulti.md"
check "multiline indented code block"  0 "$TMP/indentmulti.md"

printf 'see [docs](https://x.test/a_(b)_c?utm_source=chatgpt.com) here\n' > "$TMP/balanced.md"
check "balanced-parenthesis destination"  0 "$TMP/balanced.md"

printf 'see [docs](https://x.test/a "a title \xe2\x80\x94 with a dash") here\n' > "$TMP/linktitle.md"
check "link title is markup, not prose"   0 "$TMP/linktitle.md"

# a heading terminates a lazy blockquote, so the heading must stay visible
printf '> quoted line with a dash \xe2\x80\x94 here\n# Visible heading with a dash \xe2\x80\x94 here\n' > "$TMP/quoteheading.md"
check "heading after blockquote stays visible" 20 "$TMP/quoteheading.md"
grep_check "heading text is not masked" "Visible heading" "$TMP/quoteheading.md"

# ---- forms found by self-probing after round 3 --------------------------
printf '\xef\xbb\xbf---\ntitle: dash \xe2\x80\x94 here\n---\n\nclean prose here.\n' > "$TMP/bom.md"
check "byte-order mark before frontmatter"  0 "$TMP/bom.md"

printf '<!-- comment dash \xe2\x80\x94 here -->\n\nclean prose here.\n' > "$TMP/htmlcomment.md"
check "HTML comment never reaches a reader"  0 "$TMP/htmlcomment.md"

printf 'visit https://x.test/a\xe2\x80\x94b directly today\n' > "$TMP/bareurl.md"
check "bare URL is not prose"                0 "$TMP/bareurl.md"

printf '![alt text](https://x.test/a\xe2\x80\x94b?utm_source=chatgpt.com)\n\nclean prose.\n' > "$TMP/image.md"
check "image destination"                    0 "$TMP/image.md"

# a setext heading is visible prose, so its text must still be scanned
printf 'Heading with a dash \xe2\x80\x94 here\n=====\n\nclean prose.\n' > "$TMP/setext.md"
check "setext heading text is scanned"      20 "$TMP/setext.md"

printf '> > deeply quoted dash \xe2\x80\x94 here\n> > more\n\nclean.\n' > "$TMP/nestedquote.md"
check "nested blockquote"                    0 "$TMP/nestedquote.md"

printf '>     indented code inside a quote \xe2\x80\x94 dash\n\nclean.\n' > "$TMP/quoteindent.md"
check "indented code inside a blockquote"    0 "$TMP/quoteindent.md"

printf -- '- item\n\n  ```\n  code \xe2\x80\x94 dash\n  ```\n\n- next item\n' > "$TMP/listfence.md"
check "fenced code inside a list item"       0 "$TMP/listfence.md"

printf '| a | b |\n| - | - |\n| `x \xe2\x80\x94 y` | z |\n' > "$TMP/tablecode.md"
check "inline code inside a table cell"      0 "$TMP/tablecode.md"

printf 'a span with a tick: ``inner ` tick \xe2\x80\x94 dash`` done\n' > "$TMP/spaninspan.md"
check "backtick run inside a code span"      0 "$TMP/spaninspan.md"

printf 'see [text [with] brackets](https://x.test/a?utm_source=chatgpt.com) ok\n' > "$TMP/linkbrackets.md"
check "link text containing brackets"        0 "$TMP/linkbrackets.md"

printf 'text[^1]\n\n[^1]: https://x.test/a?utm_source=chatgpt.com\n' > "$TMP/footnote.md"
check "footnote definition target"           0 "$TMP/footnote.md"

printf '\n\ttab indented code \xe2\x80\x94 dash\n\tsecond line\n' > "$TMP/tabindent.md"
check "tab-indented code block"              0 "$TMP/tabindent.md"

printf 'text\r\n\r\n```\r\ncode \xe2\x80\x94 dash\r\n```\r\n\r\nclean\r\n' > "$TMP/crlffence.md"
check "CRLF inside a fence"                  0 "$TMP/crlffence.md"

# ---- false-clean classes found in round 4 -------------------------------
# Each of these masked visible prose and exited 0 before the fix. A false clean
# is the severe direction, because the scanner lies instead of over-reporting.
printf -- '> quoted\n```\ncode\n```\nvisible prose with a dash \xe2\x80\x94 here\n' > "$TMP/quotefencepr.md"
check "fence ends a quote, prose after stays visible" 20 "$TMP/quotefencepr.md"

printf 'escaped \\`tick\\` then a dash \xe2\x80\x94 in prose\n' > "$TMP/escapedopener.md"
check "escaped backtick does not open a span"  20 "$TMP/escapedopener.md"

printf 'a ``two-tick opener and a ```three-tick run, then a dash \xe2\x80\x94 in prose\n' > "$TMP/runlength.md"
check "closing backtick run must match length" 20 "$TMP/runlength.md"

printf 'a \\](not-a-link) and a dash \xe2\x80\x94 in prose\n' > "$TMP/pseudolink.md"
check "pseudo-link needs a real label"        20 "$TMP/pseudolink.md"

printf 'text[^n]\n\n[^n]: dash \xe2\x80\x94 in the footnote body\n' > "$TMP/footnotebody.md"
check "footnote body is prose"                20 "$TMP/footnotebody.md"

printf 'see ](<https://x.test/a\nb>) and a dash \xe2\x80\x94 in prose\n' > "$TMP/anglenewline.md"
check "angle destination cannot span a newline" 20 "$TMP/anglenewline.md"

# A closer may sit up to three columns past its list item's content, so a
# fence closed deeper than the list indent still ends there and the prose
# after it stays visible.
printf -- 'ok\n\n- item\n\n  ```\n  code\n    ```\n\nvisible prose with a dash \xe2\x80\x94 here\n' > "$TMP/listdeep.md"
check "list fence closer past the item indent"  20 "$TMP/listdeep.md"
grep_check "prose after a deep list closer is visible" 'visible prose' "$TMP/listdeep.md"

# ---- list containers decide what indentation means ---------------------------
# Inside a list item, indentation up to the item's content is list content,
# and only four or more columns past it is code.
printf -- '- Parent\n\n    - nested wording with a dash \xe2\x80\x94 here\n' > "$TMP/nestedprose.md"
check "nested bullet after a blank line is prose" 20 "$TMP/nestedprose.md"
printf -- '- Parent\n\n      code in the item \xe2\x80\x94 here\n' > "$TMP/listcode.md"
check "code past the item content stays masked"   0 "$TMP/listcode.md"
printf 'para\n\n    top-level code \xe2\x80\x94 here\n' > "$TMP/topcode.md"
check "top-level indented code stays masked"      0 "$TMP/topcode.md"
printf -- '- a\n  - b\n\n    ```\n    code \xe2\x80\x94 here\n    ```\n\nafter\n' > "$TMP/nestedfence.md"
check "fence inside a nested item stays masked"   0 "$TMP/nestedfence.md"
printf -- '- a\n\n  ```\n  code\n\nvisible prose with a dash \xe2\x80\x94 here\n' > "$TMP/itemends.md"
check "the item ending closes its fence"         20 "$TMP/itemends.md"
suppressed_check "protected fixture reports its suppressions" "$FIX/protected.md"

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
check "dagger footnote needs judgment" 10 "$TMP/dagger.md"

printf 'the author wrote \xe2\x80\x9cthis\xe2\x80\x9d deliberately\n' > "$TMP/curly.md"
check "curly quotes hard on house"     20 "$TMP/curly.md"
check "curly quotes soft on a sample"  10 "$TMP/curly.md" sample
check "curly quotes soft on published" 10 "$TMP/curly.md" published

printf 'Wait\342\200\246 10\302\240km away.\n' > "$TMP/typography.md"
check "house typography remains enforced" 20 "$TMP/typography.md" house
check "sample typography needs judgment" 10 "$TMP/typography.md" sample
check "published typography needs judgment" 10 "$TMP/typography.md" published

printf '\343\200\220Notice\343\200\221 Read the instructions.\n' > "$TMP/brackets.md"
check "brackets are not provider proof" 10 "$TMP/brackets.md" published

printf 'Open the lid. Check the seal. Close the lid. Press the switch.\n' > "$TMP/short.md"
check "short instructions remain clean" 0 "$TMP/short.md"
short_output=$(perl "$SCAN" "$TMP/short.md")
if [[ "$short_output" == *OVER-CORRECTED* || "$short_output" == *'flat, look'* ]]; then
  fail=$((fail + 1)); printf '  FAIL  rhythm diagnostics asserted a quality verdict\n'
else
  pass=$((pass + 1))
fi

io_output=$(perl "$SCAN" --json "$TMP/missing-json.md" 2>/dev/null)
io_exit=$?
if [[ "$io_exit" -eq 30 && "$io_output" == *'"io_errors": 1'* ]]; then
  pass=$((pass + 1))
else
  fail=$((fail + 1)); printf '  FAIL  JSON output concealed unreadable input\n'
fi

check "directory input is an I/O error" 30 "$TMP"
: > "$TMP/empty.md"
check "empty regular file is valid" 0 "$TMP/empty.md"
printf '\377' > "$TMP/invalid-utf8.md"
check "invalid UTF-8 is an I/O error" 30 "$TMP/invalid-utf8.md"
io_output=$(perl "$SCAN" --json "$TMP" "$TMP/empty.md" 2>/dev/null)
io_exit=$?
if [[ "$io_exit" -eq 30 && "$io_output" == *'"io_errors": 1'* ]]; then
  pass=$((pass + 1))
else
  fail=$((fail + 1)); printf '  FAIL  valid sibling concealed directory input error\n'
fi

printf 'an em dash \xe2\x80\x94 in someone else prose\n' > "$TMP/dash.md"
check "dash hard on house"             20 "$TMP/dash.md"
check "dash hard on our agent files"   20 "$TMP/dash.md" agent
check "dash soft on published prose"   10 "$TMP/dash.md" published

# ---- heading case: consistency is the signal, not the case ----------------
# uniform title case is a style choice; flagging every heading flooded the
# report with 499 candidates on the first repo-wide dogfood scan
printf '# My Great Tool\n\n## Getting Started Guide\n\nBody text here.\n\n## Advanced Usage Notes\n\nMore body.\n' > "$TMP/titlecase.md"
check "uniform title-case file is clean"     0 "$TMP/titlecase.md"
printf '# My tool\n\n## Getting started\n\nBody text here.\n\n## Advanced Usage Notes\n\nMore body.\n\n## Known limitations\n\nEnd.\n' > "$TMP/mixedcase.md"
check "mixed heading case fires"            10 "$TMP/mixedcase.md"
grep_check "minority heading is the one named" 'title-case heading in a sentence-case file:7' "$TMP/mixedcase.md"

# setext headings count toward the case-consistency check too
printf 'My Great Tool\n=============\n\nBody text here.\n\nAnother heading here\n----\n\nMore body.\n' > "$TMP/setextcase.md"
check "mixed-case setext headings fire"       10 "$TMP/setextcase.md"
# an equal split has no majority, and the label must not invent one
printf '# Getting Started Guide\n\nBody text here.\n\n# Known limitations\n\nEnd.\n' > "$TMP/tiecase.md"
check "heading-case tie still fires"          10 "$TMP/tiecase.md"
grep_check "tie label claims no majority"     'mixed heading case, no majority' "$TMP/tiecase.md"

# ---- agent surface exempts structure, per the surface matrix ---------------
printf -- '- **Speed:** fast\n' > "$TMP/boldlead.md"
check "bold-lead bullet is a house candidate" 10 "$TMP/boldlead.md"
check "agent surface skips bold-lead check"    0 "$TMP/boldlead.md" agent
check "agent surface skips heading case"       0 "$TMP/mixedcase.md" agent

# ---- stacked rhetorical frames (N19) ---------------------------------------
# Three distinct frame families in one paragraph fire; repetition of a single
# family and frames split across list items stay clean.
printf 'We queue the work rather than dropping it, so the retry loop stays empty, which means the backlog is the whole story.\n' > "$TMP/stacked.md"
check "three frame families in one paragraph fire"  10 "$TMP/stacked.md"
grep_check "stacked frames are named" 'stacked frames' "$TMP/stacked.md"
printf 'The job runs, so the queue drains, so the worker idles, so the pool shrinks.\n' > "$TMP/oneframe.md"
check "single-family repetition stays clean"         0 "$TMP/oneframe.md"
printf -- '- kept rather than dropped\n- retries, so the queue drains\n- the delay, not the size\n' > "$TMP/listframes.md"
check "frames across separate list items stay clean" 0 "$TMP/listframes.md"

# ---- apostrophe variant glyphs ---------------------------------------------
# A variant between letters is a house-style failure; a prime after a digit
# is legitimate technical notation.
printf 'this don\xc2\xb4t and this don\xe2\x80\xb2t read as apostrophes\n' > "$TMP/aposvariant.md"
check "apostrophe variant between letters fires"  20 "$TMP/aposvariant.md"
printf 'the 5\xe2\x80\xb2 UTR and a bare accent \xc2\xb4 alone stay clean\n' > "$TMP/primeok.md"
check "prime after a digit stays clean"            0 "$TMP/primeok.md"

# ---- transactional effort framing ------------------------------------------
printf 'the check is cheap and buys you headroom\n' > "$TMP/transact.md"
check "transactional effort framing is a candidate" 10 "$TMP/transact.md"
grep_check "transactional framing is named" 'transactional effort framing' "$TMP/transact.md"

# ---- inline spans stop at blank lines --------------------------------------
# two unpaired backtick runs in different paragraphs must not pair up and
# blank the prose between them; this hid 24 prose dashes in AGENTS.md
printf 'See (```dot) syntax.\n\nA dash \342\200\224 in prose.\n\nUse ```dot again.\n' > "$TMP/tickpair.md"
check "unpaired tick runs do not span paragraphs" 20 "$TMP/tickpair.md"
grep_check "the dash between them is reported"  'em or en dash:3' "$TMP/tickpair.md"
printf 'prose `code \342\200\224\nstill code` after\n' > "$TMP/softwrap.md"
check "span across a soft break still masks"     0 "$TMP/softwrap.md"

# ---- new candidates: importance, tradeoff, contrast, arrows ----------------
grep_check "slop fixture has an importance flag"   'importance flag:20' "$FIX/slop.md"
grep_check "slop fixture has a tradeoff denial"    'tradeoff denial:20' "$FIX/slop.md"
grep_check "slop fixture has a corrective contrast" 'corrective contrast:22' "$FIX/slop.md"
grep_check "slop fixture has a shorthand arrow"    'shorthand arrow:22' "$FIX/slop.md"

printf 'This matters.\n' > "$TMP/imp-bare.md"
check "bare sentence-initial This matters"      10 "$TMP/imp-bare.md"
printf "Here's why it matters for builds.\n" > "$TMP/imp-why.md"
check "why it matters fires"                    10 "$TMP/imp-why.md"
printf 'What matters is the key. The key matters most.\n' > "$TMP/imp-plain.md"
check "plain matters stays clean"                0 "$TMP/imp-plain.md"
printf 'It fails because\nthis matters to the cache.\n' > "$TMP/imp-wrap.md"
check "wrapped lowercase this matters is clean"  0 "$TMP/imp-wrap.md"

printf 'It runs faster without compromising accuracy.\n' > "$TMP/trade.md"
check "without compromising fires"              10 "$TMP/trade.md"
printf 'It runs without a cache.\n' > "$TMP/trade-ok.md"
check "plain without stays clean"                0 "$TMP/trade-ok.md"
printf 'Replan without losing the goal.\n' > "$TMP/trade-kept.md"
check "without losing a named thing is clean"    0 "$TMP/trade-kept.md"

# ---- padding phrases from older and open-weight model output ---------------
printf 'Certainly! Here is a comprehensive overview of the migration.\n\nAs we delve into the details, it is important to note that the team made progress, a true testament to collaboration.\n\nWe are not just moving queues, we'"'"'re building a platform.\n\nIn conclusion, the future of messaging is bright.\n\nI hope this helps! Let me know if you'"'"'d like me to expand on any section.\n' > "$TMP/padded.md"
check "padded chat text yields candidates"      10 "$TMP/padded.md" sample
grep_check "opener is a chatbot artifact"        'chatbot artifact:1' "$TMP/padded.md"
grep_check "closer is a chatbot artifact"        'chatbot artifact:9' "$TMP/padded.md"
grep_check "filler phrase is named"              'filler phrase:3' "$TMP/padded.md"
grep_check "inflated significance is named"      'inflated significance:3' "$TMP/padded.md"
grep_check "stock vocabulary is named"           'stock vocabulary:3' "$TMP/padded.md"
grep_check "dash-free not-just reframe is named" 'negative parallelism:5' "$TMP/padded.md"
grep_check "generic close is named"              'generic close:7' "$TMP/padded.md"
printf 'Of course the cache can miss, so the caller retries. It certainly helps to note the limit. The logs that were not only large but unsorted went first. Let me know if you have any questions.\n' > "$TMP/padded-ok.md"
absent_check "mid-sentence of course is clean"   'chatbot artifact' "$TMP/padded-ok.md"
absent_check "plain note and closer are clean"   'filler phrase' "$TMP/padded-ok.md"
printf 'Ultimately, the build passed. The world of work changed.\n' > "$TMP/padded-ok2.md"
check "ordinary transitions stay clean"          0 "$TMP/padded-ok2.md"

printf 'Retry the request rather than simply failing.\n' > "$TMP/contrast.md"
check "rather than simply fires"                10 "$TMP/contrast.md"
printf 'They are more than a list; they are the contract.\n' > "$TMP/morethan.md"
check "are more than a X, they fires"           10 "$TMP/morethan.md"
printf 'Retry the request rather than failing.\n' > "$TMP/contrast-ok.md"
check "bare rather than stays clean"             0 "$TMP/contrast-ok.md"
printf 'There are more than a dozen tests.\n' > "$TMP/morethan-ok.md"
check "more than a dozen without it is clean"    0 "$TMP/morethan-ok.md"

printf 'parse -> validate -> store\n' > "$TMP/arrow.md"
check "ascii arrow between words fires"         10 "$TMP/arrow.md"
printf 'ingest \xe2\x86\x92 index\n' > "$TMP/arrow-uni.md"
check "unicode arrow between words fires"       10 "$TMP/arrow-uni.md"
printf '(input) => output\n' > "$TMP/arrow-paren.md"
check "arrow after a parenthesis fires"         10 "$TMP/arrow-paren.md"
printf '`make check` -> passes\n\n`make test` \xe2\x86\x92 89 passed\n\nsee `a` -> `b`\n' > "$TMP/arrow-receipt.md"
check "arrow after a code span is a receipt"     0 "$TMP/arrow-receipt.md"
printf '| step | parse -> store |\n| ---- | -------------- |\n| a    | b -> c         |\n' > "$TMP/arrow-table.md"
check "arrow in a table row stays clean"         0 "$TMP/arrow-table.md"
printf 'retries went 3 -> 5 and x >= 2\n' > "$TMP/arrow-digits.md"
check "arrow between digits stays clean"         0 "$TMP/arrow-digits.md"

# ---- density diagnostics: descriptive, never gating -------------------------
perl -e 'print join(" ", ("alpha") x 50), ".\n"' > "$TMP/longsent.md"
check "a long sentence does not gate"            0 "$TMP/longsent.md"
grep_check "long sentence is named with line and size" 'line 1 (50 words)' "$TMP/longsent.md"
perl -e 'print "- ", join(" ", ("beta") x 4), "\n" for 1 .. 20' > "$TMP/bullets.md"
absent_check "unpunctuated bullets are not one sentence" 'long sentences' "$TMP/bullets.md"
printf 'One two three four five; six seven eight nine ten.\n' > "$TMP/semis.md"
semis_json=$(perl "$SCAN" --json "$TMP/semis.md" 2>/dev/null)
if [[ "$semis_json" == *'"semicolons_per_1000_words": 100'* \
   && "$semis_json" == *'"longest_paragraph": {'* \
   && "$semis_json" == *'"long_sentences": []'* ]]; then
  pass=$((pass + 1))
else
  fail=$((fail + 1)); printf '  FAIL  density diagnostics missing from JSON\n'
fi
grep_check "density line reports semicolons" 'semicolons per 1,000 words' "$TMP/semis.md"

# ---- compare mode -----------------------------------------------------------
CO="$FIX/compare-original.md"
CR="$FIX/compare-revised.md"
compare_check "identical files compare clean"      0 "$CO" "$CO"
compare_check "fixture revision fails"            20 "$CO" "$CR"
compare_grep "altered inline code is hard" 'protected inline code altered: `--nodes 4` now `--nodes 8` (original line 11' "$CO" "$CR"
compare_grep "altered fenced code is hard" 'protected fenced code altered:' "$CO" "$CR"
compare_grep "dropped range keeps its unit" 'dropped number: 2-4 node (original line 9)' "$CO" "$CR"
compare_grep "introduced number is named"   'introduced number: 3x (revised line 9)' "$CO" "$CR"
compare_grep "dropped author-year citation" 'dropped citation: Smith et al., 2024' "$CO" "$CR"
compare_grep "dropped bracket citation"     'dropped citation: [3]' "$CO" "$CR"
compare_grep "dropped bare URL"             'dropped url: https://x.test/metrics' "$CO" "$CR"
compare_grep "fallen hedge is counted"      'hedge or limiter fell: may 1 to 0' "$CO" "$CR"
compare_grep "risen certainty is counted"   'certainty word rose: always 0 to 1' "$CO" "$CR"
compare_grep "introduced pattern is named"  'revision introduced: participial tail 0 to 1' "$CO" "$CR"
compare_grep "size is reported"             'size: 51 words to 43 words, ratio 0.84' "$CO" "$CR"

# reflowed quotes, a code block moved out of a list, renumbered steps, and a
# thousands separator are all the same content
printf '> a quoted line that\n> wraps here.\n\n- item\n\n  ```sh\n  make x\n  ```\n\n1. first step\n2. second step\n\nIt costs 1,000 units.\n' > "$TMP/c-same-o.md"
printf 'item\n\n> a quoted line that wraps here.\n\n```sh\nmake x\n```\n\n- first step\n- second step\n\nIt costs 1000 units.\n' > "$TMP/c-same-r.md"
compare_check "layout-only edits compare clean"    0 "$TMP/c-same-o.md" "$TMP/c-same-r.md"

# a deleted span plus an unrelated new one is missing plus new, not altered
printf 'Use `A` then `B` then `C`.\n' > "$TMP/c-span-o.md"
printf 'Use `A` then `C` then `D`.\n' > "$TMP/c-span-r.md"
compare_check "deleted protected span is hard"     20 "$TMP/c-span-o.md" "$TMP/c-span-r.md"
compare_grep "deleted span is called missing" 'protected inline code missing: `B` (original line 1)' "$TMP/c-span-o.md" "$TMP/c-span-r.md"
compare_grep "unrelated span is called new"   'protected inline code new: `D` (revised line 1)' "$TMP/c-span-o.md" "$TMP/c-span-r.md"
printf 'Use `A` then `B` then `C`, or `E`.\n' > "$TMP/c-span-o-plus.md"
compare_check "a new protected span is a candidate" 10 "$TMP/c-span-o.md" "$TMP/c-span-o-plus.md"

printf "The job may take about 10 minutes. It doesn't retry.\n" > "$TMP/c-hedge-o.md"
printf 'The job takes 10 minutes. It retries.\n' > "$TMP/c-hedge-r.md"
compare_check "lost hedges are candidates only"    10 "$TMP/c-hedge-o.md" "$TMP/c-hedge-r.md"
compare_grep "contracted negation counts as not" 'hedge or limiter fell: not 1 to 0' "$TMP/c-hedge-o.md" "$TMP/c-hedge-r.md"

printf 'The job takes ten minutes.\n' > "$TMP/c-dash-o.md"
printf 'The job takes ten minutes \xe2\x80\x94 usually.\n' > "$TMP/c-dash-r.md"
compare_check "house typography still hard in compare" 20 "$TMP/c-dash-o.md" "$TMP/c-dash-r.md"
compare_check "published typography is a candidate"    10 "$TMP/c-dash-o.md" "$TMP/c-dash-r.md" published
compare_grep "published dash reads as introduced" 'revision introduced: em or en dash 0 to 1' "$TMP/c-dash-o.md" "$TMP/c-dash-r.md" published

compare_check "unreadable compare input"           30 "$CO" "$TMP/does-not-exist.md"
perl "$SCAN" --compare "$CO" >/dev/null 2>&1
if [ $? -eq 2 ]; then pass=$((pass + 1)); else
  fail=$((fail + 1)); printf '  FAIL  %-46s one-file compare was not a usage error\n' "compare arity validated"
fi
cmp_json=$(perl "$SCAN" --compare --json "$CO" "$CR" 2>/dev/null)
if [[ "$cmp_json" == *'"mode": "compare"'* && "$cmp_json" == *'"ratio": 0.84'* \
   && "$cmp_json" == *'"hard": 2'* ]]; then
  pass=$((pass + 1))
else
  fail=$((fail + 1)); printf '  FAIL  compare JSON lacks mode, size, or counts\n'
fi

# ---- compare: layout normalizes, payload stays exact ------------------------
printf '> ```py\n> s = "a  b"\n> ```\n' > "$TMP/c-qcode-o.md"
printf '> ```py\n> s = "a b"\n> ```\n' > "$TMP/c-qcode-r.md"
compare_check "whitespace in quoted code is payload"  20 "$TMP/c-qcode-o.md" "$TMP/c-qcode-r.md"
printf '```py\ns = """a   \nb"""\n```\n' > "$TMP/c-trail-o.md"
printf '```py\ns = """a\nb"""\n```\n' > "$TMP/c-trail-r.md"
compare_check "trailing spaces in code are payload"   20 "$TMP/c-trail-o.md" "$TMP/c-trail-r.md"
compare_grep "an invisible change says so" 'whitespace differs' "$TMP/c-trail-o.md" "$TMP/c-trail-r.md"
printf '> quoted prose that\n> wraps, then code:\n>\n>     x  =  1\n' > "$TMP/c-qwrap-o.md"
printf '> quoted prose that wraps, then code:\n>\n>     x  =  1\n' > "$TMP/c-qwrap-r.md"
compare_check "quoted prose may reflow around code"    0 "$TMP/c-qwrap-o.md" "$TMP/c-qwrap-r.md"
printf -- '- a\n\n      make  x\n' > "$TMP/c-lcode-o.md"
printf -- '- a\n\n      make x\n' > "$TMP/c-lcode-r.md"
compare_check "edited code inside a list item is hard" 20 "$TMP/c-lcode-o.md" "$TMP/c-lcode-r.md"
printf 'x\n\n```sh\nmake  x\n```\n' > "$TMP/c-move-o.md"
printf -- '- a\n  - b\n\n    ```sh\n    make  x\n    ```\n' > "$TMP/c-move-r.md"
compare_check "code moved into a nested item matches"   0 "$TMP/c-move-o.md" "$TMP/c-move-r.md"

printf -- '- Parent\n\n    - old wording here\n' > "$TMP/c-nest-o.md"
printf -- '- Parent\n\n    - new wording here\n' > "$TMP/c-nest-r.md"
compare_check "nested list prose edits are not code"    0 "$TMP/c-nest-o.md" "$TMP/c-nest-r.md"

printf 'Temperature is -5 degrees and drift is -0.5 units.\n' > "$TMP/c-neg-o.md"
printf 'Temperature is -6 degrees and drift is -0.7 units.\n' > "$TMP/c-neg-r.md"
compare_check "changed negative numbers are candidates" 10 "$TMP/c-neg-o.md" "$TMP/c-neg-r.md"
compare_grep "a negative keeps its sign" 'dropped number: -5 degrees' "$TMP/c-neg-o.md" "$TMP/c-neg-r.md"
compare_grep "a negative decimal keeps its sign" 'dropped number: -0.5 units' "$TMP/c-neg-o.md" "$TMP/c-neg-r.md"
printf 'Use x-5, v2-4, 2026-11-20, and path/-3 here.\n' > "$TMP/c-nosign-o.md"
printf 'Use x-5, v2-4, 2026-11-20, and path/-3 there.\n' > "$TMP/c-nosign-r.md"
compare_check "identifiers, ranges, dates, paths stay unsigned" 0 "$TMP/c-nosign-o.md" "$TMP/c-nosign-r.md"

printf 'See https://example.org/a_(one) for details.\n' > "$TMP/c-paren-o.md"
printf 'See https://example.org/a_(two) for details.\n' > "$TMP/c-paren-r.md"
compare_check "a URL keeps balanced parentheses"       10 "$TMP/c-paren-o.md" "$TMP/c-paren-r.md"
compare_grep "the whole URL is named" 'dropped url: https://example.org/a_(one)' "$TMP/c-paren-o.md" "$TMP/c-paren-r.md"
printf 'See it (https://x.test/a) today.\n' > "$TMP/c-wrap-url-o.md"
printf 'See it at https://x.test/a today.\n' > "$TMP/c-wrap-url-r.md"
compare_check "a prose parenthesis is not part of a URL" 0 "$TMP/c-wrap-url-o.md" "$TMP/c-wrap-url-r.md"

printf 'As shown by Smith et al. (2024) the cache helps.\n' > "$TMP/c-reflow-o.md"
printf 'As shown by Smith et al.\n(2024) the cache helps.\n' > "$TMP/c-reflow-r.md"
compare_check "a reflowed citation is the same citation" 0 "$TMP/c-reflow-o.md" "$TMP/c-reflow-r.md"

# ---- soft wraps and quantities in candidates ---------------------------------
printf 'It is important to\nnote the cache.\n' > "$TMP/wrapfill.md"
check "a phrase split by a soft wrap fires"           10 "$TMP/wrapfill.md"
grep_check "the wrapped phrase cites its first line" 'filler phrase:1' "$TMP/wrapfill.md"
printf 'It is important to\n\nnote the cache.\n' > "$TMP/parafill.md"
check "a paragraph break is not a soft wrap"           0 "$TMP/parafill.md"
printf 'There are more than a dozen tests; they run nightly.\n' > "$TMP/dozen.md"
check "a quantity after more than a is clean"          0 "$TMP/dozen.md"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
