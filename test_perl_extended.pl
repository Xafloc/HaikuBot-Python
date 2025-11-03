#!/usr/bin/env perl
# Test Perl Lingua::EN::Syllable against extended phrase set

use strict;
use warnings;
use lib './Lingua-EN-Syllable-0.31/lib';

# Try to load Lingua::EN::Syllable
my $has_lingua;
BEGIN {
    eval {
        require Lingua::EN::Syllable;
        Lingua::EN::Syllable->import();
        $has_lingua = 1;
    };
    if ($@) {
        $has_lingua = 0;
        print "ERROR: Lingua::EN::Syllable not available\n";
        print "Run with: perl -I./Lingua-EN-Syllable-0.31/lib test_perl_extended.pl\n\n";
        exit 1;
    }
}

sub count_phrase {
    my ($phrase) = @_;

    # Remove punctuation, split on spaces and hyphens
    $phrase =~ s/[^\w\s\-']//g;
    my @words = split /[\s\-]+/, $phrase;

    my $total = 0;
    for my $word (@words) {
        next unless $word;
        my $count = Lingua::EN::Syllable::syllable($word);
        $total += $count;
    }

    return $total;
}

# Extended test set (14 phrases)
my @test_phrases = (
    # Original 6 phrases
    ["overpowering it all", 7],
    ["overpowering", 5],
    ["confused by reality", 7],
    ["time can be irrelavent", 7],
    ["clarification required", 7],
    ["entering denial phase", 7],

    # New 8 phrases
    ["brought to you by", 4],
    ["creativity", 5],
    ["similitude of dreaming", 7],
    ["I am not fat, I am pregnant", 8],
    ["my redeemer, my savior", 7],
    ["autodetecting", 5],
    ["in desperate straits", 5],
    ["I'm emotionally scarred", 7],
);

print "=" x 100 . "\n";
print "PERL LINGUA::EN::SYLLABLE TEST (14 phrases)\n";
print "=" x 100 . "\n";
printf "%-40s %-10s %-10s %s\n", "Phrase", "Expected", "Perl", "Result";
print "=" x 100 . "\n";

my $correct = 0;

for my $test (@test_phrases) {
    my ($phrase, $expected) = @$test;
    my $actual = count_phrase($phrase);

    my $match = ($actual == $expected) ? "✓" : "✗";
    $correct++ if $actual == $expected;

    printf "%-40s %-10d %-10d %s\n", $phrase, $expected, $actual, $match;
}

print "=" x 100 . "\n";
printf "Accuracy: %d/%d (%d%%)\n", $correct, scalar(@test_phrases),
    int($correct * 100 / scalar(@test_phrases));
print "=" x 100 . "\n";

# Word-by-word analysis for failures
print "\n" . "=" x 100 . "\n";
print "DETAILED ANALYSIS OF FAILURES\n";
print "=" x 100 . "\n";

for my $test (@test_phrases) {
    my ($phrase, $expected) = @$test;
    my $actual = count_phrase($phrase);

    next if $actual == $expected;  # Skip successes

    print "\nPhrase: '$phrase' (expected $expected, got $actual)\n";

    # Show word breakdown
    $phrase =~ s/[^\w\s\-']//g;
    my @words = split /[\s\-]+/, $phrase;

    for my $word (@words) {
        next unless $word;
        my $count = Lingua::EN::Syllable::syllable($word);
        print "  $word = $count\n";
    }
}

print "\n" . "=" x 100 . "\n";
