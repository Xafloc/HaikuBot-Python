#!/usr/bin/env python3
"""Test the simple fix: switch from pyphen-first to syllables-first."""

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

def count_current_method(word):
    """Current method: pyphen first, syllables fallback."""
    pyphen_count = count_pyphen(word)
    syllables_count = count_syllables_lib(word)

    if pyphen_count > 0:
        return pyphen_count, "pyphen"
    elif syllables_count > 0:
        return syllables_count, "syllables"
    else:
        return 1, "heuristic"

def count_proposed_method(word):
    """Proposed method: syllables first, pyphen fallback."""
    syllables_count = count_syllables_lib(word)
    pyphen_count = count_pyphen(word)

    if syllables_count > 0:
        return syllables_count, "syllables"
    elif pyphen_count > 0:
        return pyphen_count, "pyphen"
    else:
        return 1, "heuristic"

def count_phrase(phrase, counter_func):
    """Count syllables in phrase."""
    words = re.split(r'[\s\-]+', re.sub(r'[^\w\s\-]', '', phrase))
    total = 0
    details = []
    for word in words:
        if word:
            count, method = counter_func(word)
            total += count
            details.append(f"{word}={count}({method[0]})")  # First letter only
    return total, details

# Test phrases
test_phrases = [
    ("overpowering it all", 7),
    ("overpowering", 5),
    ("confused by reality", 5),
    ("time can be irrelavent", 7),
    ("clarification required", 7),
    ("entering denial phase", 7),
]

print("=" * 110)
print("SIMPLE FIX COMPARISON: pyphen-first (CURRENT) vs syllables-first (PROPOSED)")
print("=" * 110)
print(f"{'Phrase':<30} {'Expected':<10} {'Current':<12} {'Proposed':<12} {'Result':<15} {'Improvement'}")
print("=" * 110)

current_correct = 0
proposed_correct = 0

for phrase, expected in test_phrases:
    current_count, current_details = count_phrase(phrase, count_current_method)
    proposed_count, proposed_details = count_phrase(phrase, count_proposed_method)

    current_match = "✓" if current_count == expected else "✗"
    proposed_match = "✓" if proposed_count == expected else "✗"

    if current_count == expected:
        current_correct += 1
    if proposed_count == expected:
        proposed_correct += 1

    # Determine improvement status
    if current_count != expected and proposed_count == expected:
        improvement = "✓ FIXED"
    elif current_count == expected and proposed_count != expected:
        improvement = "✗ BROKE"
    elif current_count == expected and proposed_count == expected:
        improvement = "= same (good)"
    else:
        improvement = "= same (bad)"

    print(f"{phrase:<30} {expected:<10} {current_count} {current_match:<10} {proposed_count} {proposed_match:<10} {improvement}")

print("=" * 110)
print(f"{'ACCURACY:':<30} {'':10} {current_correct}/6 ({current_correct*100//6}%){'':7} "
      f"{proposed_correct}/6 ({proposed_correct*100//6}%)")
print("=" * 110)

improvement = proposed_correct - current_correct
if improvement > 0:
    print(f"\n✓ RECOMMENDATION: Switch to syllables-first (fixes {improvement} phrases)")
elif improvement < 0:
    print(f"\n✗ WARNING: Syllables-first is worse (breaks {-improvement} phrases)")
else:
    print(f"\n= No change in accuracy")

print("\n" + "=" * 110)
print("IMPLEMENTATION:")
print("=" * 110)
print("""
In backend/haiku/syllable_counter.py around line 158, change from:

    # Original logic: prefer pyphen, fallback to syllables library
    if pyphen_count > 0:
        word_count = pyphen_count
    elif syllables_count > 0:
        word_count = syllables_count
    else:
        # Neither library could count, use heuristic
        word_count = _count_syllables_heuristic(part_lower)

To:

    # NEW: prefer syllables library, fallback to pyphen
    if syllables_count > 0:
        word_count = syllables_count
    elif pyphen_count > 0:
        word_count = pyphen_count
    else:
        # Neither library could count, use heuristic
        word_count = _count_syllables_heuristic(part_lower)
""")
print("=" * 110)
