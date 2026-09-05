#!/usr/bin/env perl
# slopscan: protection-aware mechanical slop scan for Markdown and plain text.
#
# Masks everything the preservation contract forbids editing (frontmatter,
# fenced code in every form, indented code, inline code spans, blockquoted
# material, link targets) before any check runs, so a scan never reports a
# hit inside code or inside a quoted example.
#
# Usage:   slopscan.pl [--surface NAME] [--json] FILE...
# Surface: house (default) | published | agent | sample
#
# Exit 0 clean, 10 candidates only, 20 hard failures, 30 unreadable input.

use strict;
use warnings;
use Encode qw(decode FB_CROAK);
use IO::Handle ();

binmode STDOUT, ':encoding(UTF-8)';
binmode STDERR, ':encoding(UTF-8)';

my $surface     = 'house';
my $json        = 0;
my $show_masked = 0;
my @files;
while (@ARGV) {
    my $a = shift @ARGV;
    if    ($a eq '--surface')     { $surface = shift @ARGV // 'house' }
    elsif ($a eq '--json')        { $json    = 1 }
    elsif ($a eq '--show-masked') { $show_masked = 1 }
    elsif ($a =~ /^-/)        { die "unknown flag: $a\n" }
    else                      { push @files, $a }
}
die "usage: slopscan.pl [--surface house|published|agent|sample] [--json] [--show-masked] FILE...\n"
    unless @files;
my %VALID = map { $_ => 1 } qw(house published agent sample);
die "unknown surface '$surface' (house|published|agent|sample)\n"
    unless $VALID{$surface};

# Dashes are a house rule rather than evidence of authorship.
# They are hard failures on our own files, house and agent alike, because the
# project contract bans them in anything we write. On someone else's prose
# (published, sample) they are density candidates needing converging signals.
my ($hard_total, $cand_total, $io_errors) = (0, 0, 0);
my @report;

for my $file (@files) {
    unless (-f $file) {
        warn "not a regular input file: $file\n";
        $io_errors++;
        next;
    }
    open my $fh, '<:raw', $file
        or do { warn "cannot read $file: $!\n"; $io_errors++; next };
    $! = 0;
    my $bytes = do { local $/; <$fh> };
    my $read_error = $fh->error ? ($! ? "$!" : 'input error') : '';
    close $fh or $read_error ||= "$!";
    if ($read_error) {
        warn "cannot read $file: $read_error\n";
        $io_errors++;
        next;
    }
    my $raw = eval { decode('UTF-8', $bytes // '', FB_CROAK) };
    if ($@) {
        warn "invalid UTF-8 input: $file\n";
        $io_errors++;
        next;
    }

    $raw =~ s/\A\x{FEFF}//;  # a byte-order mark otherwise hides the frontmatter
    $raw =~ s/\r\n?/\n/g;   # normalize CRLF and CR before anything else
    my $prose = mask($raw);

    my ($hard, $cand) = checks($prose, $surface);

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
    my $srhy  = spread('sentence', \@sent);
    my $prhy  = spread('paragraph', \@paras);

    $hard_total += scalar @hard;
    $cand_total += scalar @cand;

    push @report, { file => $file, hard => \@hard, cand => \@cand,
                    suppressed => \@suppressed,
                    sent => $srhy, para => $prhy };
}

# ---- output ---------------------------------------------------------------
if ($json) {
    print "{\n";
    print qq(  "surface": "$surface",\n);
    print qq(  "hard": $hard_total,\n  "candidates": $cand_total,\n);
    print qq(  "io_errors": $io_errors\n);
    print "}\n";
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
        print "  clean\n" if !@{ $r->{hard} } && !@{ $r->{cand} };
    }
    print "\nsurface=$surface hard=$hard_total candidates=$cand_total\n";
}

exit 30 if $io_errors;     # could not read an input: never report clean
exit 20 if $hard_total;
exit 10 if $cand_total;
exit 0;

# Every content check, so the same set can run against masked and raw text.
sub checks {
    my ($prose, $surf) = @_;
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
    push @cand, hits($prose, qr/\bnot (?:just|only|merely|simply)\b[^.!?]{0,60}\b(?:it'?s|it is|but)\b/i,
                     'negative parallelism');
    push @cand, hits($prose, qr/,\s+(?:highlighting|underscoring|emphasizing|ensuring|reflecting|symbolizing|showcasing|fostering|contributing|cultivating|encompassing|demonstrating|solidifying|cementing|signaling|positioning|paving)\s/i,
                     'participial tail');
    push @cand, hits($prose, qr/\b(?:each|every)\s+\w*\s*a\s+\w+\s+(?:in|of)\s+the\b/i,
                     'distributive appositive');
    push @cand, hits($prose, qr/\b(?:plays?|playing) an? \w+ role in\b/i, 'plays-a-role paradigm');
    push @cand, hits($prose, qr/\b(?:extends?|goes?|moves?|reaches?) (?:far )?beyond (?:mere|simple|simply|surface)\b/i,
                     'beyond family');
    push @cand, hits($prose, qr/\b(?:load-bearing|in service of|earns its keep|first-order concern|the binding constraint|asymmetric upside|forcing function)\b/i,
                     'house jargon or borrowed rigor');
    push @cand, hits($prose, qr/\bcheap(?:est|ly)?\b|\bpay(?:s|ing)? rent\b|\bbuys you\b|\bcosts you nothing\b/i,
                     'transactional effort framing');
    push @cand, stacked_frames($prose);
    push @cand, hits($prose, qr/(?:^|[.!?]\s+|^\s*[-*+]\s+)(?:let me be (?:blunt|clear)|here'?s the thing|the thing is|real talk|to be honest)\b|\bworth naming that\b/i,
                     'performed candor');
    push @cand, hits($prose, qr/\b(?:epistemic status|~?\d{1,3}% confident|I hold this loosely)\b/i,
                     'calibration theatre');
    push @cand, hits($prose, qr/\b(?:production-ready|enterprise-grade|battle-tested|built with \w+ in mind|designed for scale)\b/i,
                     'unfalsifiable claim');
    push @cand, hits($prose, qr/^\s*(?:The result\?|Why does this matter\?|So what changed\?|The catch\?)/mi,
                     'rhetorical-question transition');

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
sub mask {
    my ($t) = @_;
    my @lines = split /\n/, $t, -1;

    my $in_front = (@lines && $lines[0] eq '---') ? 1 : 0;
    my ($fence_char, $fence_len, $in_quote, $in_code, $prev_blank) = ('', 0, 0, 0, 1);

    for my $i (0 .. $#lines) {
        my $line = $lines[$i];
        my $blank = ($line =~ /^\s*$/) ? 1 : 0;

        if ($in_front) {
            my $end = ($i > 0 && $line =~ /^(?:---|\.\.\.)\s*$/);
            $lines[$i] = blank($line);
            $in_front = 0 if $end;
            $prev_blank = $blank;
            next;
        }

        if ($fence_len) {
            # closer: same character, at least as long, whitespace-only tail
            my $close = '^ {0,3}' . quotemeta($fence_char)
                      . '{' . $fence_len . ',}\s*$';
            $fence_len = 0 if $line =~ /$close/;
            $lines[$i] = blank($line);
            $prev_blank = $blank;
            next;
        }

        # fence opener. For backtick fences the info string cannot contain a
        # backtick, which is what keeps a prose line of code ticks from opening
        # a fence. A fence also ends any lazy blockquote continuation.
        if ($line =~ /^ {0,3}(`{3,})([^`]*)$/ || $line =~ /^ {0,3}(~{3,})(.*)$/) {
            $in_quote   = 0;
            $fence_char = substr($1, 0, 1);
            $fence_len  = length $1;
            $lines[$i]  = blank($line);
            $prev_blank = 0;
            next;
        }

        # blockquote, including lazy continuation. A lazy continuation ends at a
        # blank line or at any line that starts a new block, because an ATX
        # heading, fence, list, or thematic break interrupts a paragraph.
        if ($line =~ /^ {0,3}>/) { $in_quote = 1 }
        elsif ($blank
               || $line =~ /^ {0,3}(?:\#{1,6}\s|[-*+]\s|\d+[.)]\s|(?:-\s*){3,}$|(?:_\s*){3,}$|(?:\*\s*){3,}$)/
               || $line =~ m{^ {0,3}</?(?:script|pre|style|textarea|div|table|p|ul|ol|li|h[1-6]|blockquote|section|article|!--)}i) {
            $in_quote = 0;
        }
        if ($in_quote) {
            $lines[$i] = blank($line);
            $prev_blank = $blank;
            next;
        }

        # indented code block: opens on four or more spaces (or a tab) after a
        # blank line, and continues across further indented and blank lines.
        if ($in_code) {
            if ($blank || $line =~ /^(?: {4,}|\t)/) {
                $lines[$i] = blank($line);
                $prev_blank = $blank;
                next;
            }
            $in_code = 0;
        }
        if (!$blank && $prev_blank && $line =~ /^(?: {4,}|\t)\S/) {
            $in_code    = 1;
            $lines[$i]  = blank($line);
            $prev_blank = 0;
            next;
        }

        $prev_blank = $blank;
    }

    my $out = join "\n", @lines;

    # Inline code spans, including spans that wrap across a soft line break. The
    # opening run must not be escaped, the closing run must be exactly the same
    # length (a two-tick opener is not closed by a three-tick run), and the span
    # may never cross a blank line, because the paragraph ends there. Without
    # that stop, one unpaired backtick run in prose pairs with another far away
    # and blanks every line between them, which is how the contributor guide's
    # own inventory table went invisible on the first dogfood scan.
    $out =~ s/(?<!\\)(?<!`)(`+)(?!`)((?:(?!(?<!`)\1(?!`))(?!\n[ \t]*\n).)*?)(?<!`)\1(?!`)/blank($&)/gse;
    # Link and image markup: angle-bracket destination, bare destination with
    # balanced parentheses, optional title in any of the three quote forms,
    # reference definitions, and autolinks. The whole destination-and-title run
    # is markup rather than prose, so it is masked as one unit.
    my $title = qr/(?:\s+(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\((?:[^)\\]|\\.)*\)))?/;
    my $bare  = qr/(?:[^()\s\\]|\\.|\((?:[^()\\]|\\.|\((?:[^()]|\\.)*\))*\))+/;
    my $label = qr/(?<!\\)\[(?:[^\[\]\\]|\\.|\[[^\]]*\])*(?<!\\)\]/;
    $out =~ s/$label\(\s*<[^>\n]*>$title\s*\)/blank_tail($&)/ge;
    $out =~ s/$label\(\s*$bare$title\s*\)/blank_tail($&)/ge;
    # reference definitions, but never a footnote definition, whose body is prose
    $out =~ s/^ {0,3}\[(?!\^)[^\]]+\]:\s*(?:<[^>\n]*>|\S+)$title/blank($&)/gme;
    $out =~ s/<(?:https?|ftp|mailto):[^>\s]*>/blank($&)/ge;
    # HTML comments never reach a reader, and a bare URL is not prose
    $out =~ s/<!--.*?-->/blank($&)/gse;
    $out =~ s{(?<![\w/])(?:https?|ftp)://[^\s<>()\[\]"']+}{blank($&)}ge;

    return $out;
}

sub blank { my ($s) = @_; $s =~ s/[^\n]/ /g; return $s }

# For link markup, the label is visible prose and the destination is not, so mask
# from the closing bracket onward and leave the label text scannable.
sub blank_tail {
    my ($s) = @_;
    my $i = rindex($s, '](');
    return blank($s) if $i < 0;
    return substr($s, 0, $i) . blank(substr($s, $i));
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

# Stacked rhetorical frames (catalog N19). Three distinct families generate a
# candidate, not a quality judgment or model fingerprint. List items count as
# their own paragraphs so separate bullets cannot pool into a false hit.
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
    my @lines = split /\n/, $text, -1;
    my ($start, $para) = (0, '');
    my $flush = sub {
        return if $para eq '';
        my @hit = grep { $para =~ $_->[1] } @fams;
        push @out, sprintf('stacked frames (%s):%d',
                           join('+', map { $_->[0] } @hit), $start + 1)
            if @hit >= 3;
        $para = '';
    };
    for my $i (0 .. $#lines) {
        my $line = $lines[$i];
        if ($line =~ /^\s*$/ || $line =~ /^\s*[|#]/) { $flush->(); next }
        $flush->() if $line =~ /^\s*(?:[-*+]|\d+[.)])\s/;
        $start = $i if $para eq '';
        $para .= ($para eq '' ? '' : "\n") . $line;
    }
    $flush->();
    return @out;
}

sub hits {
    my ($text, $re, $label) = @_;
    my @out;
    my @lines = split /\n/, $text, -1;
    for my $i (0 .. $#lines) {
        # table delimiter rows and horizontal rules carry no prose
        next if $lines[$i] =~ /^\s*\|?[\s:|+-]{3,}\|?\s*$/;
        next unless $lines[$i] =~ /$re/;
        my $snip = $lines[$i];
        $snip =~ s/^\s+|\s+$//g;
        $snip = substr($snip, 0, 90) . '...' if length($snip) > 90;
        push @out, sprintf('%s:%d  %s', $label, $i + 1, $snip);
    }
    return @out;
}

# Sentence word counts. Splits only on a terminator followed by whitespace
# and an opening character, so v1.2.3, e.g., Node.js, and file paths stay
# inside one sentence. Skips headings, tables, and list markers.
sub sentences {
    my ($t) = @_;
    my @keep;
    for my $line (split /\n/, $t) {
        next if $line =~ /^\s*[|#]/;
        $line =~ s/^\s*(?:[-*+]|\d+\.)\s+//;
        push @keep, $line;
    }
    my $prose = join "\n", @keep;
    my @out;
    for my $s (split /(?<=[.!?])\s+(?=["(\x{2018}\x{201C}]?[A-Z]|\z)/, $prose) {
        my @w = grep { length } split /\s+/, $s;
        push @out, scalar @w if @w > 1;
    }
    return @out;
}

sub paragraphs {
    my ($t) = @_;
    my @out;
    for my $p (split /\n\s*\n/, $t) {
        next if $p =~ /^\s*[|#]/;
        my @w = grep { length } split /\s+/, $p;
        push @out, scalar @w if @w > 3;
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
