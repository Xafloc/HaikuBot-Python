#!/usr/bin/env perl
# Simple Perl syllable counter using Lingua::EN::Syllable
# Usage: perl perl_syllable_counter.pl "text to count"

use strict;
use warnings;
use FindBin qw($RealBin);
use lib "$RealBin/../../Lingua-EN-Syllable-0.31/lib";
use Lingua::EN::Syllable;

# Get text from command line argument
my $text = $ARGV[0] || '';

# Remove punctuation, split on spaces and hyphens
$text =~ s/[^\w\s\-']//g;
my @words = split /[\s\-]+/, $text;

my $total = 0;
for my $word (@words) {
    next unless $word;
    my $count = Lingua::EN::Syllable::syllable($word);
    $total += $count;
}

# Print just the number (for easy parsing)
print $total;
