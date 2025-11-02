"""Main entry point for HaikuBot.

Runs IRC bots in threads and FastAPI web server.
"""

import asyncio
import logging
import sys
from pathlib import Path

import uvicorn

from .config import load_config, set_config
from .database import init_db
from .irc import IRCManager
from .api import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


class HaikuBotApplication:
    """Main application orchestrator."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = None
        self.irc_manager = None
        self.app = None
    
    def setup(self):
        """Setup application components."""
        logger.info("Setting up HaikuBot...")
        
        # Load configuration
        try:
            self.config = load_config(self.config_path)
            set_config(self.config)
            logger.info("Configuration loaded successfully")
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
        
        # Setup logging from config
        log_level = getattr(logging, self.config.logging.level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        
        # Add file handler if configured
        if self.config.logging.file:
            file_handler = logging.FileHandler(self.config.logging.file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logging.getLogger().addHandler(file_handler)
            logger.info(f"Logging to file: {self.config.logging.file}")
        
        # Initialize database
        database_url = f"sqlite:///{self.config.database.path}"
        init_db(database_url)
        logger.info("Database initialized")
        
        # Create IRC manager
        self.irc_manager = IRCManager(self.config.servers)
        logger.info("IRC manager created")
        
        # Create FastAPI app
        self.app = create_app(self.config)
        logger.info("FastAPI app created")
        
        logger.info("Setup complete!")
    
    def start_irc(self):
        """Start IRC bots in background threads."""
        logger.info("Starting IRC bots...")
        self.irc_manager.start_all()
    
    def stop_irc(self):
        """Stop IRC bots."""
        logger.info("Stopping IRC bots...")
        self.irc_manager.stop_all()
    
    def run(self):
        """Run the application."""
        self.setup()
        
        # Start IRC bots in background threads
        self.start_irc()
        
        # Give IRC bots time to connect
        import time
        time.sleep(3)
        
        # Configure uvicorn
        config = uvicorn.Config(
            self.app,
            host=self.config.web.host,
            port=self.config.web.port,
            log_level=self.config.logging.level.lower(),
            access_log=True
        )
        
        server = uvicorn.Server(config)
        
        # Run FastAPI server
        try:
            logger.info(f"Starting web server on {self.config.web.host}:{self.config.web.port}")
            server.run()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            # Cleanup
            logger.info("Shutting down...")
            self.stop_irc()
            logger.info("Shutdown complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="HaikuBot - IRC Haiku Bot")
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Create and run application
    app = HaikuBotApplication(config_path=args.config)
    
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
