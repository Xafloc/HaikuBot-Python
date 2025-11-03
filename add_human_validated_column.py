#!/usr/bin/env python3
"""Migration script to add human_validated column to lines table."""

import sqlite3
import sys

def migrate_database(db_path='./haiku.db'):
    """Add human_validated column to lines table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(lines)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'human_validated' in columns:
            print("✓ Column 'human_validated' already exists")
            return True

        # Add the column
        print("Adding 'human_validated' column to lines table...")
        cursor.execute("""
            ALTER TABLE lines
            ADD COLUMN human_validated BOOLEAN NOT NULL DEFAULT 0
        """)

        conn.commit()
        print("✓ Successfully added 'human_validated' column")
        return True

    except sqlite3.Error as e:
        print(f"✗ Error: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else './haiku.db'
    print(f"Migrating database: {db_path}")
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
