#!/usr/bin/env python3
"""Test specific problem phrases with syllable counter."""

import sys
sys.path.insert(0, '.')

from backend.haiku.syllable_counter import count_syllables

# Test phrases that user says are incorrectly tagged
test_phrases = [
    "EvilB: which dog do you have?",
    "I did that earlier this year...",
    "going to the mother-in-laws. :(",
    "Good morning Diannao",
    "Nice, but never saw them irl"
]

print("Testing problem phrases with 3-way voting syllable counter:\n")
print("=" * 70)

for phrase in test_phrases:
    count = count_syllables(phrase)
    print(f"\nPhrase: '{phrase}'")
    print(f"Syllable count: {count}")
    print("-" * 70)

print("\n" + "=" * 70)
