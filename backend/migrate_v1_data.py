"""Migrate data from version 1 (Perl bot) database to version 2 schema."""

import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.db import init_db, get_session_factory
from backend.database.models import Line, GeneratedHaiku, Vote, User
from backend.haiku.syllable_counter import count_syllables
from backend.config import load_config


# Configuration
OLD_DB_PATH = "olddata/haiku_orig.db"
DEFAULT_SERVER = "darkscience"
DEFAULT_CHANNEL = "#haiku"
SOURCE = "manual"  # All old data was manually curated
TRUST_OLD_COUNTS = True  # Trust old database syllable counts (manually curated)
SKIP_SYLLABLE_VALIDATION = False  # Set to True to skip syllable validation


def validate_syllables(text: str, expected: int) -> tuple[bool, int]:
    """Validate syllable count for a line.

    Returns:
        (is_valid, actual_count)
    """
    actual = count_syllables(text)
    return (actual == expected, actual)


def map_placement(old_placement: int) -> str:
    """Map old placement integer to new placement string.

    Old: 0 = any position
    New: 'any', 'first', 'last'
    """
    # Old Perl bot used 0 for any position
    # We'll default everything to 'any'
    return 'any'


def map_user_role(authlevel: int) -> str:
    """Map old authlevel to new role.

    Old: Integer (0 = public, higher = more privileges)
    New: 'public', 'editor', 'admin'
    """
    if authlevel >= 2:
        return 'admin'
    elif authlevel >= 1:
        return 'editor'
    else:
        return 'public'


def migrate_lines(old_conn, new_session, table_name='haiku', source_type='manual', should_validate_syllables=False):
    """Migrate lines from old database to new 'lines' table.

    Args:
        old_conn: SQLite connection to old database
        new_session: SQLAlchemy session for new database
        table_name: 'haiku' (manual) or 'quotehaiku' (auto-collected)
        source_type: 'manual' or 'auto'
        should_validate_syllables: Whether to validate syllable counts
    """
    print(f"\n=== Migrating {table_name.title()} Lines (source={source_type}) ===")

    cursor = old_conn.cursor()
    cursor.execute(f"SELECT id, syllable, text, datetime, user_id, placement FROM {table_name}")

    lines_migrated = 0
    lines_skipped = 0
    syllable_mismatches = []

    all_rows = cursor.fetchall()
    total_lines = len(all_rows)

    for idx, (old_id, syllable, text, timestamp, user_id, placement) in enumerate(all_rows, 1):
        # Show progress every 50 lines
        if idx % 50 == 0 or idx == total_lines:
            print(f"Progress: {idx}/{total_lines} lines processed...")

        # Only import if old database says it's 5 or 7 syllables
        if syllable not in [5, 7]:
            lines_skipped += 1
            continue

        # Validate syllables if requested
        if should_validate_syllables:
            is_valid, actual_count = validate_syllables(text, syllable)
            if not is_valid:
                syllable_mismatches.append({
                    'id': old_id,
                    'text': text,
                    'expected': syllable,
                    'actual': actual_count
                })
                # Skip if actual count is not 5 or 7
                if actual_count not in [5, 7]:
                    lines_skipped += 1
                    continue
                # Use actual count if it's still valid
                syllable = actual_count

        # Create new line
        new_line = Line(
            text=text,
            syllable_count=syllable,
            server=DEFAULT_SERVER,
            channel=DEFAULT_CHANNEL,
            username=user_id or "unknown",
            timestamp=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow(),
            source=source_type,
            placement=map_placement(placement) if syllable == 5 else None,
            approved=True
        )

        try:
            new_session.add(new_line)
            new_session.flush()  # Flush to catch duplicates immediately
            lines_migrated += 1
        except Exception as e:
            # Skip duplicates
            new_session.rollback()
            lines_skipped += 1
            continue

        # Commit every 100 lines to avoid huge transactions
        if lines_migrated % 100 == 0:
            new_session.commit()

    # Final commit
    new_session.commit()

    print(f"\n✓ Lines migrated: {lines_migrated}")
    print(f"⚠️  Lines skipped: {lines_skipped}")
    if syllable_mismatches:
        print(f"⚠️  Syllable mismatches found and fixed: {len(syllable_mismatches)}")
        if len(syllable_mismatches) <= 20:
            for m in syllable_mismatches:
                print(f"   - '{m['text'][:50]}...': expected {m['expected']}, got {m['actual']}")
        else:
            print(f"   (showing first 20 of {len(syllable_mismatches)} mismatches)")
            for m in syllable_mismatches[:20]:
                print(f"   - '{m['text'][:50]}...': expected {m['expected']}, got {m['actual']}")

    return lines_migrated, syllable_mismatches


def migrate_generated_haikus(old_conn, new_session):
    """Migrate generated haikus.

    Note: Old schema stores full text, not line IDs.
    We need to parse and match lines.
    """
    print("\n=== Migrating Generated Haikus ===")

    cursor = old_conn.cursor()
    cursor.execute("SELECT id, haiku, datetime, user_id FROM generated_haiku")

    haikus_migrated = 0
    haikus_skipped = 0

    all_haikus = cursor.fetchall()
    total_haikus = len(all_haikus)

    for idx, (old_id, haiku_text, timestamp, user_id) in enumerate(all_haikus, 1):
        # Show progress
        if idx % 25 == 0 or idx == total_haikus:
            print(f"Progress: {idx}/{total_haikus} haikus processed...")
        # Parse haiku text (format: "line1 / line2 / line3")
        parts = [p.strip() for p in haiku_text.split(' / ')]

        if len(parts) != 3:
            haikus_skipped += 1
            continue

        # Try to find matching line IDs in new database
        line_ids = []
        for i, line_text in enumerate(parts):
            line = new_session.query(Line).filter(Line.text == line_text).first()
            if not line:
                line_ids = None
                break
            line_ids.append(line.id)

        if not line_ids:
            haikus_skipped += 1
            continue

        # Create new generated haiku
        new_haiku = GeneratedHaiku(
            line1_id=line_ids[0],
            line2_id=line_ids[1],
            line3_id=line_ids[2],
            full_text=haiku_text,
            generated_at=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow(),
            triggered_by=user_id or "unknown",
            server=DEFAULT_SERVER,
            channel=DEFAULT_CHANNEL
        )

        new_session.add(new_haiku)
        haikus_migrated += 1

    new_session.commit()

    print(f"\n✓ Haikus migrated: {haikus_migrated}")
    print(f"⚠️  Haikus skipped: {haikus_skipped}")

    return haikus_migrated


def migrate_votes(old_conn, new_session):
    """Migrate votes."""
    print("\n=== Migrating Votes ===")

    cursor = old_conn.cursor()
    cursor.execute("SELECT haiku_id, user_id, datetime FROM haiku_votes")

    votes_migrated = 0
    votes_skipped = 0

    for haiku_id, user_id, timestamp in cursor.fetchall():
        # Check if haiku exists in new database
        haiku = new_session.query(GeneratedHaiku).filter(GeneratedHaiku.id == haiku_id).first()
        if not haiku:
            votes_skipped += 1
            continue

        # Create new vote
        new_vote = Vote(
            haiku_id=haiku_id,
            username=user_id or "unknown",
            voted_at=datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()
        )

        new_session.add(new_vote)
        votes_migrated += 1

    new_session.commit()

    print(f"\n✓ Votes migrated: {votes_migrated}")
    print(f"⚠️  Votes skipped: {votes_skipped}")

    return votes_migrated


def migrate_users(old_conn, new_session):
    """Migrate users."""
    print("\n=== Migrating Users ===")

    cursor = old_conn.cursor()
    cursor.execute("SELECT id, username, authlevel FROM users")

    users_migrated = 0

    for old_id, username, authlevel in cursor.fetchall():
        # Check if user already exists
        existing = new_session.query(User).filter(User.username == username).first()
        if existing:
            continue

        # Create new user
        new_user = User(
            username=username,
            role=map_user_role(authlevel),
            opted_out=False,
            created_at=datetime.utcnow()
        )

        new_session.add(new_user)
        users_migrated += 1

    new_session.commit()

    print(f"\n✓ Users migrated: {users_migrated}")

    return users_migrated


def main():
    """Run the migration."""
    parser = argparse.ArgumentParser(description='Migrate HaikuBot v1 data to v2')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("=" * 60)
    print("HaikuBot v1 → v2 Data Migration")
    print("=" * 60)

    # Check if old database exists
    if not Path(OLD_DB_PATH).exists():
        print(f"❌ Error: Old database not found at {OLD_DB_PATH}")
        sys.exit(1)

    # Initialize new database
    print("📂 Initializing new database...")
    config = load_config("config.yaml")
    database_url = f"sqlite:///{config.database.path}"
    init_db(database_url)

    # Connect to old database
    print(f"📂 Opening old database: {OLD_DB_PATH}")
    old_conn = sqlite3.connect(OLD_DB_PATH)

    # Get new database session
    print("📂 Creating database session")
    SessionLocal = get_session_factory()
    new_session = SessionLocal()

    try:
        # Show summary of old data
        cursor = old_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM haiku")
        old_manual_lines = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM quotehaiku")
        old_auto_lines = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM generated_haiku")
        old_haikus = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM haiku_votes")
        old_votes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        old_users = cursor.fetchone()[0]

        print(f"\n📊 Old Database Summary:")
        print(f"   Manual Lines (haiku):        {old_manual_lines}")
        print(f"   Auto Lines (quotehaiku):     {old_auto_lines}")
        print(f"   Total Lines:                 {old_manual_lines + old_auto_lines}")
        print(f"   Generated Haikus:            {old_haikus}")
        print(f"   Votes:                       {old_votes}")
        print(f"   Users:                       {old_users}")

        # Confirm migration
        print("\n⚠️  Warning: This will import data into your current database.")
        print(f"   Server will be set to: {DEFAULT_SERVER}")
        print(f"   Channel will be set to: {DEFAULT_CHANNEL}")
        print(f"   Manual lines: source='manual', trust old syllable counts")
        print(f"   Auto lines: source='auto', validate syllables")

        if not args.yes:
            print("\n❌ Use --yes flag to confirm migration")
            print("   Example: python backend/migrate_v1_data.py --yes")
            return

        print("\n✅ Starting migration...")

        # Run migrations
        # 1. Migrate manual lines (trust old counts)
        manual_lines_count, manual_mismatches = migrate_lines(
            old_conn, new_session,
            table_name='haiku',
            source_type='manual',
            should_validate_syllables=False
        )

        # 2. Migrate auto-collected lines (validate syllables)
        auto_lines_count, auto_mismatches = migrate_lines(
            old_conn, new_session,
            table_name='quotehaiku',
            source_type='auto',
            should_validate_syllables=True
        )

        total_lines = manual_lines_count + auto_lines_count
        all_mismatches = manual_mismatches + auto_mismatches

        haikus_count = migrate_generated_haikus(old_conn, new_session)
        votes_count = migrate_votes(old_conn, new_session)
        users_count = migrate_users(old_conn, new_session)

        # Summary
        print("\n" + "=" * 60)
        print("✅ Migration Complete!")
        print("=" * 60)
        print(f"Manual lines migrated:   {manual_lines_count}")
        print(f"Auto lines migrated:     {auto_lines_count}")
        print(f"Total lines migrated:    {total_lines}")
        print(f"Generated haikus:        {haikus_count}")
        print(f"Votes migrated:          {votes_count}")
        print(f"Users migrated:          {users_count}")

        if all_mismatches:
            print(f"\n⚠️  {len(all_mismatches)} syllable mismatches were found and fixed:")
            if len(all_mismatches) <= 20:
                for mismatch in all_mismatches:
                    print(f"   - '{mismatch['text']}': expected {mismatch['expected']}, got {mismatch['actual']}")
            else:
                print(f"   (showing first 20 of {len(all_mismatches)} mismatches)")
                for mismatch in all_mismatches[:20]:
                    print(f"   - '{mismatch['text']}': expected {mismatch['expected']}, got {mismatch['actual']}")

    finally:
        old_conn.close()
        new_session.close()


if __name__ == "__main__":
    main()
