#!/usr/bin/env python3
"""Test syllable counting for debugging."""

import sys
from backend.haiku.syllable_counter import count_syllables
from syllables import estimate as syllables_estimate
import pyphen

# Initialize pyphen
hyphenator = pyphen.Pyphen(lang='en_US')

def test_word(word):
    """Test a single word with all methods."""
    # Clean the word
    clean = word.strip().lower()

    # Test syllables library
    try:
        syl_count = syllables_estimate(clean)
    except:
        syl_count = 0

    # Test pyphen
    try:
        hyphenated = hyphenator.inserted(clean)
        pyph_count = hyphenated.count('-') + 1 if hyphenated else 0
    except:
        pyph_count = 0

    print(f"  '{word}': syllables_lib={syl_count}, pyphen={pyph_count} (hyphenated: {hyphenator.inserted(clean)})")

def test_phrase(phrase):
    """Test a full phrase."""
    print(f"\nPhrase: '{phrase}'")
    print(f"Total count: {count_syllables(phrase)} syllables")
    print("Word breakdown:")

    # Split and test each word
    import re
    words = re.split(r'[\s\-]+', re.sub(r'[^\w\s\-]', '', phrase.lower()))
    for word in words:
        if word:
            test_word(word)

# Test the problematic phrases
print("=" * 70)
print("TESTING PROBLEMATIC PHRASES")
print("=" * 70)

test_phrase("I did that earlier this year")
print(f"\n>>> EXPECTED: 8 syllables (I=1, did=1, that=1, ear-li-er=3, this=1, year=1)")

test_phrase("going to the mother-in-laws")
print(f"\n>>> EXPECTED: 8 syllables (go-ing=2, to=1, the=1, moth-er-in-laws=4)")

test_phrase("which dog do you have")
print(f"\n>>> EXPECTED: 6 syllables (which=1, dog=1, do=1, you=1, have=1... wait, that's only 5?)")
print(f">>> Let me recount: which=1, dog=1, do=1, you=1, have=1 = 5 syllables")
print(f">>> Actually this might be CORRECT if it's 5 syllables")

# Test individual problem words
print("\n" + "=" * 70)
print("TESTING SPECIFIC PROBLEM WORDS")
print("=" * 70)

test_phrase("earlier")
print(">>> EXPECTED: 3 syllables (ear-li-er)")

test_phrase("mother-in-laws")
print(">>> EXPECTED: 4 syllables (moth-er-in-laws)")

test_phrase("going")
print(">>> EXPECTED: 2 syllables (go-ing)")

test_phrase("year")
print(">>> EXPECTED: 1 syllable")

# Test additional edge cases
print("\n" + "=" * 70)
print("ADDITIONAL TESTS")
print("=" * 70)

test_phrase("the")
print(">>> EXPECTED: 1 syllable")

test_phrase("mother")
print(">>> EXPECTED: 2 syllables (moth-er)")

test_phrase("in")
print(">>> EXPECTED: 1 syllable")

test_phrase("laws")
print(">>> EXPECTED: 1 syllable")
