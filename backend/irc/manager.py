"""IRC manager for multi-server connections."""

import logging
import threading
from typing import Dict, List

from .bot import HaikuBot
from ..config import ServerConfig

logger = logging.getLogger(__name__)


class IRCManager:
    """Manages multiple IRC bot connections."""
    
    def __init__(self, servers: List[ServerConfig]):
        """Initialize IRC manager.
        
        Args:
            servers: List of server configurations
        """
        self.servers = servers
        self.bots: Dict[str, HaikuBot] = {}
        self.threads: List[threading.Thread] = []
        
        logger.info(f"IRC Manager initialized with {len(servers)} server(s)")
    
    def start_all(self):
        """Start all IRC bot connections in separate threads."""
        logger.info("Starting all IRC bots...")
        
        for server_config in self.servers:
            self.start_server(server_config)
        
        logger.info(f"Started {len(self.bots)} IRC bot(s)")
    
    def start_server(self, server_config: ServerConfig):
        """Start a bot for a specific server in a separate thread.
        
        Args:
            server_config: Server configuration
        """
        try:
            logger.info(f"Starting bot for server: {server_config.name}")
            
            # Create bot instance
            bot = HaikuBot(server_config, server_config.name)
            
            # Store bot reference
            self.bots[server_config.name] = bot
            
            # Start bot in a separate thread
            thread = threading.Thread(
                target=bot.start,
                name=f"IRC-{server_config.name}",
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            
            logger.info(f"[{server_config.name}] Bot thread started")
            
        except Exception as e:
            logger.error(f"Failed to start bot for {server_config.name}: {e}", exc_info=True)
    
    def stop_all(self):
        """Stop all IRC bot connections."""
        logger.info("Stopping all IRC bots...")
        
        for name, bot in self.bots.items():
            try:
                logger.info(f"Disconnecting bot: {name}")
                bot.die("Bot shutting down")
            except Exception as e:
                logger.error(f"Error disconnecting {name}: {e}")
        
        # Wait for threads to finish (with timeout)
        for thread in self.threads:
            thread.join(timeout=5.0)
        
        logger.info("All IRC bots stopped")
    
    def get_bot(self, server_name: str) -> HaikuBot:
        """Get a bot instance by server name.
        
        Args:
            server_name: Name of the server
            
        Returns:
            HaikuBot instance or None
        """
        return self.bots.get(server_name)
    
    def broadcast_message(self, message: str, channel: str = None):
        """Broadcast a message to all servers.
        
        Args:
            message: Message to broadcast
            channel: Optional channel name (broadcasts to all channels if not specified)
        """
        for name, bot in self.bots.items():
            try:
                if channel:
                    if channel in bot.channels:
                        bot.send_message(channel, message)
                else:
                    # Send to all channels this bot is in
                    for ch in bot.channels:
                        bot.send_message(ch, message)
            except Exception as e:
                logger.error(f"Error broadcasting to {name}: {e}")
