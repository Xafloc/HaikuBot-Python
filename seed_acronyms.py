"""Seed common IRC/internet acronyms into the database.

This script populates the acronyms table with commonly used internet slang
that should be allowed in auto-collected haiku lines.

Run with: python seed_acronyms.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_session, Acronym, init_db
from backend.config import load_config, set_config

# Common IRC/internet acronyms with their syllable counts
# Format: (acronym, syllable_count, description)
COMMON_ACRONYMS = [
    # Very common internet slang
    ("lol", 3, "Laughing out loud"),
    ("omg", 3, "Oh my god"),
    ("wtf", 3, "What the f***"),
    ("lmao", 4, "Laughing my a** off"),
    ("rofl", 2, "Rolling on floor laughing"),
    ("brb", 3, "Be right back"),
    ("afk", 3, "Away from keyboard"),
    ("btw", 3, "By the way"),
    ("imo", 3, "In my opinion"),
    ("imho", 4, "In my humble opinion"),
    ("fyi", 3, "For your information"),
    ("tbh", 3, "To be honest"),
    ("irl", 3, "In real life"),
    ("jk", 2, "Just kidding"),

    # Technical (minimal - only extremely common)
    ("pc", 2, "Personal computer"),
    ("os", 2, "Operating system"),
    ("ui", 2, "User interface"),
    ("api", 3, "Application programming interface"),
    ("url", 3, "Uniform resource locator"),
    ("html", 4, "HyperText Markup Language"),
    ("wifi", 2, "Wireless fidelity"),

    # Time-based
    ("asap", 4, "As soon as possible"),
    ("eta", 3, "Estimated time of arrival"),

    # Common abbreviations
    ("aka", 3, "Also known as"),
    ("etc", 3, "Et cetera"),
    ("vs", 2, "Versus"),
]


def seed_acronyms():
    """Add acronyms to database."""
    print("Seeding acronyms...")

    added = 0
    skipped = 0

    with get_session() as session:
        for acronym_text, syllable_count, description in COMMON_ACRONYMS:
            # Check if already exists
            existing = session.query(Acronym).filter(
                Acronym.acronym == acronym_text.lower()
            ).first()

            if existing:
                print(f"  Skip: {acronym_text} (already exists)")
                skipped += 1
                continue

            # Add new acronym
            acronym = Acronym(
                acronym=acronym_text.lower(),
                syllable_count=syllable_count,
                description=description
            )
            session.add(acronym)
            print(f"  Add: {acronym_text} ({syllable_count} syllables) - {description}")
            added += 1

        session.commit()

    print(f"\nDone! Added {added} acronyms, skipped {skipped} existing.")


if __name__ == "__main__":
    # Load configuration
    try:
        config = load_config("config.yaml")
        set_config(config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Initialize database
    try:
        db_path = config.database.path
        database_url = f"sqlite:///{db_path}"
        init_db(database_url)
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

    seed_acronyms()
