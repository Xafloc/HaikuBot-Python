#!/usr/bin/env python3
"""Test phrases that admin panel says are wrong."""

import sys
sys.path.insert(0, '.')

from backend.config import load_config
from backend.database import init_db
from backend.haiku.syllable_counter import count_syllables

# Initialize database
config = load_config()
database_url = f"sqlite:///{config.database.path}"
init_db(database_url)

# Phrases from the screenshot - all should match stored values
test_phrases = [
    ("overpowering it all", 7),       # o-ver-pow-er-ing it all = 7
    ("overpowering", 5),               # o-ver-pow-er-ing = 5
    ("confused by reality", 5),        # con-fused by re-al-i-ty = 2+1+4 = 7? Let me verify
    ("time can be irrelavent", 7),     # time can be ir-rel-a-vent = 1+1+1+4 = 7
    ("clarification required", 7),     # clar-i-fi-ca-tion re-quired = 5+2 = 7
    ("entering denial phase", 7),      # en-ter-ing de-ni-al phase = 3+3+1 = 7
]

print("Testing phrases from admin panel (with reverted voting logic):\n")
print("=" * 80)

all_pass = True

for phrase, stored in test_phrases:
    actual = count_syllables(phrase)
    match = "✓" if actual == stored else "✗"

    if actual != stored:
        all_pass = False

    print(f"\n{match} Phrase: '{phrase}'")
    print(f"  Stored in DB:   {stored} syllables (CORRECT)")
    print(f"  Counter says:   {actual} syllables")

    if actual != stored:
        print(f"  ERROR: Off by {abs(actual - stored)}")

    print("-" * 80)

print("\n" + "=" * 80)
if all_pass:
    print("✓ All tests PASSED!")
else:
    print("✗ Some tests FAILED!")
print("=" * 80)
