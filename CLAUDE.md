# HaikuBot - AI Assistant Context

## Project Overview
HaikuBot is a modern Python-based IRC bot that monitors conversations across multiple IRC servers, automatically detects 5 and 7 syllable phrases, and generates random haiku (5-7-5 format). It features a React-based web interface for browsing, voting, and statistics.

This is a rewrite of an original Perl-based bot that successfully ran for years. The new version adds multi-server support, passive auto-collection, web interface, and modern architecture.

## Architecture

### High-Level Design
```
┌─────────────────────────────────────┐
│   Single Python Process             │
├─────────────────────────────────────┤
│  asyncio Event Loop                 │
│  ├─ IRC Client (server 1)           │
│  ├─ IRC Client (server 2)           │
│  ├─ IRC Client (server N...)        │
│  └─ FastAPI Web Server (:8000)      │
│                                     │
│  Shared SQLite Database             │
└─────────────────────────────────────┘
```

### Technology Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, pydle (IRC), pyphen/syllables
- **Frontend**: React 18, Vite, TailwindCSS, React Query, WebSocket
- **Database**: SQLite
- **Deployment**: Linux server with systemd or Docker

### Key Design Decisions

1. **Single Process Architecture**: IRC bots and FastAPI web server run in the same asyncio event loop, sharing database access without IPC complexity.

2. **Dual Collection System**:
   - **Auto-collection**: Passively monitors all IRC messages, detects 5/7 syllable phrases, stores with `source='auto'`
   - **Manual submission**: Authorized editors explicitly submit lines with `source='manual'`

3. **Smart Placement System**: 5-syllable lines can be marked for position preference:
   - `any` (default): Can be used in position 1 or 3
   - `first`: Only position 1
   - `last`: Only position 3
   - When generating, line 1 excludes `last`, line 3 excludes `first`

4. **Multi-Server Tracking**: Every line and haiku tracks origin server and channel for filtering and attribution.

## Database Schema

### Core Tables

**`lines`**: Individual 5 or 7 syllable phrases
- Primary storage for all collected/submitted lines
- Tracks: text, syllable_count, server, channel, username, timestamp, source, placement
- UNIQUE constraint on text (case-insensitive) to prevent duplicates

**`generated_haikus`**: Complete haikus (three lines combined)
- References three `lines` records (line1_id, line2_id, line3_id)
- Stores full assembled text for easy display
- Tracks who triggered generation and where

**`votes`**: Haiku upvotes
- One vote per username per haiku (UNIQUE constraint)
- Tracks timestamp for analytics

**`users`**: User authorization and preferences
- Roles: `public`, `editor`, `admin`
- `opted_out` flag for privacy (stealth feature)

**`servers`**: IRC server configurations
- Mirrors config.yaml but stored in DB for runtime access
- Can be managed via admin commands

## Features & Commands

### IRC Commands

**Public** (anyone can use):
- `!haiku` - Generate random haiku
- `!haiku @username` - Generate using specific user's lines
- `!haiku #channel` - Generate from specific channel
- `!haikustats` - Statistics
- `!haikuvote <id>` - Upvote haiku
- `!haikutop` - Top voted haikus
- `!myhaiku` / `!mystats` - Personal statistics

**Editor** (requires authorization):
- `!haiku5 <text>` - Submit 5-syllable line
- `!haiku5 --first <text>` - Submit with first-position preference
- `!haiku5 --last <text>` - Submit with last-position preference
- `!haiku7 <text>` - Submit 7-syllable line

**Admin** (bot owner only):
- `!haiku promote @username` - Grant editor privileges
- `!haiku demote @username` - Revoke editor privileges
- `!haiku editors` - List editors

**Privacy** (stealth, not advertised):
- `!haiku optout` - Opt out of auto-collection
- `!haiku optin` - Opt back in

### Web Interface Features
- Browse all generated haikus (paginated, filterable)
- Filter by server, channel, user, date
- Vote on haikus
- Real-time live feed (WebSocket)
- Statistics dashboard
- User profiles
- Generate haiku via web UI

## Configuration

**config.yaml** structure:
```yaml
database:
  path: "./haiku.db"

bot:
  owner: "AdminNickname"
  web_url: "https://your-domain.com"
  trigger_prefix: "!"

servers:
  - name: "libera"
    host: "irc.libera.chat"
    port: 6697
    ssl: true
    nick: "HaikuBot"
    channels: ["#haiku", "#bots"]

features:
  auto_collect: true
  allow_manual_submission: true

web:
  host: "0.0.0.0"
  port: 8000

logging:
  level: "INFO"
  file: "./haikubot.log"
```

## File Structure

```
HaikuBot/
├── backend/
│   ├── main.py                 # Entry point, orchestrates everything
│   ├── config.py               # YAML config loader
│   ├── database/
│   │   ├── db.py               # Database connection, session management
│   │   └── models.py           # SQLAlchemy models
│   ├── irc/
│   │   ├── bot.py              # pydle IRC bot implementation
│   │   ├── manager.py          # Multi-server connection manager
│   │   └── handlers.py         # Message/command handlers
│   ├── haiku/
│   │   ├── syllable_counter.py # Syllable detection
│   │   ├── generator.py        # Haiku generation logic
│   │   └── commands.py         # Command implementations
│   ├── api/
│   │   ├── routes.py           # REST API endpoints
│   │   └── websocket.py        # WebSocket live feed
│   └── utils/
│       └── auth.py             # Authorization helpers
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── api/                # API client
│   │   └── hooks/              # Custom hooks (WebSocket, etc.)
│   ├── package.json
│   └── vite.config.js
├── config.yaml                 # Main configuration
├── requirements.txt
├── PROJECT_PLAN.md            # Detailed project plan
└── README.md                  # Setup instructions
```

## Implementation Status

**Current Phase**: Building from scratch

**Completed**:
- [x] Project planning and architecture design
- [x] Documentation (PROJECT_PLAN.md, CLAUDE.md)

**In Progress**:
- [ ] Core backend implementation

**Pending**:
- [ ] IRC bot implementation
- [ ] Web API implementation
- [ ] Frontend implementation
- [ ] Testing and polish

## Key Algorithms

### Syllable Detection
Uses combination of:
- `pyphen` library (hyphenation-based)
- `syllables` library (dictionary-based)
- Fallback heuristics for edge cases

### Haiku Generation with Placement Logic
```python
# Simplified pseudocode
line1 = SELECT random FROM lines 
        WHERE syllable_count=5 
        AND placement != 'last'

line2 = SELECT random FROM lines 
        WHERE syllable_count=7

line3 = SELECT random FROM lines 
        WHERE syllable_count=5 
        AND placement != 'first'

haiku = f"{line1.text} / {line2.text} / {line3.text}"
```

### Authorization Check
```python
def can_submit(username):
    user = get_user(username)
    return user and user.role in ['editor', 'admin']
```

## Important Behaviors

1. **Auto-Collection Privacy**: 
   - Respects user opt-outs (check before storing)
   - Feature exists but not advertised to users
   - Bot owner aware of privacy considerations

2. **Duplicate Prevention**:
   - Lines table has UNIQUE constraint on text (case-insensitive)
   - INSERT ... WHERE NOT EXISTS pattern
   - Silently ignores duplicates

3. **Vote Limiting**:
   - One vote per username per haiku
   - UNIQUE constraint on (haiku_id, username)
   - Returns friendly message if already voted

4. **Multi-Server Isolation**:
   - Each line/haiku tagged with server and channel
   - Can filter generation by origin
   - Statistics can be per-server or global

5. **Trigger Prefix**:
   - Configurable (default `!`)
   - Commands always match: `^[trigger_prefix][command]`
   - Case-insensitive matching

## Development Notes

### Running Locally
```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python backend/main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

### Testing
- Unit tests in `backend/tests/`
- Test syllable counter accuracy
- Test haiku generation logic
- Test authorization logic
- Manual IRC testing in #bots channels

### Deployment
- Systemd service for production
- FastAPI serves both API and built frontend
- Single process, single SQLite file
- Logs to file and stdout

## Migration from Perl Bot

If migrating existing data:
1. Old schema: `haiku`, `generated_haiku`, `haiku_votes`, `users` tables
2. Import script needed to map old schema to new schema
3. Add server/channel metadata (default to original server)
4. Set `source='manual'` for old data (was manually curated)

## Common Issues & Solutions

**Issue**: Syllable counter inaccurate
- **Solution**: Use both pyphen and syllables, take consensus, log mismatches

**Issue**: Too many auto-collected lines flooding DB
- **Solution**: Add rate limiting per user, quality filters

**Issue**: Haiku generation produces weird results
- **Solution**: Add optional profanity filter, human review queue for auto-collected

**Issue**: IRC connection drops
- **Solution**: pydle has auto-reconnect, implement exponential backoff

**Issue**: WebSocket clients not receiving updates
- **Solution**: Check CORS, verify broadcast logic, test with simple client

## AI Assistant Guidelines

When working on this project:

1. **Maintain async patterns**: Everything runs in asyncio event loop
2. **Use SQLAlchemy properly**: Session management, avoid holding sessions across awaits
3. **IRC is stateful**: Track connection state, handle disconnects gracefully
4. **Placement logic is critical**: Test thoroughly, affects haiku quality
5. **Privacy matters**: Always check opt-out before auto-collecting
6. **Multi-server awareness**: Never assume single server, always track origin
7. **Frontend is fancy**: Use modern React patterns, TailwindCSS for styling
8. **Configuration-driven**: Most behavior configurable via config.yaml
9. **Logging is essential**: Log all IRC events, command executions, errors
10. **Error handling**: IRC commands should never crash bot, return friendly errors

## Contact

- **Original Bot Author**: Xafloc (Perl version)
- **Current Maintainer**: darren
- **Project Start**: October 2025

## Additional Resources

- See `PROJECT_PLAN.md` for detailed implementation phases
- See `README.md` for setup and deployment instructions (to be created)
- Original Perl code available for reference (in project history)

---

Last Updated: 2025-10-31

