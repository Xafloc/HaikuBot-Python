#!/usr/bin/env python3
"""Test syllable counter with database initialized (for acronym support)."""

import sys
sys.path.insert(0, '.')

from backend.config import load_config
from backend.database import init_db
from backend.haiku.syllable_counter import count_syllables

# Initialize database for acronym lookup
config = load_config()
database_url = f"sqlite:///{config.database.path}"
init_db(database_url)

# Test phrases
test_phrases = [
    ("EvilB: which dog do you have?", 8),
    ("I did that earlier this year...", 8),
    ("going to the mother-in-laws. :(", 8),
    ("Good morning Diannao", 6),
    ("Nice, but never saw them irl", 9),  # irl = i-r-l = 3 syllables (acronym lookup)
]

print("Testing syllable counter with database initialized:\n")
print("=" * 70)

all_passed = True

for phrase, expected in test_phrases:
    count = count_syllables(phrase)
    status = "✓" if count == expected else "✗"

    if count != expected:
        all_passed = False

    print(f"\n{status} Phrase: '{phrase}'")
    print(f"  Expected: {expected} syllables")
    print(f"  Got:      {count} syllables")

    if count != expected:
        print(f"  ERROR: Mismatch!")

    print("-" * 70)

print("\n" + "=" * 70)
if all_passed:
    print("✓ All tests passed!")
else:
    print("✗ Some tests failed!")
