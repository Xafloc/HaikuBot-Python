# HaikuBot Quick Start Guide

Get HaikuBot running in 5 minutes!

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed (for frontend)
- Git installed

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# Clone and setup
git clone https://github.com/yourusername/haikubot.git
cd haikubot
./setup.sh

# Edit configuration
nano config.yaml  # or use your favorite editor

# Run the bot
source venv/bin/activate
python -m backend.main
```

### Option 2: Manual Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/haikubot.git
cd haikubot

# 2. Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp config.yaml.example config.yaml
nano config.yaml  # Edit with your settings

# 4. Setup Frontend (optional, for development)
cd frontend
npm install
cd ..

# 5. Run
python -m backend.main
```

## Minimal Configuration

Edit `config.yaml`:

```yaml
database:
  path: "./haiku.db"

bot:
  owner: "YourIRCNickname"  # CHANGE THIS
  web_url: "http://localhost:8000"
  trigger_prefix: "!"

servers:
  - name: "libera"
    host: "irc.libera.chat"
    port: 6697
    ssl: true
    nick: "HaikuBot"           # CHANGE THIS if needed
    password: ""               # Add if required
    channels: ["#test"]        # CHANGE THIS

features:
  auto_collect: true
  allow_manual_submission: true

web:
  host: "0.0.0.0"
  port: 8000
```

## First Run

```bash
# Activate virtual environment
source venv/bin/activate

# Start the bot
python -m backend.main
```

You should see:
```
INFO - Setting up HaikuBot...
INFO - Configuration loaded successfully
INFO - Database initialized
INFO - IRC Manager created
INFO - FastAPI app created
INFO - [libera] Connected to IRC server
INFO - Starting web server on 0.0.0.0:8000
```

## Accessing the Bot

### IRC

Connect to your IRC server and join the same channel:
```
!haiku          # Generate a random haiku (won't work until you have lines)
!haikuhelp      # Show help
!haikustats     # Show statistics
```

### Web Interface

Open http://localhost:8000 in your browser

### API

Visit http://localhost:8000/docs for interactive API documentation

## Getting Started with Content

The bot needs lines to generate haikus. You have two options:

### 1. Auto-Collection (Passive)

Just let people chat! The bot will automatically collect 5 and 7 syllable messages.

Example messages that will be collected:
- "The rain falls softly" (5 syllables)
- "Cherry blossoms bloom tonight" (7 syllables)
- "Winter wind blows cold" (5 syllables)

### 2. Manual Submission (Active)

Promote yourself to editor first:

As the bot owner, you're automatically an admin. Promote yourself to editor:
```
!haiku promote @YourNickname
```

Then submit lines:
```
!haiku5 The moon shines so bright
!haiku7 I watch the stars dance above me
!haiku5 A peaceful summer night
```

Generate a haiku:
```
!haiku
```

## Testing Locally

Want to test without connecting to real IRC servers?

1. Comment out the IRC servers in `config.yaml`
2. Manually add some lines to the database:

```bash
python3
>>> from backend.database import init_db, get_session, Line
>>> from datetime import datetime
>>> init_db("sqlite:///haiku.db")
>>> with get_session() as session:
...     line1 = Line(text="The rain falls softly", syllable_count=5, server="test", 
...                  channel="#test", username="TestUser", timestamp=datetime.utcnow(),
...                  source="manual", placement="any", approved=True)
...     line2 = Line(text="Cherry blossoms bloom tonight", syllable_count=7, server="test",
...                  channel="#test", username="TestUser", timestamp=datetime.utcnow(),
...                  source="manual", placement=None, approved=True)
...     line3 = Line(text="Winter wind blows cold", syllable_count=5, server="test",
...                  channel="#test", username="TestUser", timestamp=datetime.utcnow(),
...                  source="manual", placement="any", approved=True)
...     session.add_all([line1, line2, line3])
>>> quit()
```

3. Visit http://localhost:8000 and click "Generate New Haiku"

## Common Issues

### "No module named 'backend'"

Make sure you're running from the project root and venv is activated:
```bash
cd /path/to/haikubot
source venv/bin/activate
python -m backend.main
```

### "Configuration file not found"

Create config.yaml from the example:
```bash
cp config.yaml.example config.yaml
```

### "Not enough lines to generate haiku"

You need at least:
- 1 line with 5 syllables
- 1 line with 7 syllables  
- 1 more line with 5 syllables

Let people chat, or manually submit lines with `!haiku5` and `!haiku7`

### Port 8000 already in use

Change the port in config.yaml:
```yaml
web:
  port: 8080  # or any other available port
```

## Next Steps

1. **Read the full documentation**: See [README.md](README.md)
2. **Understand the project**: See [PROJECT_PLAN.md](PROJECT_PLAN.md)
3. **Deploy to production**: See README.md deployment section
4. **Customize**: Edit templates, add features, etc.

## Getting Help

- Check logs: `tail -f haikubot.log`
- Read documentation: README.md and PROJECT_PLAN.md
- Check IRC connection: Are you connected? Are you in the right channels?
- Check database: Does haiku.db exist? Does it have lines?

## Development Mode

Run backend and frontend separately:

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python -m backend.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Visit http://localhost:5173
```

Frontend will proxy API requests to backend at http://localhost:8000

---

Happy haiku generating! 俳句 🎋

