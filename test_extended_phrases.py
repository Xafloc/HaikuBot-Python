#!/usr/bin/env python3
"""Test all libraries against extended phrase set."""

import sys
sys.path.insert(0, '.')

import re
import pyphen
from syllables import estimate as syllables_estimate

# Initialize pyphen
_hyphenator = pyphen.Pyphen(lang='en_US')

def count_pyphen(word):
    """Count using pyphen."""
    try:
        hyphenated = _hyphenator.inserted(word.lower())
        if hyphenated:
            return hyphenated.count('-') + 1
    except:
        pass
    return 0

def count_syllables_lib(word):
    """Count using syllables library."""
    try:
        return max(0, syllables_estimate(word.lower()))
    except:
        return 0

def count_phrase_pyphen(phrase):
    """Count syllables in phrase using pyphen first."""
    words = re.split(r'[\s\-]+', re.sub(r'[^\w\s\-]', '', phrase))
    total = 0
    for word in words:
        if word:
            count = count_pyphen(word)
            if count > 0:
                total += count
            else:
                count = count_syllables_lib(word)
                total += count if count > 0 else 1
    return total

def count_phrase_syllables(phrase):
    """Count syllables in phrase using syllables first."""
    words = re.split(r'[\s\-]+', re.sub(r'[^\w\s\-]', '', phrase))
    total = 0
    for word in words:
        if word:
            count = count_syllables_lib(word)
            if count > 0:
                total += count
            else:
                count = count_pyphen(word)
                total += count if count > 0 else 1
    return total

# Extended test set
test_phrases = [
    # Original 6 phrases
    ("overpowering it all", 7),
    ("overpowering", 5),
    ("confused by reality", 7),
    ("time can be irrelavent", 7),
    ("clarification required", 7),
    ("entering denial phase", 7),

    # New 8 phrases (entering denial phase already in original 6)
    ("brought to you by", 4),  # DB says 5 (wrong)
    ("creativity", 5),
    ("similitude of dreaming", 7),
    ("I am not fat, I am pregnant", 8),  # DB says 7 (wrong)
    ("my redeemer, my savior", 7),
    ("autodetecting", 5),
    ("in desperate straits", 5),
    ("I'm emotionally scarred", 7),
]

print("=" * 100)
print("EXTENDED SYLLABLE COUNTER TEST (14 phrases)")
print("=" * 100)
print(f"{'Phrase':<35} {'Expected':<10} {'pyphen-1st':<12} {'syllables-1st':<15} {'Better'}")
print("=" * 100)

pyphen_correct = 0
syllables_correct = 0

for phrase, expected in test_phrases:
    pyphen_result = count_phrase_pyphen(phrase)
    syllables_result = count_phrase_syllables(phrase)

    pyphen_match = "✓" if pyphen_result == expected else "✗"
    syllables_match = "✓" if syllables_result == expected else "✗"

    if pyphen_result == expected:
        pyphen_correct += 1
    if syllables_result == expected:
        syllables_correct += 1

    # Determine which is better
    if pyphen_result == expected and syllables_result != expected:
        better = "pyphen"
    elif syllables_result == expected and pyphen_result != expected:
        better = "syllables"
    elif pyphen_result == expected and syllables_result == expected:
        better = "both"
    else:
        better = "neither"

    print(f"{phrase:<35} {expected:<10} {pyphen_result} {pyphen_match:<10} {syllables_result} {syllables_match:<13} {better}")

print("=" * 100)
total = len(test_phrases)
print(f"{'FINAL SCORES:':<35} {'':10} {pyphen_correct}/{total} ({pyphen_correct*100//total}%){'':7} "
      f"{syllables_correct}/{total} ({syllables_correct*100//total}%){'':5}")
print("=" * 100)

improvement = syllables_correct - pyphen_correct
if improvement > 0:
    print(f"\n✓ syllables-first is BETTER by {improvement} phrases ({improvement*100//total}% improvement)")
elif improvement < 0:
    print(f"\n✗ pyphen-first is BETTER by {-improvement} phrases")
else:
    print(f"\n= TIE")

print("\n" + "=" * 100)
print("WORD-BY-WORD ANALYSIS OF FAILURES")
print("=" * 100)

# Analyze failures
for phrase, expected in test_phrases:
    pyphen_result = count_phrase_pyphen(phrase)
    syllables_result = count_phrase_syllables(phrase)

    if pyphen_result != expected or syllables_result != expected:
        print(f"\nPhrase: '{phrase}' (expected {expected})")
        print(f"  pyphen-first:    {pyphen_result} {'✓' if pyphen_result == expected else '✗'}")
        print(f"  syllables-first: {syllables_result} {'✓' if syllables_result == expected else '✗'}")

        # Show word breakdown
        words = re.split(r'[\s\-]+', re.sub(r'[^\w\s\-]', '', phrase))
        word_details = []
        for word in words:
            if word:
                p_count = count_pyphen(word) or count_syllables_lib(word) or 1
                s_count = count_syllables_lib(word) or count_pyphen(word) or 1
                word_details.append(f"{word}:p{p_count}/s{s_count}")
        print(f"  Breakdown: {', '.join(word_details)}")
