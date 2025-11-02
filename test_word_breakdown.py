#!/usr/bin/env python3
"""Debug specific words to see what's going wrong."""

import sys
import logging
sys.path.insert(0, '.')

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from backend.config import load_config
from backend.database import init_db
from backend.haiku.syllable_counter import count_syllables

# Initialize database
config = load_config()
database_url = f"sqlite:///{config.database.path}"
init_db(database_url)

# Test problem phrases word by word
phrases = [
    "writ of habeas corpus",
    "the road went out to nowhere",
    "I am not evil",
]

print("Word-by-word breakdown:\n")
print("=" * 70)

for phrase in phrases:
    print(f"\nPhrase: '{phrase}'")
    total = count_syllables(phrase)
    print(f"Total: {total} syllables")
    print("-" * 70)
