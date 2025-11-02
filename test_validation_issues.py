#!/usr/bin/env python3
"""Test phrases that admin panel says are wrong but are actually right."""

import sys
sys.path.insert(0, '.')

from backend.config import load_config
from backend.database import init_db
from backend.haiku.syllable_counter import count_syllables

# Initialize database for acronym lookup
config = load_config()
database_url = f"sqlite:///{config.database.path}"
init_db(database_url)

# Test phrases that are supposedly wrong
test_phrases = [
    ("writ of habeas corpus", 7),
    ("the road went out to nowhere", 7),
    ("I am not evil", 5),
]

print("Testing phrases marked as wrong by admin panel:\n")
print("=" * 70)

for phrase, expected in test_phrases:
    count = count_syllables(phrase)
    match = "✓" if count == expected else "✗"

    print(f"\n{match} Phrase: '{phrase}'")
    print(f"  Stored in DB:  {expected} syllables")
    print(f"  Counter says:  {count} syllables")

    if count != expected:
        print(f"  MISMATCH: Off by {abs(count - expected)}")

    print("-" * 70)

print("\n" + "=" * 70)
