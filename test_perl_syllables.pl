#!/usr/bin/env perl
# Test Perl syllable counting against the same test phrases

use strict;
use warnings;

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
        print "WARNING: Lingua::EN::Syllable not installed\n";
        print "Install with: cpan Lingua::EN::Syllable\n";
        print "or: cpanm Lingua::EN::Syllable\n\n";
    }
}

sub count_syllables_lingua {
    my ($word) = @_;
    return 0 unless $has_lingua;
    return Lingua::EN::Syllable::syllable($word);
}

sub count_syllables_heuristic {
    my ($word) = @_;
    $word = lc($word);

    # Count vowel groups
    my $count = 0;
    my $prev_was_vowel = 0;

    for my $char (split //, $word) {
        my $is_vowel = ($char =~ /[aeiouy]/);
        if ($is_vowel && !$prev_was_vowel) {
            $count++;
        }
        $prev_was_vowel = $is_vowel;
    }

    # Adjust for silent 'e'
    if ($word =~ /e$/ && $count > 1) {
        $count--;
    }

    # Adjust for 'le' ending
    if ($word =~ /[^aeiouy]le$/ && length($word) > 2) {
        $count++;
    }

    return $count > 0 ? $count : 1;
}

sub count_phrase {
    my ($phrase, $use_heuristic) = @_;

    # Remove punctuation, split on spaces and hyphens
    $phrase =~ s/[^\w\s\-]//g;
    my @words = split /[\s\-]+/, $phrase;

    my $total = 0;
    my @details;

    for my $word (@words) {
        next unless $word;

        my $count;
        my $method;

        if ($use_heuristic) {
            $count = count_syllables_heuristic($word);
            $method = "heuristic";
        } else {
            $count = count_syllables_lingua($word);
            $method = "Lingua";
        }

        $total += $count;
        push @details, "$word=$count($method)";
    }

    return ($total, join(", ", @details));
}

# Test phrases
my @test_phrases = (
    ["overpowering it all", 7],
    ["overpowering", 5],
    ["confused by reality", 5],
    ["time can be irrelavent", 7],
    ["clarification required", 7],
    ["entering denial phase", 7],
);

print "=" x 100 . "\n";
print "PERL SYLLABLE COUNTER TEST\n";
print "=" x 100 . "\n";

if ($has_lingua) {
    print "Using: Lingua::EN::Syllable\n";
} else {
    print "Using: Heuristic fallback (Lingua::EN::Syllable not available)\n";
}

print "=" x 100 . "\n";
printf "%-30s %-10s %-10s %-8s %s\n", "Phrase", "Expected", "Perl", "Result", "Details";
print "=" x 100 . "\n";

my $correct = 0;

for my $test (@test_phrases) {
    my ($phrase, $expected) = @$test;
    my ($actual, $details) = count_phrase($phrase, !$has_lingua);

    my $match = ($actual == $expected) ? "✓" : "✗";
    $correct++ if $actual == $expected;

    printf "%-30s %-10d %-10d %-8s %s\n", $phrase, $expected, $actual, $match, "";
}

print "=" x 100 . "\n";
printf "Accuracy: %d/%d (%d%%)\n", $correct, scalar(@test_phrases),
    int($correct * 100 / scalar(@test_phrases));
print "=" x 100 . "\n";

# Detailed breakdown for specific words
print "\nDetailed word analysis:\n";
print "-" x 70 . "\n";

my @words_to_test = qw(overpowering confused reality clarification required);

for my $word (@words_to_test) {
    my $count = $has_lingua ? count_syllables_lingua($word) : count_syllables_heuristic($word);
    printf "%-20s %d syllables\n", $word, $count;
}

print "\nNOTE: If Lingua::EN::Syllable matches your database better than Python libraries,\n";
print "you could create a hybrid system that calls a Perl subprocess for validation.\n";
