# HaikuBot v2.0

A modern IRC bot that monitors conversations across multiple servers, automatically detects 5 and 7 syllable phrases, and generates random haiku (5-7-5 format). Features a beautiful React-based web interface for browsing, voting, and statistics.

## Features

- 🤖 **Multi-Server IRC Support** - Connect to multiple IRC servers simultaneously
- 🎭 **Auto-Collection** - Passively monitors messages and collects 5/7 syllable phrases
- ✍️ **Manual Submission** - Authorized editors can submit lines with placement preferences
- 🎲 **Smart Generation** - Placement-aware algorithm for better narrative flow
- 🌐 **Modern Web Interface** - Browse, filter, and vote on haikus
- 📊 **Statistics Dashboard** - Track contributions and popular haikus
- 🔴 **Live Feed** - Real-time WebSocket updates when new haikus are generated
- 🗳️ **Voting System** - Community-driven haiku ranking
- 🔒 **Privacy Options** - Opt-out of auto-collection (stealth feature)

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI (web framework)
- SQLAlchemy (ORM)
- pydle (IRC client)
- pyphen + syllables (syllable counting)
- SQLite (database)

**Frontend:**
- React 18
- Vite (build tool)
- TailwindCSS (styling)
- React Query (data fetching)
- WebSocket (real-time updates)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Xafloc/HaikuBot-Python.git
cd HaikuBot-Python
```

2. **Set up Python environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure the bot:**
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your IRC servers, channels, and settings
```

4. **Initialize the database:**
```bash
python -m backend.main --config config.yaml
# The database will be created automatically on first run
```

5. **Set up the frontend (for development):**
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

6. **Run the bot:**
```bash
# In the project root, with venv activated:
python -m backend.main
```

The bot will:
- Connect to all configured IRC servers
- Start the web API on http://localhost:8000
- Begin monitoring channels and collecting lines

## Configuration

Edit `config.yaml` to customize:

```yaml
database:
  path: "./haiku.db"

bot:
  owner: "YourNickname"  # Your IRC nickname (admin access)
  web_url: "http://localhost:8000"
  trigger_prefix: "!"

servers:
  - name: "libera"
    host: "irc.libera.chat"
    port: 6697
    ssl: true
    nick: "HaikuBot"
    password: ""  # Optional
    channels: ["#haiku", "#bots"]

features:
  auto_collect: true
  allow_manual_submission: true

web:
  host: "0.0.0.0"
  port: 8000
```

## IRC Commands

### Public Commands (Anyone)

- `!haiku` - Generate random haiku
- `!haiku @username` - Generate using specific user's lines
- `!haiku #channel` - Generate from specific channel's lines
- `!haikustats` - Show bot statistics
- `!haikuvote <id>` - Upvote a generated haiku
- `!haikutop` - Show top voted haikus
- `!myhaiku` - Show your contributed lines
- `!mystats` - Show your statistics
- `!haikuhelp` - Display help

### Editor Commands (Authorized Users)

- `!haiku5 <text>` - Submit 5-syllable line
- `!haiku5 --first <text>` - Submit 5-syllable line (first position only)
- `!haiku5 --last <text>` - Submit 5-syllable line (last position only)
- `!haiku7 <text>` - Submit 7-syllable line

### Admin Commands (Bot Owner)

- `!haiku promote @username` - Grant editor privileges
- `!haiku demote @username` - Revoke editor privileges
- `!haiku editors` - List all editors

### Privacy Commands (Not Advertised)

- `!haiku optout` - Opt out of auto-collection
- `!haiku optin` - Opt back into auto-collection

## Web Interface

Access the web interface at http://localhost:8000

**Pages:**
- **Home** - Live feed and recent haikus with generation button
- **Browse** - Filter and paginate through all haikus
- **Statistics** - Global stats and contributor leaderboard
- **User Profile** - View individual user contributions

## API Documentation

The REST API is available at http://localhost:8000/api

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

### Key Endpoints

- `GET /api/haikus` - List haikus (with filters)
- `GET /api/haikus/{id}` - Get specific haiku
- `POST /api/haikus/generate` - Generate new haiku
- `POST /api/haikus/{id}/vote` - Vote for haiku
- `GET /api/stats` - Global statistics
- `GET /api/leaderboard` - Top contributors
- `GET /api/users/{username}/stats` - User statistics
- `WS /ws/live` - WebSocket live feed

## Production Deployment

### Build Frontend

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/` and will be served automatically by FastAPI.

### Using systemd (Linux)

1. Copy the service file:
```bash
sudo cp systemd/haikubot.service /etc/systemd/system/
```

2. Edit the service file with your paths:
```bash
sudo nano /etc/systemd/system/haikubot.service
```

3. Enable and start:
```bash
sudo systemctl enable haikubot
sudo systemctl start haikubot
sudo systemctl status haikubot
```

4. View logs:
```bash
sudo journalctl -u haikubot -f
```

### Using Docker (Alternative)

```bash
# Build image
docker build -t haikubot .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/haiku.db:/app/haiku.db \
  --name haikubot \
  haikubot
```

## Development

### Running Tests

```bash
# Backend tests
pytest backend/tests/

# Frontend tests (if configured)
cd frontend
npm test
```

### Code Style

```bash
# Python
black backend/
flake8 backend/

# JavaScript
cd frontend
npm run lint
```

## Migration from Perl Bot

If you have an existing Perl-based HaikuBot database:

1. The new schema is compatible with the old one
2. You may need to add new columns (server, channel, source, placement)
3. A migration script can be created to import old data

## Troubleshooting

**Bot won't connect to IRC:**
- Check SSL settings in config.yaml
- Verify firewall allows outbound connections on IRC ports
- Ensure nick isn't already taken

**Syllable counting inaccurate:**
- The syllable counter uses pyphen + syllables libraries
- Some words (proper nouns, acronyms) may be miscounted
- Consider adding manual corrections for common issues

**WebSocket not working:**
- Check CORS settings in config.yaml
- Verify firewall allows WebSocket connections
- Check browser console for errors

**No haikus generating:**
- Ensure database has enough lines (need 5-syl and 7-syl)
- Check logs for errors
- Verify IRC channels have activity

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[License TBD]

## Credits

- **Original Perl Bot**: Xafloc
- **Python Rewrite**: 2025
- **Haiku Format**: 5-7-5 syllable structure from Japanese poetry tradition

## Links

- [Project Documentation](PROJECT_PLAN.md)
- [AI Assistant Context](CLAUDE.md)
- IRC: Connect to see it in action!

---

**Built with ❤️ and Python**

