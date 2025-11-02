# Migrating Data from Version 1

This guide explains how to migrate data from the old Perl-based HaikuBot (v1) to the new Python version (v2).

## Overview

The migration script handles:
- ✅ Migrating individual lines (5 and 7 syllable phrases)
- ✅ Validating syllable counts with the new syllable counter
- ✅ Migrating generated haikus
- ✅ Migrating votes
- ✅ Migrating users with proper role mapping
- ✅ Adding missing metadata (server, channel, source)

## Schema Differences

### Old Schema (v1)
```
haiku table:
  - id, syllable, text, datetime, user_id, placement

generated_haiku table:
  - id, haiku (full text), datetime, user_id, votes

haiku_votes table:
  - haiku_id, user_id, datetime

users table:
  - id, username, authlevel (integer)
```

### New Schema (v2)
```
lines table:
  - id, text, syllable_count, server, channel, username,
    timestamp, source, placement, approved

generated_haikus table:
  - id, line1_id, line2_id, line3_id, full_text,
    generated_at, triggered_by, server, channel

votes table:
  - id, haiku_id, username, voted_at

users table:
  - id, username, role (string), opted_out, created_at, notes
```

## Migration Process

### 1. Prepare the Old Database

Place your old `haiku.db` file in the `olddata/` directory:
```bash
mkdir -p olddata
cp /path/to/old/haiku.db olddata/
```

### 2. Review What Will Be Migrated

The script will show you a summary before proceeding:
```bash
python backend/migrate_v1_data.py
```

You'll see:
- Count of lines, haikus, votes, and users in old database
- Default values that will be used (server, channel, source)

### 3. Handle Syllable Mismatches

The migration script validates syllable counts using the new counter. If there are mismatches, you'll be prompted for each one:

```
⚠️  Line #3: Syllable mismatch!
   Text: 'every good boy'
   Expected: 5, Actual: 4
   [u]se actual count, [s]kip this line, or [k]eep expected? (u/s/k):
```

Options:
- **u** - Use the actual count from the new syllable counter (recommended)
- **s** - Skip this line entirely (don't migrate it)
- **k** - Keep the expected count from old database (not recommended)

### 4. Review Results

After migration, you'll see a summary:
```
✅ Migration Complete!
Lines migrated:          8
Generated haikus:        3
Votes migrated:          1
Users migrated:          1
```

## Default Values Applied

The migration adds these defaults for missing fields:

| Field | Default Value | Reason |
|-------|---------------|--------|
| `server` | `darkscience` | Old bot only had one server |
| `channel` | `#haiku` | Primary channel for old bot |
| `source` | `manual` | All old data was manually curated |
| `placement` | `any` | Old placement=0 maps to 'any' |
| `approved` | `true` | All old data was approved |

## User Role Mapping

Old `authlevel` (integer) maps to new `role` (string):

| Old authlevel | New role |
|---------------|----------|
| 0 | public |
| 1 | editor |
| 2+ | admin |

## Troubleshooting

### "Could not find line" errors for generated haikus

If a generated haiku references a line that was skipped during migration (due to syllable mismatch), the haiku itself will also be skipped. You can:
1. Re-run migration and choose to migrate all lines (even with bad syllable counts)
2. Manually re-create the haiku later using the web interface

### Duplicate line errors

The new database has a unique constraint on line text. If you've already added some test lines, the migration will skip duplicates automatically.

### Need to re-run migration

If you need to start over:
```bash
# Backup current database
cp haiku.db haiku_backup.db

# Delete current database
rm haiku.db

# Restart the bot to create fresh database
python -m backend.main

# Run migration again
python backend/migrate_v1_data.py
```

## Post-Migration Steps

1. **Verify the data** - Browse the web interface to check lines and haikus
2. **Test syllable counter** - Check if any lines have incorrect counts
3. **Update user roles** - Use `!haiku promote @username` to adjust roles if needed
4. **Clean up test data** - Use `!haiku delete line <id>` to remove any test entries

## Notes

- Migration is **additive** - it doesn't delete existing data
- Old haiku IDs **may not match** new IDs (especially if some were skipped)
- Timestamps are preserved from the old database
- All migrated data is marked as `source='manual'` (manually curated)
