#!/usr/bin/env python3
"""Populate the acronyms table with common internet/IRC acronyms."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import init_db, get_session, Acronym
from backend.config import load_config


# Common internet acronyms and their syllable counts
# Format: (acronym, syllable_count, description)
COMMON_ACRONYMS = [
    # 2 letters - NOTE: ok removed because it's a common English word
    ("gg", 2, "good game"),
    ("wp", 2, "well played"),
    ("gl", 2, "good luck"),
    ("hf", 2, "have fun"),
    ("ty", 2, "thank you"),
    ("np", 2, "no problem"),
    ("nm", 2, "not much / nevermind"),
    ("ic", 2, "I see"),

    # 3 letters (usually 3 syllables when pronounced as letters)
    ("lol", 3, "laugh out loud"),
    ("brb", 3, "be right back"),
    ("afk", 3, "away from keyboard"),
    ("omg", 3, "oh my god"),
    ("wtf", 5, "what the f***"),
    ("fyi", 3, "for your information"),
    ("imo", 3, "in my opinion"),
    ("tbh", 3, "to be honest"),
    ("idk", 3, "I don't know"),
    ("irl", 3, "in real life"),
    ("btw", 5, "by the way"),
    ("tho", 3, "though"),
    ("rip", 3, "rest in peace"),
    ("eta", 3, "estimated time of arrival"),
    ("asap", 4, "as soon as possible"),

    # 4+ letters
    ("imho", 4, "in my humble opinion"),
    ("rofl", 4, "rolling on floor laughing"),
    ("lmao", 4, "laughing my a** off"),
    ("gtfo", 4, "get the f*** out"),
    ("stfu", 4, "shut the f*** up"),
    ("nsfw", 6, "not safe for work"),
    ("iirc", 4, "if I recall correctly"),
    ("afaik", 5, "as far as I know"),
    ("roflmao", 7, "rolling on floor laughing my a** off"),

    # Gaming specific
    ("ez", 2, "easy"),
    ("op", 2, "overpowered"),
    ("noob", 1, "newbie/inexperienced player"),
    ("pwn", 1, "own/dominate"),

    # Social media / texting
    ("dm", 2, "direct message"),
    ("pm", 2, "private message"),
    ("rt", 2, "retweet"),
    ("tl", 2, "timeline"),
    ("fb", 2, "Facebook"),
    ("ig", 2, "Instagram"),
    ("sm", 2, "social media"),

    # Technical
    ("api", 3, "application programming interface"),
    ("cpu", 3, "central processing unit"),
    ("gpu", 3, "graphics processing unit"),
    ("ram", 1, "random access memory"),
    ("url", 3, "uniform resource locator"),
    ("html", 4, "hypertext markup language"),
    ("css", 3, "cascading style sheets"),
    ("sql", 3, "structured query language"),
    ("json", 2, "JavaScript object notation"),
    ("xml", 3, "extensible markup language"),
    ("ssh", 3, "secure shell"),
    ("ftp", 3, "file transfer protocol"),
    ("http", 4, "hypertext transfer protocol"),
    ("https", 5, "hypertext transfer protocol secure"),

    # IRC specific
    ("bot", 1, "robot/automated user"),
    ("chan", 1, "channel"),
    ("nick", 1, "nickname"),
    ("ping", 1, "connection test"),
    ("pong", 1, "ping response"),
    ("ctcp", 4, "client-to-client protocol"),

    # Time/date - NOTE: am/pm/ok removed because they're common English words
    ("est", 3, "eastern standard time"),
    ("pst", 3, "pacific standard time"),
    ("utc", 3, "coordinated universal time"),
    ("gmt", 3, "Greenwich mean time"),
]


def populate_acronyms(recreate_table: bool = False):
    """Populate the acronyms table with common internet acronyms.

    Args:
        recreate_table: If True, drop and recreate the table before populating
    """
    # Load config and initialize database
    config = load_config()
    database_url = f"sqlite:///{config.database.path}"
    init_db(database_url)

    if recreate_table:
        print("Recreating acronyms table...")
        from backend.database.models import Base
        from backend.database.db import get_db
        engine = get_db()

        # Drop and recreate just the acronyms table
        Acronym.__table__.drop(engine, checkfirst=True)
        Acronym.__table__.create(engine, checkfirst=True)
        print("Table recreated.")

    # Populate acronyms
    with get_session() as session:
        added = 0
        skipped = 0
        seen = set()  # Track what we've added in this run

        for acronym, syllables, description in COMMON_ACRONYMS:
            acronym_lower = acronym.lower()

            # Skip if we've already seen this acronym in this run
            if acronym_lower in seen:
                print(f"  Warning: Duplicate in list - {acronym_lower}")
                skipped += 1
                continue

            # Check if already exists in database
            existing = session.query(Acronym).filter(
                Acronym.acronym == acronym_lower
            ).first()

            if existing:
                skipped += 1
                continue

            # Add new acronym
            new_acronym = Acronym(
                acronym=acronym_lower,
                syllable_count=syllables,
                description=description
            )
            session.add(new_acronym)
            seen.add(acronym_lower)
            added += 1

        session.commit()

        print(f"\nAcronym population complete:")
        print(f"  Added: {added}")
        print(f"  Skipped (already exists or duplicates): {skipped}")
        print(f"  Total in database: {session.query(Acronym).count()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate acronyms table")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate the table before populating"
    )

    args = parser.parse_args()

    print("Populating acronyms table...")
    populate_acronyms(recreate_table=args.recreate)
    print("Done!")
