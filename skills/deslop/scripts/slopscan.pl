#!/usr/bin/env perl
# slopscan: protection-aware mechanical slop scan for Markdown and plain text.
#
# Masks everything the preservation contract forbids editing (frontmatter,
# fenced code in every form, indented code, inline code spans, blockquoted
# material, HTML comments, link targets) before any check runs, so a scan
# never reports a hit inside code or inside a quoted example.
#
# Usage:   slopscan.pl [--surface NAME] [--json] [--show-masked] FILE...
#          slopscan.pl --compare ORIGINAL REVISED [--surface NAME] [--json]
# Surface: house (default) | published | agent | sample
#
# Scan mode reports hard findings and candidates per file, then descriptive
# rhythm that never gates: sentence and paragraph spread, semicolons per
# 1,000 words, the longest paragraph, and up to three sentences of 45 or more
# words as places to inspect.
#
# Compare mode reports what an edit did.
#   Hard: a protected region of ORIGINAL (code, blockquote, link target,
#     reference definition, autolink, frontmatter, HTML comment) missing or
#     altered in REVISED, and every hard finding of a normal scan of REVISED.
#   Candidates: a protected region new in REVISED; a number, citation, or
#     bare URL dropped or introduced; a hedge or limiter whose count fell; a
#     certainty word whose count rose; a candidate label whose hit count rose.
#   Size: visible word counts and their ratio, descriptive and never a finding.
# Dropped, missing, and altered items cite ORIGINAL lines; everything else
# cites REVISED lines.
#
# Exit 0 clean, 10 candidates only, 20 hard failures, 30 unreadable input,
# 2 usage error. Both modes take --json for the same report as one object.

use strict;
use warnings;
use Encode qw(decode FB_CROAK);
use IO::Handle ();
use JSON::PP ();

binmode STDOUT, ':encoding(UTF-8)';
binmode STDERR, ':encoding(UTF-8)';

# Modality words for compare mode. "never" sits in both lists on purpose: a
# drop loses a limiter and a rise adds certainty.
my @HEDGE   = qw(may might could likely approximately about estimated roughly
                 not no never only unless);
my @CERTAIN = qw(always never guarantees proves causes definitely certainly);
my $LONG_SENTENCE = 45;

# Inline code spans, including spans that wrap across a soft line break. The
# opening run must not be escaped, the closing run must be exactly the same
# length (a two-tick opener is not closed by a three-tick run), and the span
# may never cross a blank line, because the paragraph ends there. Without
# that stop, one unpaired backtick run in prose pairs with another far away
# and blanks every line between them, which is how the contributor guide's
# own inventory table went invisible on the first dogfood scan.
my $INLINE_CODE = qr/(?<!\\)(?<!`)(`+)(?!`)((?:(?!(?<!`)\1(?!`))(?!\n[ \t]*\n).)*?)(?<!`)\1(?!`)/s;

my $surface     = 'house';
my $json        = 0;
my $show_masked = 0;
my $compare     = 0;
my @files;
while (@ARGV) {
    my $arg = shift @ARGV;
    if    ($arg eq '--surface')     { $surface = shift @ARGV // 'house' }
    elsif ($arg eq '--json')        { $json    = 1 }
    elsif ($arg eq '--show-masked') { $show_masked = 1 }
    elsif ($arg eq '--compare')     { $compare = 1 }
    elsif ($arg =~ /^-/)            { usage_error("unknown flag: $arg\n") }
    else                            { push @files, $arg }
}
my $usage = "usage: slopscan.pl [--surface house|published|agent|sample] [--json] [--show-masked] FILE...\n"
          . "       slopscan.pl --compare ORIGINAL REVISED [--surface NAME] [--json]\n";
usage_error($usage) unless @files;
usage_error($usage) if $compare && @files != 2;
my %VALID = map { $_ => 1 } qw(house published agent sample);
usage_error("unknown surface '$surface' (house|published|agent|sample)\n")
    unless $VALID{$surface};

my $JSON = JSON::PP->new->canonical->indent->indent_length(2)->space_after;

exit run_compare(@files) if $compare;

# Dashes are a house rule rather than evidence of authorship.
# They are hard failures on our own files, house and agent alike, because the
# project contract bans them in anything we write. On someone else's prose
# (published, sample) they are density candidates needing converging signals.
my ($hard_total, $cand_total, $io_errors) = (0, 0, 0);
my @report;

for my $file (@files) {
    my $raw = read_input($file);
    unless (defined $raw) { $io_errors++; next }
    my $prose = mask($raw);

    my ($hard, $cand) = checks($prose, $surface, $raw);

    # Masking is a heuristic, not a CommonMark parser, so run the same checks on
    # the raw text. Anything present there and absent here was suppressed by
    # masking. Legitimate suppressions are dashes inside code and quotes; a
    # masking bug shows up here instead of vanishing, which is the whole point.
    my ($raw_hard, undef) = checks($raw, $surface);
    # Compare on label and line only. Masking changes the snippet text, so a
    # line carrying a tell in both prose and code would otherwise be reported
    # as suppressed even though the prose hit was already caught.
    my %seen = map { /^([^:]+:\d+)/ ? ($1 => 1) : () } @$hard;
    my @suppressed = grep { /^([^:]+:\d+)/ && !$seen{$1} } @$raw_hard;

    my @hard = @$hard;
    my @cand = @$cand;

    # ---- rhythm diagnostics (never gate on these) --------------------------
    my @sent  = sentences($prose);
    my @paras = paragraphs($prose);
    my $srhy  = spread('sentence',  [ map { $_->[0] } @sent ]);
    my $prhy  = spread('paragraph', [ map { $_->[0] } @paras ]);
    my $dens  = density($prose, \@sent, \@paras);

    $hard_total += scalar @hard;
    $cand_total += scalar @cand;

    push @report, { file => $file, hard => \@hard, cand => \@cand,
                    suppressed => \@suppressed,
                    sent => $srhy, para => $prhy, density => $dens };
}

# ---- output ---------------------------------------------------------------
if ($json) {
    print $JSON->encode({
        mode       => 'scan',
        surface    => $surface,
        hard       => 0 + $hard_total,
        candidates => 0 + $cand_total,
        io_errors  => 0 + $io_errors,
        files      => [ map { +{
            file               => $_->{file},
            hard_findings      => $_->{hard},
            candidate_findings => $_->{cand},
            suppressed         => 0 + @{ $_->{suppressed} },
            rhythm             => { sentence  => $_->{sent},
                                    paragraph => $_->{para},
                                    %{ $_->{density} } },
        } } @report ],
    });
} else {
    for my $r (@report) {
        print "\n$r->{file} (surface: $surface)\n";
        if (@{ $r->{hard} }) {
            print "  HARD FAIL\n";
            print "    $_\n" for @{ $r->{hard} };
        }
        if (@{ $r->{cand} }) {
            print "  CANDIDATES (judge, do not auto-fix)\n";
            print "    $_\n" for @{ $r->{cand} };
        }
        if (@{ $r->{suppressed} }) {
            my $n = scalar @{ $r->{suppressed} };
            print "  masking suppressed $n hard hit(s), expected inside code and"
                . " quotes. If any is really prose, the masker is wrong"
                . ($show_masked ? ':' : " (--show-masked to list)") . "\n";
            if ($show_masked) { print "    $_\n" for @{ $r->{suppressed} } }
        }
        print "  rhythm: $r->{sent}\n";
        print "          $r->{para}\n";
        print "          $_\n" for density_lines($r->{density});
        print "  clean\n" if !@{ $r->{hard} } && !@{ $r->{cand} };
    }
    print "\nsurface=$surface hard=$hard_total candidates=$cand_total\n";
}

exit 30 if $io_errors;     # could not read an input: never report clean
exit 20 if $hard_total;
exit 10 if $cand_total;
exit 0;

# A fixed status, because die exits with whatever errno holds and could
# collide with a finding code.
sub usage_error { print STDERR $_[0]; exit 2 }

# Reads, decodes, and normalizes one input. Returns undef after a warning
# when the file cannot be used, so the caller can count it as an I/O error.
sub read_input {
    my ($file) = @_;
    unless (-f $file) {
        warn "not a regular input file: $file\n";
        return undef;
    }
    open my $fh, '<:raw', $file
        or do { warn "cannot read $file: $!\n"; return undef };
    $! = 0;
    my $bytes = do { local $/; <$fh> };
    my $read_error = $fh->error ? ($! ? "$!" : 'input error') : '';
    close $fh or $read_error ||= "$!";
    if ($read_error) {
        warn "cannot read $file: $read_error\n";
        return undef;
    }
    my $raw = eval { decode('UTF-8', $bytes // '', FB_CROAK) };
    if ($@) {
        warn "invalid UTF-8 input: $file\n";
        return undef;
    }
    $raw =~ s/\A\x{FEFF}//;  # a byte-order mark otherwise hides the frontmatter
    $raw =~ s/\r\n?/\n/g;   # normalize CRLF and CR before anything else
    return $raw;
}

# Every content check, so the same set can run against masked and raw text.
# RAW, when given, lets a check see what a masked span next to a hit was.
sub checks {
    my ($prose, $surf, $raw) = @_;
    $raw //= $prose;
    my $dash_hard = ($surf eq 'house' || $surf eq 'agent');
    my (@hard, @cand);


    # ---- character-level checks -------------------------------------------
    push @{ $dash_hard ? \@hard : \@cand },
        hits($prose, qr/[\x{2014}\x{2013}]/,        'em or en dash');
    push @{ $dash_hard ? \@hard : \@cand },
        hits($prose, qr/(?<=[[:alnum:],;:)"'])--(?=[[:alnum:]("'])|(?<=\s)--(?=\s)/, 'double-hyphen dash');
    # Typography outside house surfaces follows the author's or publication's
    # conventions; a glyph can be intentional, including in localized prose.
    push @{ $dash_hard ? \@hard : \@cand },
        hits($prose, qr/[\x{201C}\x{201D}\x{2018}\x{2019}]/, 'curly quote');
    # These variants are flanked-by-letters only, so a prime
    # in "the 5' UTR" or a bare accent stays clean. Grave accent (U+0060) is
    # excluded: it is the inline-code delimiter and the masker owns it.
    push @{ $dash_hard ? \@hard : \@cand },
        hits($prose, qr/(?<=[[:alpha:]])[\x{02BC}\x{00B4}\x{2032}\x{201B}](?=[[:alpha:]])/,
             'apostrophe variant glyph');
    push @{ $dash_hard ? \@hard : \@cand },
        hits($prose, qr/[\x{00A0}\x{2007}\x{202F}]/, 'non-breaking space');
    push @{ $dash_hard ? \@hard : \@cand },
        hits($prose, qr/\x{2026}/, 'ellipsis character');

    # Unresolved provider tokens are hard findings in visible prose. Generic
    # footnote punctuation and brackets also have legitimate uses.
    push @hard, hits($prose, qr/turn\d{1,4}(?:search|news|image)\d{1,4}/, 'chat-export artifact');
    push @hard, hits($prose, qr/\[cite:\s*\d+\]|\[span_\d+\]/, 'citation artifact');
    push @cand, hits($prose, qr/\x{2020}\d/, 'dagger footnote marker');
    push @cand, hits($prose, qr/utm_source=(?:chatgpt|claude)/, 'tracking parameter');
    push @cand, hits($prose, qr/\x{3010}[^\x{3011}]{0,40}\x{3011}/, 'lenticular bracket');

    # ---- candidates: need judgment ----------------------------------------
    # Structural candidates are skipped on the agent surface, where the
    # surface matrix exempts structure (tables, density, bold leads) outright.
    if ($surf ne 'agent') {
        push @cand, hits($prose, qr/^\s*[-*+]\s+\*\*[^*]+:\*\*/m, 'bold-lead bullet');
        push @cand, heading_case($prose);
    }
    push @cand, hits($prose, qr/\bnot\s+(?:just|only|merely|simply)\b[^.!?]{0,60}\b(?:it['\x{2019}]?s|it\s+is|we['\x{2019}]re|they['\x{2019}]re|that['\x{2019}]s|but)\b/i,
                     'negative parallelism');
    push @cand, hits($prose, qr/,\s+(?:highlighting|underscoring|emphasizing|ensuring|reflecting|symbolizing|showcasing|fostering|contributing|cultivating|encompassing|demonstrating|solidifying|cementing|signaling|positioning|paving)\s/i,
                     'participial tail');
    push @cand, hits($prose, qr/\b(?:each|every)\s+\w*\s*a\s+\w+\s+(?:in|of)\s+the\b/i,
                     'distributive appositive');
    push @cand, hits($prose, qr/\b(?:plays?|playing)\s+an?\s+\w+\s+role\s+in\b/i, 'plays-a-role paradigm');
    push @cand, hits($prose, qr/\b(?:extends?|goes?|moves?|reaches?)\s+(?:far\s+)?beyond\s+(?:mere|simple|simply|surface)\b/i,
                     'beyond family');
    push @cand, hits($prose, qr/\b(?:load-bearing|in\s+service\s+of|earns\s+its\s+keep|first-order\s+concern|the\s+binding\s+constraint|asymmetric\s+upside|forcing\s+function)\b/i,
                     'house jargon or borrowed rigor');
    push @cand, hits($prose, qr/\bcheap(?:est|ly)?\b|\bpay(?:s|ing)?\s+rent\b|\bbuys\s+you\b|\bcosts\s+you\s+nothing\b/i,
                     'transactional effort framing');
    push @cand, stacked_frames($prose);
    push @cand, hits($prose, qr/(?:^|[.!?]\s+|^\s*[-*+]\s+)(?:let\s+me\s+be\s+(?:blunt|clear)|here'?s\s+the\s+thing|the\s+thing\s+is|real\s+talk|to\s+be\s+honest)\b|\bworth\s+naming\s+that\b/i,
                     'performed candor');
    push @cand, hits($prose, qr/\b(?:epistemic\s+status|~?\d{1,3}%\s+confident|I\s+hold\s+this\s+loosely)\b/i,
                     'calibration theatre');
    push @cand, hits($prose, qr/\b(?:production-ready|enterprise-grade|battle-tested|built\s+with\s+\w+\s+in\s+mind|designed\s+for\s+scale)\b/i,
                     'unfalsifiable claim');
    push @cand, hits($prose, qr/^\s*(?:The\s+result\?|Why\s+does\s+this\s+matter\?|So\s+what\s+changed\?|The\s+catch\?)/mi,
                     'rhetorical-question transition');
    # Sentence-initial "This matters" is case-sensitive so a wrapped line that
    # merely continues "...because this matters" stays quiet.
    push @cand, hits($prose, qr/\b(?:this|that)\s+(?:distinction|difference|point|detail|nuance)\s+matters\b|\bwhy\s+(?:this|that|it)\s+matters\b|(?-i:(?:^\s*(?:[-*+]\s+|\d+[.)]\s+)?|[.!?]["')]?\s+)This\s+matters\b)/i,
                     'importance flag');
    # "without losing" and "without giving up" usually name a real thing kept,
    # so only the verbs that assert a free lunch are flagged.
    push @cand, hits($prose, qr/\bwithout\s+(?:sacrificing|compromising|trading\s+off)\b/i,
                     'tradeoff denial');
    # Bare "rather than" is ordinary English; only the corrective intensifier
    # and the "more than a X ... it" reframe are flagged. A quantity after
    # "more than a" ("a dozen", "a few", "a 10x") is a count, not a reframe.
    push @cand, hits($prose, qr/\brather\s+than\s+(?:simply|merely|just)\b|\b(?:is|are|['\x{2019}]s|['\x{2019}]re)\s+more\s+than\s+(?:just\s+)?an?\s+(?!(?:dozen|few|couple|handful|hundred|thousand|million|billion)\b|\d)[\w-]+\b[^.!?]*?\b(?:it|they)\b/i,
                     'corrective contrast');
    push @cand, arrows($prose, $raw);

    # Padding phrases, most common in older and open-weight model output and in
    # chat text pasted into a document. Each has legitimate uses, so each is a
    # candidate. Line-initial forms are case-sensitive on purpose.
    push @cand, hits($prose, qr/^\s*(?:Certainly|Absolutely|Of\s+course|Sure\s+thing|Great\s+question)[!,.]|(?i:\bhope\s+this\s+(?:helps|(?:email|message)\s+finds\s+you)\b|\blet\s+me\s+know\s+if\s+you(?:['\x{2019}]d|\s+would)\s+like(?:\s+me)?\s+to\b|\bfeel\s+free\s+to\s+(?:reach\s+out|ask)\b|\bas\s+an\s+AI\b|\bhere(?:['\x{2019}]s|\s+is)\s+an?\s+(?:comprehensive|detailed|quick|brief)\s+(?:overview|breakdown|summary|guide)\b)/m,
                     'chatbot artifact');
    push @cand, hits($prose, qr/\bit(?:['\x{2019}]s|\s+is)\s+(?:important|worth|crucial|essential)\s+to\s+(?:note|mention|remember|understand|recognize)\b|\bit(?:['\x{2019}]s|\s+is)\s+worth\s+(?:noting|mentioning|emphasizing|highlighting)\b|\bin\s+today['\x{2019}]s\s+(?:fast-paced|ever-evolving|digital|modern)\b|\bneedless\s+to\s+say\b/i,
                     'filler phrase');
    push @cand, hits($prose, qr/\ban?\s+(?:true\s+|real\s+)?testament\s+to\b|\bpivotal\s+(?:moment|role|step|point)\b|\bmarks?\s+an?\s+(?:significant|pivotal|major|new)\s+(?:milestone|step|shift|chapter|moment)\b|\bgame(?:-|\s+)chang(?:er|ing)\b|\bthe\s+future\s+(?:of\s+[\w\s]{1,30}\s)?(?:is|looks)\s+bright\b/i,
                     'inflated significance');
    push @cand, hits($prose, qr/\bdelv(?:e|es|ed|ing)\b|\btapestry\b|\b(?:ever-evolving|ever-changing|fast-paced)\s+(?:\w+\s+)?(?:landscape|world)\b|\bin\s+the\s+realm\s+of\b|\bnavigat(?:e|es|ing)\s+the\s+complexit(?:y|ies)\b/i,
                     'stock vocabulary');
    push @cand, hits($prose, qr/^\s*(?:In\s+conclusion|To\s+sum\s+up|All\s+in\s+all),/m,
                     'generic close');

    return (\@hard, \@cand);
}

# ---- helpers --------------------------------------------------------------

# Replace every protected region with same-length blanks so line and column
# numbers survive. A line-oriented state machine rather than multiline regexes,
# because regex fence matching leaked in both directions: a closer at a
# different indent masked the rest of the file, and code content that looked
# like a closer reopened the scan inside code.
#
# Protected: YAML frontmatter, fenced code (either fence character, any length
# from three up, zero to three spaces of indent, closer tail whitespace-only),
# indented code blocks, blockquotes including lazy continuation, inline code
# spans including multiline ones, and link, reference, and autolink targets.
#
# With REGIONS, every masked region is also recorded, in document order, as
# { kind, line, text } with its original text. Bare URLs are recorded with
# kind 'url' because they are prose content rather than markup.
sub mask {
    my ($t, $regions) = @_;
    my @lines = split /\n/, $t, -1;
    my @orig  = @lines;

    # Block regions: a new region opens when asked, or when the previous
    # recorded line belongs to a different kind or is not adjacent. BASE is
    # the column where a code block's payload starts, so normalization can
    # strip layout indentation and nothing else.
    my ($cur, $cur_kind, $cur_last) = (undef, '', -2);
    my $rec = sub {
        my ($kind, $i, $new, $base) = @_;
        return unless $regions;
        if ($new || !defined $cur || $cur_kind ne $kind || $cur_last != $i - 1) {
            push @$regions, { kind => $kind, line => $i + 1, text => $orig[$i],
                              base => $base // 0 };
            $cur = $regions->[-1];
        } else {
            $cur->{text} .= "\n" . $orig[$i];
        }
        ($cur_kind, $cur_last) = ($kind, $i);
    };

    my $in_front = (@lines && $lines[0] eq '---') ? 1 : 0;
    my ($fence_char, $fence_len, $fence_base, $in_quote, $in_code, $code_base, $prev_blank)
        = ('', 0, 0, 0, 0, 0, 1);
    # Content columns of the open list items, innermost last. Indentation is
    # measured from the innermost item's content, so a nested bullet indented
    # four spaces is list content, and only four or more columns past the
    # content is indented code.
    my @lists;

    for my $i (0 .. $#lines) {
        my $line  = $lines[$i];
        my $blank = ($line =~ /^\s*$/) ? 1 : 0;
        my $ex    = expand_lead($line);
        my $ind   = length(($ex =~ /^( *)/)[0]);

        if ($in_front) {
            my $end = ($i > 0 && $line =~ /^(?:---|\.\.\.)\s*$/);
            $lines[$i] = blank($line);
            $rec->('frontmatter', $i, $i == 0);
            $in_front = 0 if $end;
            $prev_blank = $blank;
            next;
        }

        if ($fence_len) {
            # A line indented less than the list item holding the fence ends the
            # item and the fence with it. Otherwise the closer uses the same
            # character, is at least as long, sits at most three columns past
            # the item's content, and has a whitespace-only tail.
            if (!$blank && $ind < $fence_base) {
                $fence_len = 0;
            } else {
                my $close = '^ *' . quotemeta($fence_char) . '{' . $fence_len . ',}\s*$';
                $fence_len = 0 if $ind - $fence_base <= 3 && $ex =~ /$close/;
                $lines[$i] = blank($line);
                $rec->('fenced code', $i, 0);
                $prev_blank = $blank;
                next;
            }
        }

        # After a blank line, or at a line that starts a new block, a line
        # indented less than an item's content closes that item. Any other
        # less-indented line is a lazy paragraph continuation and closes nothing.
        if (!$blank && ($prev_blank
                        || $ex =~ /^ *(?:#{1,6}(?:\s|$)|`{3,}|~{3,}|>|[-*+](?:\s|$)|\d{1,9}[.)](?:\s|$))/)) {
            pop @lists while @lists && $lists[-1] > $ind;
        }
        my $base = @lists ? $lists[-1] : 0;
        my $rel  = $ind - $base;

        # fence opener. For backtick fences the info string cannot contain a
        # backtick, which is what keeps a prose line of code ticks from opening
        # a fence. A fence also ends any lazy blockquote continuation.
        if ($rel >= 0 && $rel <= 3
            && ($ex =~ /^ *(`{3,})([^`]*)$/ || $ex =~ /^ *(~{3,})(.*)$/)) {
            $in_quote   = 0;
            $fence_char = substr($1, 0, 1);
            $fence_len  = length $1;
            $fence_base = $base;
            $lines[$i]  = blank($line);
            $rec->('fenced code', $i, 1, $ind);
            $prev_blank = 0;
            next;
        }

        # blockquote, including lazy continuation. A lazy continuation ends at a
        # blank line or at any line that starts a new block, because an ATX
        # heading, fence, list, or thematic break interrupts a paragraph.
        if ($rel >= 0 && $rel <= 3 && $ex =~ /^ *>/) { $in_quote = 1 }
        elsif ($blank
               || $line =~ /^ {0,3}(?:\#{1,6}\s|[-*+]\s|\d+[.)]\s|(?:-\s*){3,}$|(?:_\s*){3,}$|(?:\*\s*){3,}$)/
               || $line =~ m{^ {0,3}</?(?:script|pre|style|textarea|div|table|p|ul|ol|li|h[1-6]|blockquote|section|article|!--)}i) {
            $in_quote = 0;
        }
        if ($in_quote) {
            $lines[$i] = blank($line);
            $rec->('blockquote', $i, 0);
            $prev_blank = $blank;
            next;
        }

        # indented code block: opens four or more columns past the current
        # content column after a blank line, and continues across further
        # lines indented that far and across blank lines.
        if ($in_code) {
            if ($blank || $ind >= $code_base) {
                $lines[$i] = blank($line);
                $rec->('indented code', $i, 0);
                $prev_blank = $blank;
                next;
            }
            $in_code = 0;
        }
        if (!$blank && $prev_blank && $rel >= 4) {
            $in_code    = 1;
            $code_base  = $base + 4;
            $lines[$i]  = blank($line);
            $rec->('indented code', $i, 1, $code_base);
            $prev_blank = 0;
            next;
        }

        # list item: its content column is the marker plus one to four spaces;
        # an empty item or a wider gap puts the content one column past the
        # marker.
        if (!$blank && $rel >= 0 && $rel <= 3 && $ex !~ /^ *(?:[-*_] *){3,}$/
            && $ex =~ /^( *)([-*+]|\d{1,9}[.)])(?:( +)\S|\s*$)/) {
            my ($m, $w, $n) = (length $1, length $2, defined $3 ? length $3 : 0);
            pop @lists while @lists && $lists[-1] > $m;
            push @lists, $m + $w + (($n >= 1 && $n <= 4) ? $n : 1);
        }

        $prev_blank = $blank;
    }

    my $out = join "\n", @lines;

    # Link and image markup: angle-bracket destination, bare destination with
    # balanced parentheses, optional title in any of the three quote forms,
    # reference definitions, and autolinks. The whole destination-and-title run
    # is markup rather than prose, so it is masked as one unit.
    my $title = qr/(?:\s+(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\((?:[^)\\]|\\.)*\)))?/;
    my $bare  = qr/(?:[^()\s\\]|\\.|\((?:[^()\\]|\\.|\((?:[^()]|\\.)*\))*\))+/;
    my $label = qr/(?<!\\)\[(?:[^\[\]\\]|\\.|\[[^\]]*\])*(?<!\\)\]/;

    # Inline passes run in order, each over the output of the one before, so a
    # link inside a code span is never seen as a link. A pass flagged as a
    # tail masks from the closing bracket onward and leaves the label visible.
    my @passes = (
        [ 'inline code', 0, $INLINE_CODE ],
        [ 'link target', 1, qr/$label\(\s*<[^>\n]*>$title\s*\)/ ],
        [ 'link target', 1, qr/$label\(\s*$bare$title\s*\)/ ],
        # reference definitions, but never a footnote definition, whose body is prose
        [ 'reference definition', 0, qr/^ {0,3}\[(?!\^)[^\]]+\]:\s*(?:<[^>\n]*>|\S+)$title/m ],
        [ 'autolink', 0, qr/<(?:https?|ftp|mailto):[^>\s]*>/ ],
        # HTML comments never reach a reader, and a bare URL is not prose. A
        # URL may hold balanced parentheses, as in a_(one); an unbalanced
        # closing parenthesis belongs to the surrounding sentence.
        [ 'HTML comment', 0, qr/<!--.*?-->/s ],
        [ 'url', 0, qr{(?<![\w/])(?:https?|ftp)://(?:[^\s<>()\[\]"']|\([^\s<>()\[\]"']*\))+} ],
    );
    for my $pass (@passes) {
        my ($kind, $tail, $re) = @$pass;
        my @m;
        push @m, [ $-[0], $+[0] ] while $out =~ /$re/g;
        my ($pos, $lineno) = (0, 1);
        for my $m (@m) {
            my ($s, $e) = @$m;
            my $text = substr($out, $s, $e - $s);
            my $cut  = $tail ? rindex($text, '](') : -1;
            my $from = $cut < 0 ? 0 : $cut;
            substr($out, $s + $from, $e - $s - $from) = blank(substr($text, $from));
            next unless $regions;
            $lineno += (substr($out, $pos, $s - $pos) =~ tr/\n//);
            $pos = $s;
            push @$regions, { kind => $kind, line => $lineno,
                              col  => $s - (rindex($out, "\n", $s - 1) + 1),
                              text => $cut < 0 ? $text : substr($text, $cut + 1) };
        }
    }
    @$regions = sort { $a->{line} <=> $b->{line} || ($a->{col} // -1) <=> ($b->{col} // -1) }
                @$regions if $regions;

    return $out;
}

sub blank { my ($s) = @_; $s =~ s/[^\n]/ /g; return $s }

# The line with tabs in its first 80 characters expanded to stops of four,
# for measuring indentation. Structure never sits further right than that.
sub expand_lead {
    my ($line) = @_;
    return $line unless $line =~ /\t/;
    my $head = substr($line, 0, 80);
    1 while $head =~ s/^([^\t]*)\t/$1 . (' ' x (4 - length($1) % 4))/e;
    return $head . (length($line) > 80 ? substr($line, 80) : '');
}

# Removes up to N columns of leading whitespace, counting a tab to the next
# stop of four, and keeps any columns of a split tab as spaces.
sub strip_cols {
    my ($line, $n) = @_;
    my ($col, $k) = (0, 0);
    while ($k < length($line) && $col < $n) {
        my $c = substr($line, $k, 1);
        if ($c eq ' ') {
            $col++;
        } elsif ($c eq "\t") {
            my $w = 4 - $col % 4;
            return (' ' x ($col + $w - $n)) . substr($line, $k + 1) if $col + $w > $n;
            $col += $w;
        } else {
            last;
        }
        $k++;
    }
    return substr($line, $k);
}

# Two lines join across a soft wrap when both carry text and the second does
# not start a new block, so a phrase or citation split by the wrap still reads
# as one.
sub soft_break {
    my ($lines, $i) = @_;
    return 0 if $i >= $#$lines;
    my ($cur, $nxt) = ($lines->[$i], $lines->[$i + 1]);
    return 0 unless $cur =~ /\S/ && $nxt =~ /\S/;
    return 0 if $cur =~ /^\s*[#|]/;
    return 0 if $nxt =~ /^\s*(?:[-*+]\s|\d+[.)]\s|[#|>]|(?:[-*_=]\s*){3,}$)/;
    return 1;
}

# Title case is a style choice rather than a tell; the tell is a file that
# mixes heading cases, which is how an inserted section betrays a second
# author. Flag the minority style only, and stay silent on a consistent
# file. A proper noun can still put a heading on the wrong side of the
# classifier, which is why the result is a candidate.
sub heading_case {
    my ($text) = @_;
    my (@title, @sent);
    my @lines = split /\n/, $text, -1;
    for my $i (0 .. $#lines) {
        my $body;
        if ($lines[$i] =~ /^ {0,3}#{1,6}\s+(\S.*?)\s*$/) {
            $body = $1;
            $body =~ s/\s+#+$//;
        }
        # setext: a text line underlined by = or -, which CommonMark reads as
        # a heading even when the author meant a thematic break
        elsif ($i < $#lines
               && $lines[$i]     =~ /^ {0,3}\S/
               && $lines[$i]     !~ /^ {0,3}(?:#|>|\||[-*+]\s|\d+[.)]\s|(?:=+|-+)\s*$)/
               && $lines[$i + 1] =~ /^ {0,3}(?:=+|-+)\s*$/) {
            ($body = $lines[$i]) =~ s/^\s+|\s+$//g;
        }
        next unless defined $body;
        my @words = grep { /[[:alpha:]]/ } split ' ', $body;
        next if @words < 2;
        my $caps = grep { /^[^[:alpha:]]*[[:upper:]]/ } @words;
        if ($caps == @words || $body =~ /[a-z] [A-Z][a-z]/) {
            push @title, [$i + 1, $body];
        } else {
            push @sent, [$i + 1, $body];
        }
    }
    return () unless @title && @sent;
    # On an equal split there is no majority to deviate from, so say so
    # instead of inventing one; the title-case half is still the likelier
    # insertion, so those are the lines reported.
    my ($minor, $label) =
        (@title == @sent) ? (\@title, 'mixed heading case, no majority')
      : (@title <  @sent) ? (\@title, 'title-case heading in a sentence-case file')
      :                     (\@sent,  'sentence-case heading in a title-case file');
    return map { sprintf('%s:%d  %s', $label, $_->[0], substr($_->[1], 0, 90)) }
               @$minor;
}

# Prose blocks shared by the frame and rhythm checks: paragraphs split at
# blank lines, with each list item its own block so separate bullets cannot
# pool. Heading, table, and thematic-break lines end a block and are dropped;
# list markers are stripped. Returns [first_line, text] pairs.
sub blocks {
    my ($text) = @_;
    my (@out, @buf, $start);
    my $flush = sub { push @out, [ $start, join("\n", @buf) ] if @buf; @buf = () };
    my @lines = split /\n/, $text, -1;
    for my $i (0 .. $#lines) {
        my $line = $lines[$i];
        if ($line =~ /^\s*$/ || $line =~ /^\s*[|#]/ || $line =~ /^\s*(?:[-*_=]\s*){3,}$/) {
            $flush->();
            next;
        }
        $flush->() if $line =~ s/^\s*(?:[-*+]|\d+[.)])\s+//;
        $start = $i + 1 unless @buf;
        push @buf, $line;
    }
    $flush->();
    return @out;
}

# Stacked rhetorical frames (catalog N19). Three distinct families generate a
# candidate, not a quality judgment or model fingerprint.
sub stacked_frames {
    my ($text) = @_;
    my @fams = (
        [ contrast    => qr/\brather than\b|\binstead of\b/i ],
        [ reframe     => qr/,\s+which\s+(?:is|means|makes)\b/i ],
        [ consequence => qr/,\s+so\s+[a-z]/ ],
        [ closer      => qr/\b(?:is|was)\s+the\s+(?:whole|entire|real|actual|only)\b/i ],
        [ negation    => qr/,\s+not\s+(?:a|an|the)?\s*[a-z]/ ],
    );
    my @out;
    for my $blk (blocks($text)) {
        my ($start, $para) = @$blk;
        my @hit = grep { $para =~ $_->[1] } @fams;
        push @out, sprintf('stacked frames (%s):%d',
                           join('+', map { $_->[0] } @hit), $start)
            if @hit >= 3;
    }
    return @out;
}

# Shorthand arrows joining prose words. The neighbors are read from the raw
# line, where a masked code span is still code rather than blank space, so a
# receipt such as `make check` -> passes stays quiet. Table rows are skipped.
sub arrows {
    my ($prose, $raw) = @_;
    my @p = split /\n/, $prose, -1;
    my @r = split /\n/, $raw,   -1;
    my @out;
    for my $i (0 .. $#p) {
        my $line = $p[$i];
        next if $line =~ /^\s*\|/ || ($line =~ tr/|//) >= 2;
        my $src = $r[$i] // $line;
        while ($line =~ /->|=>|[\x{2192}\x{21D2}\x{27F6}]/g) {
            my ($s, $e) = ($-[0], $+[0]);
            next unless substr($src, 0, $s) =~ /[[:alpha:])][ \t]*\z/
                     && substr($src, $e)    =~ /\A[ \t]*[[:alpha:]]/;
            push @out, snippet('shorthand arrow', $i, $line);
            last;
        }
    }
    return @out;
}

sub hits {
    my ($text, $re, $label) = @_;
    my @out;
    my @lines = split /\n/, $text, -1;
    for my $i (0 .. $#lines) {
        # table delimiter rows and horizontal rules carry no prose
        next if $lines[$i] =~ /^\s*\|?[\s:|+-]{3,}\|?\s*$/;
        # A match may run on into the next line of the same paragraph, so a
        # phrase split by a soft wrap still fires, but it must start on this
        # line. The leftmost match decides, so a later start cannot hide one.
        my $win = $lines[$i];
        $win .= "\n" . $lines[$i + 1] if soft_break(\@lines, $i);
        next unless $win =~ $re && $-[0] < length $lines[$i];
        push @out, snippet($label, $i, $lines[$i]);
    }
    return @out;
}

sub snippet {
    my ($label, $i, $line) = @_;
    $line =~ s/^\s+|\s+$//g;
    $line = substr($line, 0, 90) . '...' if length($line) > 90;
    return sprintf('%s:%d  %s', $label, $i + 1, $line);
}

# Sentences as [word_count, line]. Splits only on a terminator followed by
# whitespace and an opening character, so v1.2.3, e.g., Node.js, and file
# paths stay inside one sentence. A sentence never crosses a block boundary,
# so a run of unpunctuated bullets does not read as one long sentence.
sub sentences {
    my ($t) = @_;
    my @out;
    for my $blk (blocks($t)) {
        my ($line, $text) = @$blk;
        my @parts = split /((?<=[.!?])\s+(?=["(\x{2018}\x{201C}]?[A-Z]|\z))/, $text;
        while (@parts) {
            my $s   = shift @parts;
            my $sep = shift @parts // '';
            my @w = grep { length } split /\s+/, $s;
            # a sentence's line is where its first word sits
            my ($lead) = $s =~ /\A(\s*)/;
            push @out, [ scalar @w, $line + ($lead =~ tr/\n//) ] if @w > 1;
            $line += ($s =~ tr/\n//) + ($sep =~ tr/\n//);
        }
    }
    return @out;
}

# Paragraphs as [word_count, first_line], over the same blocks.
sub paragraphs {
    my ($t) = @_;
    my @out;
    for my $blk (blocks($t)) {
        my @w = grep { length } split /\s+/, $blk->[1];
        push @out, [ scalar @w, $blk->[0] ] if @w > 3;
    }
    return @out;
}

# Density: semicolons per 1,000 words, the longest paragraph, and the longest
# sentences at or over the threshold. Descriptive only; a dense paragraph can
# be exactly right for its reader.
sub density {
    my ($prose, $sent, $paras) = @_;
    my ($words, $semis) = (0, 0);
    for my $blk (blocks($prose)) {
        $words += () = $blk->[1] =~ /\S+/g;
        $semis += () = $blk->[1] =~ /;/g;
    }
    my @long = sort { $b->[0] <=> $a->[0] || $a->[1] <=> $b->[1] }
               grep { $_->[0] >= $LONG_SENTENCE } @$sent;
    my ($top) = sort { $b->[0] <=> $a->[0] || $a->[1] <=> $b->[1] } @$paras;
    my @shown = @long > 3 ? @long[0 .. 2] : @long;
    return {
        words                     => 0 + $words,
        semicolons_per_1000_words => $words ? 0 + sprintf('%.1f', 1000 * $semis / $words) : 0,
        long_sentence_threshold   => 0 + $LONG_SENTENCE,
        long_sentence_count       => 0 + @long,
        long_sentences            => [ map { +{ line => 0 + $_->[1], words => 0 + $_->[0] } } @shown ],
        longest_paragraph         => $top ? { line => 0 + $top->[1], words => 0 + $top->[0] } : undef,
    };
}

sub density_lines {
    my ($d) = @_;
    return ('density: too few words to measure') unless $d->{words};
    my @out = (sprintf('density: %.1f semicolons per 1,000 words, longest paragraph %s',
                       $d->{semicolons_per_1000_words},
                       $d->{longest_paragraph}
                           ? sprintf('%d words (line %d)', @{ $d->{longest_paragraph} }{qw(words line)})
                           : 'n/a'));
    if (@{ $d->{long_sentences} }) {
        my $list = join ', ', map { sprintf('line %d (%d words)', $_->{line}, $_->{words}) }
                                  @{ $d->{long_sentences} };
        $list .= sprintf('; %d in all', $d->{long_sentence_count})
            if $d->{long_sentence_count} > @{ $d->{long_sentences} };
        push @out, "long sentences to inspect ($d->{long_sentence_threshold}+ words): $list";
    }
    return @out;
}

sub stats {
    my ($vals) = @_;
    return (0, 0) unless @$vals;
    my $m = 0; $m += $_ for @$vals; $m /= @$vals;
    my $v = 0; $v += ($_ - $m) ** 2 for @$vals; $v /= @$vals;
    return ($m, sqrt $v);
}

# Coefficient of variation is scale-free, so it compares across documents.
# Report it; never gate on it. Short crisp technical prose legitimately
# scores low, and the thresholds circulating for this metric are unvalidated.
sub spread {
    my ($kind, $vals) = @_;
    return "$kind spread: too few to measure" if @$vals < 4;
    my ($m, $sd) = stats($vals);
    my $cv = $m ? $sd / $m : 0;
    my @s = sort { $a <=> $b } @$vals;
    return sprintf('%s spread: n=%d min=%d median=%d max=%d mean=%.1f cv=%.2f',
                   $kind, scalar @s, $s[0], $s[int(@s / 2)], $s[-1], $m, $cv);
}

# ---- compare mode -----------------------------------------------------------

sub run_compare {
    my ($ofile, $rfile) = @_;
    my $oraw = read_input($ofile);
    my $rraw = read_input($rfile);
    my $io = (defined $oraw ? 0 : 1) + (defined $rraw ? 0 : 1);
    my (@hard, @cand, %size);

    if (!$io) {
        my (@oreg, @rreg);
        my $oprose = mask($oraw, \@oreg);
        my $rprose = mask($rraw, \@rreg);

        my ($ph, $pc) = compare_regions([ grep { $_->{kind} ne 'url' } @oreg ],
                                        [ grep { $_->{kind} ne 'url' } @rreg ]);
        push @hard, @$ph;
        push @cand, @$pc;

        my ($rhard, $rcand) = checks($rprose, $surface, $rraw);
        my (undef,  $ocand) = checks($oprose, $surface, $oraw);
        push @hard, map { "revised: $_" } @$rhard;

        my $oinv = inventory($oprose, \@oreg);
        my $rinv = inventory($rprose, \@rreg);
        for my $kind (qw(number citation url)) {
            push @cand, inventory_diff($kind, $oinv->{$kind}, $rinv->{$kind});
        }
        push @cand, modality_diff(modality($oprose), modality($rprose));
        push @cand, introduced($ocand, $rcand);

        my ($ow, $rw) = (visible_words($oprose), visible_words($rprose));
        %size = (original_words => 0 + $ow, revised_words => 0 + $rw,
                 ratio => $ow ? 0 + sprintf('%.2f', $rw / $ow) : undef);
    }

    if ($json) {
        print $JSON->encode({
            mode               => 'compare',
            surface            => $surface,
            original           => $ofile,
            revised            => $rfile,
            hard               => 0 + @hard,
            candidates         => 0 + @cand,
            io_errors          => 0 + $io,
            hard_findings      => \@hard,
            candidate_findings => \@cand,
            size               => %size ? \%size : undef,
        });
    } else {
        print "\ncompare $ofile to $rfile (surface: $surface)\n";
        if (@hard) {
            print "  HARD FAIL\n";
            print "    $_\n" for @hard;
        }
        if (@cand) {
            print "  CANDIDATES (judge, do not auto-fix)\n";
            print "    $_\n" for @cand;
        }
        if (%size) {
            printf "  size: %d words to %d words, ratio %s (descriptive only)\n",
                $size{original_words}, $size{revised_words},
                defined $size{ratio} ? sprintf('%.2f', $size{ratio}) : 'n/a';
            print "  clean\n" if !@hard && !@cand;
        }
        printf "\nsurface=%s hard=%d candidates=%d\n", $surface, scalar @hard, scalar @cand;
    }

    return 30 if $io;
    return 20 if @hard;
    return 10 if @cand;
    return 0;
}

# Normalized comparison text for a protected region. Only Markdown layout is
# normalized; code payload compares exactly, whitespace included. Code drops
# the indentation that places it in a list item or fence (its base column),
# a fence line drops its outer whitespace, and indented code drops trailing
# blank lines, so a block moved into or out of a list still matches. Inline
# code tolerates a soft wrap. A quote is parsed so its prose tolerates
# reflowing while any code inside it stays exact. Frontmatter is exact.
sub region_norm {
    my ($r) = @_;
    my ($kind, $t) = ($r->{kind}, $r->{text});
    return $t if $kind eq 'frontmatter';
    if ($kind eq 'fenced code' || $kind eq 'indented code') {
        my @l = map { strip_cols($_, $r->{base} // 0) } split /\n/, $t, -1;
        if ($kind eq 'fenced code') {
            $l[0]  =~ s/^\s+|\s+\z//g;
            $l[-1] =~ s/^\s+|\s+\z//g if @l > 1 && $l[-1] =~ /^\s*(?:`{3,}|~{3,})\s*\z/;
        } else {
            pop @l while @l && $l[-1] =~ /^\s*\z/;
        }
        return join "\n", @l;
    }
    if ($kind eq 'inline code') {
        $t =~ s/[ \t]*\n[ \t]*/ /g;
        return $t;
    }
    return quote_norm($t) if $kind eq 'blockquote';
    $t =~ s/\s+/ /g;
    $t =~ s/^ | $//g;
    return $t;
}

# One quote level comes off each line (the marker and one optional space),
# and the inner text is masked like a document. Code and nested quotes inside
# it normalize as regions of their own; each prose paragraph collapses its
# whitespace outside inline code. Paragraph breaks stay significant.
sub quote_norm {
    my ($t) = @_;
    # the leading empty line keeps an inner "---" from reading as frontmatter
    my $inner = join "\n", '', map { my $x = $_; $x =~ s/^ {0,3}> ?//; $x } split /\n/, $t, -1;
    my @reg;
    mask($inner, \@reg);
    my @lines = split /\n/, $inner, -1;
    my %owner;
    for my $r (grep { $_->{kind} =~ /^(?:fenced code|indented code|blockquote)\z/ } @reg) {
        my $n = ($r->{text} =~ tr/\n//) + 1;
        $owner{ $r->{line} - 1 + $_ } = $r for 0 .. $n - 1;
    }
    my (@out, @para, %done);
    my $flush = sub { push @out, prose_norm(join "\n", @para) if @para; @para = () };
    for my $k (0 .. $#lines) {
        if (my $r = $owner{$k}) {
            $flush->();
            push @out, "[$r->{kind}]\n" . region_norm($r) unless $done{$r}++;
        } elsif ($lines[$k] =~ /^\s*\z/) {
            $flush->();
        } else {
            push @para, $lines[$k];
        }
    }
    $flush->();
    return join "\n", @out;
}

sub prose_norm {
    my ($p) = @_;
    my ($out, $last) = ('', 0);
    while ($p =~ /$INLINE_CODE/g) {
        my ($s, $e) = ($-[0], $+[0]);
        (my $gap  = substr($p, $last, $s - $last)) =~ s/\s+/ /g;
        (my $span = substr($p, $s, $e - $s))       =~ s/[ \t]*\n[ \t]*/ /g;
        $out .= $gap . $span;
        $last = $e;
    }
    (my $rest = substr($p, $last)) =~ s/\s+/ /g;
    $out .= $rest;
    $out =~ s/^ | $//g;
    return $out;
}

sub region_show {
    my ($text, $max) = @_;
    my $s = join ' / ', grep { length } map { my $x = $_; $x =~ s/^\s+|\s+$//g; $x } split /\n/, $text;
    $s = substr($s, 0, $max) . '...' if length($s) > $max;
    return $s;
}

# Exact matches first, as multisets, so a moved region is still preserved.
# A leftover original pairs with a leftover revised region of the same kind
# only when both sit after the same number of matched regions; that pair is
# reported as altered, and every other leftover as missing or new.
sub compare_regions {
    my ($o, $r) = @_;
    my (@hard, @cand);
    my %pool;
    for my $j (0 .. $#$r) {
        $r->[$j]{key} = $r->[$j]{kind} . "\0" . region_norm($r->[$j]);
        push @{ $pool{ $r->[$j]{key} } }, $j;
    }
    my (%omatch, %rmatch);
    for my $i (0 .. $#$o) {
        $o->[$i]{key} = $o->[$i]{kind} . "\0" . region_norm($o->[$i]);
        my $q = $pool{ $o->[$i]{key} };
        next unless $q && @$q;
        $omatch{$i} = 1;
        $rmatch{ shift @$q } = 1;
    }
    my $anchor = sub {
        my ($list, $matched) = @_;
        my ($n, @at) = (0);
        for my $k (0 .. $#$list) { push @at, $n; $n++ if $matched->{$k} }
        return @at;
    };
    my @oa = $anchor->($o, \%omatch);
    my @ra = $anchor->($r, \%rmatch);
    my %taken;
    for my $i (grep { !$omatch{$_} } 0 .. $#$o) {
        my $or = $o->[$i];
        my ($j) = grep { !$rmatch{$_} && !$taken{$_}
                         && $r->[$_]{kind} eq $or->{kind} && $ra[$_] == $oa[$i] } 0 .. $#$r;
        if (defined $j) {
            $taken{$j} = 1;
            my ($was, $now) = first_difference(region_norm($or), region_norm($r->[$j]));
            my ($ws, $ns) = (region_show($was, 50), region_show($now, 50));
            my $q = $or->{kind} eq 'inline code' ? '' : '"';
            push @hard, sprintf('protected %s altered: %s%s%s now %s%s%s%s (original line %d, revised line %d)',
                                $or->{kind}, $q, $ws, $q, $q, $ns, $q,
                                ($ws eq $ns ? ', whitespace differs' : ''),
                                $or->{line}, $r->[$j]{line});
        } else {
            push @hard, sprintf('protected %s missing: %s (original line %d)',
                                $or->{kind}, region_show($or->{text}, 70), $or->{line});
        }
    }
    for my $j (grep { !$rmatch{$_} && !$taken{$_} } 0 .. $#$r) {
        push @cand, sprintf('protected %s new: %s (revised line %d)',
                            $r->[$j]{kind}, region_show($r->[$j]{text}, 70), $r->[$j]{line});
    }
    return (\@hard, \@cand);
}

sub first_difference {
    my ($x, $y) = @_;
    my @x = split /\n/, $x, -1;
    my @y = split /\n/, $y, -1;
    for my $k (0 .. ($#x > $#y ? $#x : $#y)) {
        my ($p, $q) = ($x[$k] // '(nothing)', $y[$k] // '(nothing)');
        return ($p, $q) if $p ne $q;
    }
    return ($x, $y);
}

# Tracked tokens in visible prose: numbers, citation-like tokens, and bare
# URLs, each as key => { n, show, lines }. Citations are blanked before the
# number pass so a year or reference numeral is not counted twice.
sub inventory {
    my ($prose, $regions) = @_;
    my %inv = (number => {}, citation => {}, url => {});
    my $add = sub {
        my ($kind, $key, $show, $line) = @_;
        my $e = $inv{$kind}{$key} //= { n => 0, show => $show, lines => [] };
        $e->{n}++;
        push @{ $e->{lines} }, $line;
    };
    for my $r (grep { $_->{kind} eq 'url' } @$regions) {
        (my $u = $r->{text}) =~ s/[.,;:!?]+\z//;
        $add->('url', $u, $u, $r->{line});
    }

    my $name = qr/[[:upper:]][\p{L}'\x{2019}-]+/;
    my $year = qr/(?:1[89]|20)\d{2}[a-z]?/;
    # The parenthesized form runs before "et al." so "(Smith et al. 2024)"
    # is taken whole rather than leaving its opening parenthesis behind.
    my @cite = (
        qr/\[\^[^\]\s]+\]/,
        qr/\[\d+(?:\s*[,\x{2013}-]\s*\d+)*\]/,
        qr/\((?:see\s+)?$name(?:\s+(?:and|&)\s+$name|\s+et\s+al\.?)?,?\s+$year\)/,
        qr/\b$name\s+et\s+al\.?,?\s+\(?$year\)?/,
        qr/\b$name(?:\s+(?:and|&)\s+$name)?\s+\($year\)/,
        qr/\barXiv:\s?\d{4}\.\d{4,5}(?:v\d+)?/i,
        qr/\b(?:doi:\s?)?10\.\d{4,9}\/[^\s"<>]+/i,
    );
    my %stop = map { $_ => 1 } qw(a an and are as at be by for from in is it
                                  of on or per than that the to was were with);

    # One string with every soft wrap turned into a space, so a citation or
    # number split by a reflow reads the same as before it. Every edit keeps
    # length, so an offset still maps back to its original line.
    my @lines = split /\n/, $prose, -1;
    my @join  = map { soft_break(\@lines, $_) } 0 .. $#lines;
    for (@lines) {
        $_ = blank($_) if /^\s*\|?[\s:|+-]{3,}\|?\s*$/;          # table delimiter row
        s/^(\s*)(\d+[.)])(?=\s)/$1 . (' ' x length $2)/e;      # ordered list marker
    }
    my ($flat, @starts) = ('');
    for my $i (0 .. $#lines) {
        push @starts, length $flat;
        $flat .= $lines[$i] . ($i < $#lines ? ($join[$i] ? ' ' : "\n") : '');
    }
    my $line_of = sub {
        my ($off) = @_;
        my ($lo, $hi) = (0, $#starts);
        while ($lo < $hi) {
            my $mid = int(($lo + $hi + 1) / 2);
            if ($starts[$mid] <= $off) { $lo = $mid } else { $hi = $mid - 1 }
        }
        return $lo + 1;
    };

    for my $re (@cite) {
        $flat =~ s{$re}{
            my $m   = $&;
            my $off = $-[0];
            my $key = lc $m;
            if ($key =~ /^(?:\[|arxiv|doi|10\.)/) {
                $key =~ s/[.,;:)\]]+\z// if $key =~ /^(?:doi|10\.)/;
                $key =~ s/^doi://;
                $key =~ s/\s+//g;
            } else {
                $key =~ s/^\(?see\s+//;
                $key =~ tr/(),.;//d;
                $key =~ s/\s+/ /g;
            }
            $add->('citation', $key, $m, $line_of->($off));
            ' ' x length $m;
        }ge;
    }
    # A sign counts only where it is a sign: at the start, after whitespace,
    # or after an opening bracket. Digits after a letter, dot, slash, or a
    # hyphen that is not a sign belong to an identifier, path, or range.
    while ($flat =~ /(?:(?<![^\s(\[{])([-+\x{2212}])(?=v?\d))?(?(1)|(?<![\w.\/\\-]))(v?)(\d+(?:[.,:\/\x{2013}-]\d+)*)(%?)(?:([ \t]?)([[:alpha:]]+))?/g) {
        my ($sign, $v, $num, $pct, $gap, $unit) = ($1 // '', $2, $3, $4, $5 // '', $6);
        my $key = $num;
        $key =~ tr/\x{2013}/-/;
        $key =~ tr/,//d if $key =~ /^\d{1,3}(?:,\d{3})+(?:\.\d+)?$/;
        (my $s = $sign) =~ tr/\x{2212}/-/;
        $key = $s . $key;
        $key .= '%' if $pct || (defined $unit && lc $unit eq 'percent');
        my $show = "$sign$v$num$pct";
        $show .= "$gap$unit" if defined $unit && !$stop{ lc $unit };
        $add->('number', $key, $show, $line_of->($-[0]));
    }
    return \%inv;
}

sub inventory_diff {
    my ($kind, $o, $r) = @_;
    my @out;
    for my $k (sort { $o->{$a}{lines}[0] <=> $o->{$b}{lines}[0] || $a cmp $b } keys %$o) {
        my ($n0, $n1) = ($o->{$k}{n}, $r->{$k} ? $r->{$k}{n} : 0);
        next unless $n1 < $n0;
        push @out, sprintf('dropped %s: %s (%soriginal %s)', $kind, $o->{$k}{show},
                           ($n0 > 1 ? "count $n0 to $n1; " : ''), line_list($o->{$k}{lines}));
    }
    for my $k (sort { $r->{$a}{lines}[0] <=> $r->{$b}{lines}[0] || $a cmp $b } keys %$r) {
        my ($n0, $n1) = ($o->{$k} ? $o->{$k}{n} : 0, $r->{$k}{n});
        next unless $n1 > $n0;
        push @out, sprintf('introduced %s: %s (%srevised %s)', $kind, $r->{$k}{show},
                           ($n1 > 1 ? "count $n0 to $n1; " : ''), line_list($r->{$k}{lines}));
    }
    return @out;
}

sub line_list {
    my ($lines) = @_;
    my %seen;
    my @u = grep { !$seen{$_}++ } @$lines;
    my $more = @u > 10 ? ', ...' : '';
    @u = @u[0 .. 9] if @u > 10;
    return (@u == 1 ? 'line ' : 'lines ') . join(', ', @u) . $more;
}

# Per-word counts and lines for the modality lists. "not" also counts the
# contracted and fused negations, because "doesn't" to "does" flips a claim.
sub modality {
    my ($prose) = @_;
    my %seen;
    my %re = map {
        $_ => ($_ eq 'not' ? qr/\bnot\b|\bcannot\b|n['\x{2019}]t\b/i : qr/\b\Q$_\E\b/i)
    } grep { !$seen{$_}++ } @HEDGE, @CERTAIN;
    my %count = map { $_ => { n => 0, lines => [] } } keys %re;
    my @lines = split /\n/, $prose, -1;
    for my $i (0 .. $#lines) {
        for my $w (keys %re) {
            my $n = () = $lines[$i] =~ /$re{$w}/g;
            next unless $n;
            $count{$w}{n} += $n;
            push @{ $count{$w}{lines} }, $i + 1;
        }
    }
    return \%count;
}

sub modality_diff {
    my ($o, $r) = @_;
    my @out;
    for my $w (@HEDGE) {
        next unless $r->{$w}{n} < $o->{$w}{n};
        push @out, sprintf('hedge or limiter fell: %s %d to %d (original %s)',
                           $w, $o->{$w}{n}, $r->{$w}{n}, line_list($o->{$w}{lines}));
    }
    for my $w (@CERTAIN) {
        next unless $r->{$w}{n} > $o->{$w}{n};
        push @out, sprintf('certainty word rose: %s %d to %d (revised %s)',
                           $w, $o->{$w}{n}, $r->{$w}{n}, line_list($r->{$w}{lines}));
    }
    return @out;
}

# Candidate labels whose hit count rose, in order of first revised line.
sub introduced {
    my ($ocand, $rcand) = @_;
    my $tally = sub {
        my %t;
        for (@{ $_[0] }) {
            next unless /^(.+?):(\d+)(?:\s|\z)/;
            my ($label, $line) = ($1, $2);
            $label =~ s/^stacked frames \(.*\)\z/stacked frames/;
            push @{ $t{$label} }, $line;
        }
        return \%t;
    };
    my ($o, $r) = ($tally->($ocand), $tally->($rcand));
    my @out;
    for my $label (sort { $r->{$a}[0] <=> $r->{$b}[0] || $a cmp $b } keys %$r) {
        my ($n0, $n1) = (scalar @{ $o->{$label} // [] }, scalar @{ $r->{$label} });
        next unless $n1 > $n0;
        push @out, sprintf('revision introduced: %s %d to %d (revised %s)',
                           $label, $n0, $n1, line_list($r->{$label}));
    }
    return @out;
}

sub visible_words {
    my ($prose) = @_;
    $prose =~ s/^\s*(?:[-*+]|\d+[.)])\s+//mg;
    return scalar grep { /[\p{L}\p{N}]/ } split ' ', $prose;
}
