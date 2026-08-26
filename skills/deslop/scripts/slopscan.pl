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
# Exit 0 clean, 10 candidates only, 20 hard failures present.

use strict;
use warnings;

binmode STDOUT, ':encoding(UTF-8)';
binmode STDERR, ':encoding(UTF-8)';

my $surface = 'house';
my $json    = 0;
my @files;
while (@ARGV) {
    my $a = shift @ARGV;
    if    ($a eq '--surface') { $surface = shift @ARGV // 'house' }
    elsif ($a eq '--json')    { $json    = 1 }
    elsif ($a =~ /^-/)        { die "unknown flag: $a\n" }
    else                      { push @files, $a }
}
die "usage: slopscan.pl [--surface house|published|agent|sample] [--json] FILE...\n"
    unless @files;

# Dashes and curly quotes are a house rule, not a universal AI tell (see
# references/evidence.md: published human essays out-dash frontier models).
# On the house surface they are hard failures because the contract bans them.
# Elsewhere they are density candidates.
my $dash_is_hard = ($surface eq 'house');

my ($hard_total, $cand_total) = (0, 0);
my @report;

for my $file (@files) {
    open my $fh, '<:encoding(UTF-8)', $file or do { warn "skip $file: $!\n"; next };
    my $raw = do { local $/; <$fh> };
    close $fh;

    my $prose = mask($raw);

    my @hard = ();
    my @cand = ();

    # ---- character-level checks -------------------------------------------
    push @{ $dash_is_hard ? \@hard : \@cand },
        hits($prose, qr/[\x{2014}\x{2013}]/,        'em or en dash');
    push @{ $dash_is_hard ? \@hard : \@cand },
        hits($prose, qr/(?<=[[:alnum:],;:)"'])--(?=[[:alnum:]("'])|(?<=\s)--(?=\s)/, 'double-hyphen dash');
    push @hard, hits($prose, qr/[\x{201C}\x{201D}\x{2018}\x{2019}]/, 'curly quote');
    push @hard, hits($prose, qr/[\x{00A0}\x{2007}\x{202F}]/,         'non-breaking space');
    push @hard, hits($prose, qr/\x{2026}/,                            'ellipsis character');

    # provider and harness residue: always a hard failure, never legitimate
    push @hard, hits($prose, qr/turn\d{1,4}(?:search|news|image)\d{1,4}/, 'chat-export artifact');
    push @hard, hits($prose, qr/\[cite:\s*\d+\]|\[span_\d+\]/,            'citation artifact');
    push @hard, hits($prose, qr/utm_source=(?:chatgpt|claude)/,           'tracking parameter');
    push @hard, hits($prose, qr/\x{3010}[^\x{3011}]{0,40}\x{3011}/,       'lenticular bracket');

    # ---- candidates: need judgment ----------------------------------------
    push @cand, hits($prose, qr/^\s*[-*+]\s+\*\*[^*]+:\*\*/m,      'bold-lead bullet');
    push @cand, hits($prose, qr/^#{1,6} .*[a-z] [A-Z][a-z]/m,      'possible title-case heading');
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
    push @cand, hits($prose, qr/(?:^|[.!?]\s+|^\s*[-*+]\s+)(?:let me be (?:blunt|clear)|here'?s the thing|the thing is|real talk|to be honest)\b|\bworth naming that\b/i,
                     'performed candor');
    push @cand, hits($prose, qr/\b(?:epistemic status|~?\d{1,3}% confident|I hold this loosely)\b/i,
                     'calibration theatre');
    push @cand, hits($prose, qr/\b(?:production-ready|enterprise-grade|battle-tested|built with \w+ in mind|designed for scale)\b/i,
                     'unfalsifiable claim');
    push @cand, hits($prose, qr/^\s*(?:The result\?|Why does this matter\?|So what changed\?|The catch\?)/mi,
                     'rhetorical-question transition');

    # ---- rhythm diagnostics (never gate on these) --------------------------
    my @sent  = sentences($prose);
    my @paras = paragraphs($prose);
    my $srhy  = spread('sentence', \@sent);
    my $prhy  = spread('paragraph', \@paras);

    # over-correction trip: deterministic, no judgment
    my $trip = '';
    if (@sent >= 4) {
        my ($m, $sd) = stats(\@sent);
        my $tiny = grep { $_ < 6 } @sent;
        $trip = sprintf('OVER-CORRECTED: mean %.1f words, sd %.1f', $m, $sd)
            if $m < 10 && $sd < 4;
        $trip = sprintf('OVER-CORRECTED: %d%% of sentences under 6 words',
                        int(100 * $tiny / @sent))
            if $tiny / @sent > 0.6;
    }

    $hard_total += scalar @hard;
    $cand_total += scalar @cand;

    push @report, { file => $file, hard => \@hard, cand => \@cand,
                    sent => $srhy, para => $prhy, trip => $trip };
}

# ---- output ---------------------------------------------------------------
if ($json) {
    print "{\n";
    print qq(  "surface": "$surface",\n);
    print qq(  "hard": $hard_total,\n  "candidates": $cand_total\n);
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
        print "  rhythm: $r->{sent}\n";
        print "          $r->{para}\n";
        print "  $r->{trip}\n" if $r->{trip};
        print "  clean\n" if !@{ $r->{hard} } && !@{ $r->{cand} };
    }
    print "\nsurface=$surface hard=$hard_total candidates=$cand_total\n";
}

exit 20 if $hard_total;
exit 10 if $cand_total;
exit 0;

# ---- helpers --------------------------------------------------------------

# Replace every protected region with same-length blanks so line and column
# numbers survive. Protected: YAML frontmatter, fenced code (backtick and
# tilde, any indent, any fence length), indented code blocks, inline code
# spans, blockquotes, and link/image targets.
sub mask {
    my ($t) = @_;
    $t =~ s/\A---\n.*?\n---\n/blank($&)/se;
    $t =~ s/^([ \t]{0,3})(`{3,}|~{3,})[^\n]*\n.*?^\1?\2[^\n]*$/blank($&)/gmse;
    $t =~ s/^([ \t]{0,3})(`{3,}|~{3,})[^\n]*\n.*\z/blank($&)/mse;   # unclosed fence
    $t =~ s/^(?: {4}|\t)\S[^\n]*$/blank($&)/gme;
    $t =~ s/(`+)[^`\n]*?\1/blank($&)/ge;
    $t =~ s/^[ \t]*>[^\n]*$/blank($&)/gme;
    $t =~ s/\]\([^)\s]+/blank($&)/ge;
    return $t;
}

sub blank { my ($s) = @_; $s =~ s/[^\n]/ /g; return $s }

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
    return sprintf('%s spread: n=%d min=%d median=%d max=%d mean=%.1f cv=%.2f%s',
                   $kind, scalar @s, $s[0], $s[int(@s / 2)], $s[-1], $m, $cv,
                   $cv < 0.35 ? '  <- flat, look at the rhythm' : '');
}
