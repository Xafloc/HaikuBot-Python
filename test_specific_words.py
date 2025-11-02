#!/usr/bin/env python3
"""Test specific problematic words."""

import sys
sys.path.insert(0, '.')

from backend.haiku.syllable_counter import (
    count_syllables,
    _count_syllables_pyphen,
    _count_syllables_library,
    _count_syllables_cmu,
    _count_syllables_heuristic
)

# Test specific problem words
test_words = [
    "EvilB",
    "irl",
    "Diannao",
]

print("Testing individual problem words:\n")
print("=" * 80)

for word in test_words:
    pyphen = _count_syllables_pyphen(word)
    library = _count_syllables_library(word)
    cmu = _count_syllables_cmu(word)
    heuristic = _count_syllables_heuristic(word)
    final = count_syllables(word)

    print(f"\nWord: '{word}'")
    print(f"  pyphen:    {pyphen}")
    print(f"  syllables: {library}")
    print(f"  cmu:       {cmu}")
    print(f"  heuristic: {heuristic}")
    print(f"  FINAL:     {final}")
    print("-" * 80)

# Now test the full phrases word by word
print("\n\nFull phrase breakdown:\n")
print("=" * 80)

phrase1 = "EvilB: which dog do you have?"
print(f"\nPhrase: '{phrase1}'")
words = phrase1.replace(":", "").split()
total = 0
for word in words:
    count = count_syllables(word)
    print(f"  '{word}' = {count}")
    total += count
print(f"  TOTAL: {total}")
print("-" * 80)

phrase5 = "Nice, but never saw them irl"
print(f"\nPhrase: '{phrase5}'")
words = phrase5.replace(",", "").split()
total = 0
for word in words:
    count = count_syllables(word)
    print(f"  '{word}' = {count}")
    total += count
print(f"  TOTAL: {total}")
print("-" * 80)

print("\n" + "=" * 80)
