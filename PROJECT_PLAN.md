# HaikuBot Project Plan

## Overview
A modern IRC bot that monitors conversations across multiple servers, collects 5 and 7 syllable messages, and generates random haiku. Features a React-based web interface for browsing, voting, and statistics.

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **IRC Client**: pydle (async, multi-server support)
- **Database**: SQLite with SQLAlchemy ORM
- **Syllable Detection**: pyphen + syllables libraries
- **Config**: PyYAML
- **Validation**: Pydantic

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **Data Fetching**: React Query (TanStack Query)
- **Real-time**: WebSocket client
- **Routing**: React Router

### Deployment
- **Target**: Linux server
- **Process Management**: systemd service
- **Alternative**: Docker container

---

## Core Features

### 1. Dual Collection System
- **Auto-collection**: Passively monitors all IRC messages, detects 5 or 7 syllable phrases, stores automatically
- **Manual submission**: Authorized editors can explicitly submit lines via commands
- Both types stored in same database with `source` field differentiation

### 2. Multi-Server Support
- Connect to multiple IRC servers simultaneously
- Track metadata: server name, channel, username, timestamp
- Per-server configuration (host, port, SSL, channels, nick)

### 3. Haiku Generation Algorithm
```
Line 1 (5 syllables): SELECT WHERE placement != 'last'
Line 2 (7 syllables): SELECT all 7-syllable lines
Line 3 (5 syllables): SELECT WHERE placement != 'first'
```

### 4. Placement System (5-syllable lines only)
- `any` (default): Can be used in position 1 or 3
- `first`: Only used in position 1
- `last`: Only used in position 3
- 7-syllable lines have no placement restrictions (always position 2)

### 5. Authorization Levels
- **Public**: Anyone can trigger haiku generation, vote, view stats
- **Editor**: Can manually submit/edit lines (promoted by admin)
- **Admin**: Can promote/demote editors, manage bot

### 6. Privacy Features
- Users can opt-out of auto-collection (stealth feature, not advertised)
- Opt-out/opt-in tracked per username
- Respects privacy flags during collection

### 7. Web Interface
- Browse all generated haikus (paginated, filterable)
- Filter by server, channel, user, date range
- Vote on haikus
- Real-time live feed of new haikus (WebSocket)
- Statistics dashboard
- User profiles showing contributions
- Generate haiku via web UI

---

## Database Schema

### `lines` Table
Stores individual 5 and 7 syllable lines
```sql
id                  INTEGER PRIMARY KEY
text                TEXT NOT NULL
syllable_count      INTEGER NOT NULL (5 or 7)
server              TEXT NOT NULL
channel             TEXT NOT NULL
username            TEXT NOT NULL
timestamp           DATETIME NOT NULL
source              TEXT NOT NULL ('auto' or 'manual')
placement           TEXT ('any', 'first', 'last', NULL for 7-syl)
approved            BOOLEAN DEFAULT TRUE
UNIQUE(text COLLATE NOCASE)
```

### `generated_haikus` Table
Stores complete generated haikus
```sql
id                  INTEGER PRIMARY KEY
line1_id            INTEGER REFERENCES lines(id)
line2_id            INTEGER REFERENCES lines(id)
line3_id            INTEGER REFERENCES lines(id)
full_text           TEXT NOT NULL
generated_at        DATETIME NOT NULL
triggered_by        TEXT NOT NULL
server              TEXT NOT NULL
channel             TEXT NOT NULL
```

### `votes` Table
Tracks haiku upvotes
```sql
id                  INTEGER PRIMARY KEY
haiku_id            INTEGER REFERENCES generated_haikus(id)
username            TEXT NOT NULL
voted_at            DATETIME NOT NULL
UNIQUE(haiku_id, username)
```

### `users` Table
User authorization and preferences
```sql
id                  INTEGER PRIMARY KEY
username            TEXT UNIQUE NOT NULL
role                TEXT NOT NULL ('public', 'editor', 'admin')
opted_out           BOOLEAN DEFAULT FALSE
created_at          DATETIME NOT NULL
notes               TEXT
```

### `servers` Table
IRC server configurations
```sql
id                  INTEGER PRIMARY KEY
name                TEXT UNIQUE NOT NULL
host                TEXT NOT NULL
port                INTEGER NOT NULL
ssl                 BOOLEAN NOT NULL
nick                TEXT NOT NULL
password            TEXT
channels            TEXT NOT NULL (JSON array)
enabled             BOOLEAN DEFAULT TRUE
```

---

## IRC Commands

### Public Commands (Anyone)
- `!haiku` - Generate random haiku
- `!haiku @username` - Generate using specific user's lines
- `!haiku #channel` - Generate from specific channel's lines
- `!haikustats` - Show bot statistics
- `!haikuvote <id>` - Upvote a generated haiku
- `!haikutop [N]` - Show top N voted haikus (default 5)
- `!myhaiku` - Show your contributed lines
- `!mystats` - Show your personal statistics
- `!haikuhelp` - Display help information

### Editor Commands (Authorized Users)
- `!haiku5 <text>` - Submit 5-syllable line (any placement)
- `!haiku5 --first <text>` - Submit 5-syllable line (first position only)
- `!haiku5 --last <text>` - Submit 5-syllable line (last position only)
- `!haiku7 <text>` - Submit 7-syllable line

### Admin Commands (Bot Owner)
- `!haiku promote @username` - Grant editor privileges
- `!haiku demote @username` - Revoke editor privileges
- `!haiku editors` - List all editors
- `!haiku ban @username` - Ban user from auto-collection
- `!haiku unban @username` - Unban user

### Privacy Commands (Stealth - Not Advertised)
- `!haiku optout` - Opt out of auto-collection
- `!haiku optin` - Opt back into auto-collection

---

## API Endpoints

### REST API

**Haikus**
- `GET /api/haikus` - List haikus (paginated, filterable)
- `GET /api/haikus/{id}` - Get specific haiku with details
- `GET /api/haikus/random` - Get random haiku
- `POST /api/haikus/generate` - Generate new haiku (returns JSON)
- `POST /api/haikus/{id}/vote` - Vote for a haiku

**Lines**
- `GET /api/lines` - List all lines (paginated, filterable)
- `GET /api/lines/stats` - Get line statistics

**Users**
- `GET /api/users/{username}/haikus` - Get user's haikus
- `GET /api/users/{username}/lines` - Get user's contributed lines
- `GET /api/users/{username}/stats` - Get user statistics

**Statistics**
- `GET /api/stats` - Global statistics
- `GET /api/stats/servers` - Per-server statistics
- `GET /api/stats/channels` - Per-channel statistics
- `GET /api/stats/leaderboard` - User leaderboard

**WebSocket**
- `WS /ws/live` - Real-time haiku generation feed

---

## Configuration File (config.yaml)

```yaml
database:
  path: "./haiku.db"

bot:
  owner: "YourNickname"
  web_url: "https://your-domain.com"
  trigger_prefix: "!"
  
servers:
  - name: "libera"
    host: "irc.libera.chat"
    port: 6697
    ssl: true
    nick: "HaikuBot"
    password: ""
    channels: ["#haiku", "#bots"]
    
  - name: "darkscience"
    host: "irc.darkscience.net"
    port: 6697
    ssl: true
    nick: "HaikuBot"
    password: ""
    channels: ["#haiku"]

features:
  auto_collect: true
  allow_manual_submission: true
  
web:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["http://localhost:5173"]  # Vite dev server

logging:
  level: "INFO"
  file: "./haikubot.log"
```

---

## Implementation Phases

### Phase 1: Core Backend ✓
1. Project structure setup
2. Database models (SQLAlchemy)
3. Configuration loader
4. Syllable counter implementation
5. Haiku generator logic
6. Basic unit tests

### Phase 2: IRC Bot ✓
1. pydle IRC client setup
2. Multi-server connection manager
3. Passive message monitoring
4. Auto-collection with syllable detection
5. Command parser and router
6. Command handlers (public, editor, admin)
7. Authorization middleware

### Phase 3: Web API ✓
1. FastAPI application setup
2. REST endpoint implementation
3. WebSocket live feed
4. CORS configuration
5. Request/response validation
6. Error handling

### Phase 4: Frontend ✓
1. React + Vite project scaffold
2. TailwindCSS setup
3. Component library (HaikuCard, Stats, etc.)
4. Pages (Home, Browse, Stats, User Profile)
5. API integration with React Query
6. WebSocket integration for live feed
7. Responsive design
8. Voting UI

### Phase 5: Integration & Polish ✓
1. Connect IRC bot + FastAPI + Frontend
2. Comprehensive error handling
3. Logging throughout
4. README with setup instructions
5. systemd service file
6. Docker configuration (optional)
7. Migration from old Perl bot (data import script)

---

## Project Structure

```
HaikuBot/
├── backend/
│   ├── main.py                 # Entry point, orchestrates IRC + FastAPI
│   ├── config.py               # Configuration loader (YAML)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py               # Database connection, session management
│   │   └── models.py           # SQLAlchemy models (Line, Haiku, Vote, User, Server)
│   ├── irc/
│   │   ├── __init__.py
│   │   ├── bot.py              # pydle IRC bot class
│   │   ├── manager.py          # Multi-server connection manager
│   │   └── handlers.py         # Message handlers (monitor, commands)
│   ├── haiku/
│   │   ├── __init__.py
│   │   ├── syllable_counter.py # Syllable detection logic
│   │   ├── generator.py        # Haiku generation with placement logic
│   │   └── commands.py         # IRC command implementations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # REST API endpoints
│   │   └── websocket.py        # WebSocket handlers
│   ├── utils/
│   │   ├── __init__.py
│   │   └── auth.py             # Authorization helpers
│   └── tests/
│       └── test_*.py
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── HaikuCard.jsx
│   │   │   ├── HaikuFeed.jsx
│   │   │   ├── Stats.jsx
│   │   │   ├── Filters.jsx
│   │   │   └── Navigation.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Browse.jsx
│   │   │   ├── Statistics.jsx
│   │   │   └── UserProfile.jsx
│   │   ├── api/
│   │   │   └── client.js       # API client functions
│   │   └── hooks/
│   │       └── useWebSocket.js # WebSocket hook
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── config.yaml                 # Main configuration
├── requirements.txt            # Python dependencies
├── .gitignore
├── README.md                   # Setup and deployment guide
├── PROJECT_PLAN.md            # This file
├── CLAUDE.md                  # AI assistant context
└── systemd/
    └── haikubot.service       # systemd service file
```

---

## Deployment

### Linux Server Deployment

1. **Install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cd frontend && npm install && npm run build
   ```

2. **Configure**:
   - Copy `config.yaml.example` to `config.yaml`
   - Edit IRC servers, credentials, channels
   - Set bot owner nickname

3. **Initialize database**:
   ```bash
   python -m backend.database.init_db
   ```

4. **Run manually** (testing):
   ```bash
   python backend/main.py
   ```

5. **Install as systemd service**:
   ```bash
   sudo cp systemd/haikubot.service /etc/systemd/system/
   sudo systemctl enable haikubot
   sudo systemctl start haikubot
   ```

### Docker Deployment (Alternative)

```bash
docker build -t haikubot .
docker run -d -p 8000:8000 -v ./config.yaml:/app/config.yaml haikubot
```

---

## Migration from Perl Bot

Create data import script to migrate existing data:

```python
# scripts/import_perl_data.py
# - Connect to old haiku.db
# - Import haiku table → lines table (map fields)
# - Import generated_haiku table
# - Import haiku_votes table
# - Import users table
# - Set appropriate server/channel (from config or default)
```

---

## Future Enhancements

- [ ] Discord bot integration (same backend)
- [ ] Markov chain haiku generation (experimental mode)
- [ ] Image export (haiku as pretty image for sharing)
- [ ] RSS feed of new haikus
- [ ] Email digest (daily top haiku)
- [ ] Admin web panel for moderation
- [ ] Natural language queries ("show me haikus about cats")
- [ ] Multi-language support (beyond English)
- [ ] Rate limiting and anti-spam measures
- [ ] Haiku themes/categories (auto-tag by content)

---

## Notes

- All IRC command trigger prefixes are configurable via `config.yaml`
- SQLite is used for simplicity; can migrate to PostgreSQL for scale
- Frontend is served as static files by FastAPI (production mode)
- Development: Frontend runs on Vite dev server (port 5173), backend on 8000
- WebSocket updates are broadcast to all connected clients
- Syllable counter may have accuracy issues with proper nouns, acronyms
- Placement system ensures haikus have better narrative flow
- Auto-collection respects opt-outs and can be globally disabled

---

## Success Metrics

- Successful multi-server IRC connection
- Accurate syllable detection (>90%)
- Haiku generation with proper placement logic
- Web interface loads and displays haikus
- Real-time updates via WebSocket working
- Vote system prevents duplicates
- Authorization properly restricts editor commands
- Can handle 100+ messages/minute across servers
- Web UI responsive on mobile devices

---

## Contact & Ownership

- **Original Perl Bot**: Written by Xafloc
- **Python Rewrite**: 2025
- **License**: TBD
- **Repository**: TBD

