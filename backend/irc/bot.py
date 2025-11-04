"""IRC bot implementation using irc library."""

import logging
import ssl
import irc.bot
import irc.connection
import irc.strings
from datetime import datetime

from ..config import get_config
from ..database import get_session, Line, User
from ..haiku import count_syllables, validate_line_for_auto_collection
from .commands import CommandHandler

logger = logging.getLogger(__name__)


class HaikuBot(irc.bot.SingleServerIRCBot):
    """HaikuBot IRC client.
    
    Handles IRC connections, monitors messages for auto-collection,
    and processes commands.
    """
    
    def __init__(self, server_config, server_name: str):
        """Initialize the bot.
        
        Args:
            server_config: Server configuration object
            server_name: Name of the server this bot is connected to
        """
        self.server_name = server_name
        self.server_config = server_config
        self.config = get_config()

        # Create server spec
        server_spec = irc.bot.ServerSpec(
            host=server_config.host,
            port=server_config.port,
            password=server_config.password if server_config.password else None
        )

        # Configure SSL if needed
        connect_factory = irc.connection.Factory()
        if server_config.ssl:
            ssl_context = ssl.create_default_context()
            # Create wrapper that passes server_hostname for proper SSL verification
            def ssl_wrapper(sock):
                return ssl_context.wrap_socket(sock, server_hostname=server_config.host)
            connect_factory = irc.connection.Factory(wrapper=ssl_wrapper)

        # Initialize parent
        super().__init__(
            [server_spec],
            server_config.nick,
            server_config.realname,
            connect_factory=connect_factory
        )
        
        self.command_handler = CommandHandler(self)
        self.channels_to_join = server_config.channels
        
        logger.info(f"HaikuBot initialized for server: {server_name}")
    
    def on_nicknameinuse(self, connection, event):
        """Called when nickname is already in use."""
        connection.nick(connection.get_nickname() + "_")
    
    def on_welcome(self, connection, event):
        """Called when bot connects to IRC server."""
        logger.info(f"[{self.server_name}] Connected to IRC server")
        
        # Join all configured channels
        for channel in self.channels_to_join:
            logger.info(f"[{self.server_name}] Joining channel: {channel}")
            connection.join(channel)
    
    def on_join(self, connection, event):
        """Called when someone joins a channel.
        
        Args:
            connection: IRC connection
            event: Join event
        """
        nick = event.source.nick
        channel = event.target
        
        if nick == connection.get_nickname():
            logger.info(f"[{self.server_name}] Joined channel: {channel}")
    
    def on_pubmsg(self, connection, event):
        """Called when a public message is received in a channel.
        
        Args:
            connection: IRC connection
            event: Message event
        """
        source = event.source.nick
        channel = event.target
        message = event.arguments[0]
        
        # Ignore our own messages
        if source == connection.get_nickname():
            return
        
        logger.debug(f"[{self.server_name}][{channel}] <{source}> {message}")
        
        # Check if this is a command
        prefix = self.config.bot.trigger_prefix
        if message.startswith(prefix):
            self._handle_command(connection, source, channel, message)
            return
        
        # Auto-collect if enabled
        if self.config.features.auto_collect:
            self._auto_collect(source, channel, message)
    
    def on_privmsg(self, connection, event):
        """Called when a private message is received.
        
        Args:
            connection: IRC connection
            event: Message event
        """
        source = event.source.nick
        message = event.arguments[0]
        
        logger.debug(f"[{self.server_name}][PM] <{source}> {message}")
        
        # Check if this is a command
        prefix = self.config.bot.trigger_prefix
        if message.startswith(prefix):
            self._handle_command(connection, source, "PM", message)
    
    def _handle_command(self, connection, source: str, channel: str, message: str):
        """Handle a command message.
        
        Args:
            connection: IRC connection
            source: User who sent the command
            channel: Channel where command was sent (or "PM")
            message: Full message text
        """
        try:
            # Use synchronous wrapper since irc.bot is not async
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self.command_handler.handle(source, channel, message)
            )
            loop.close()
            
            if response:
                # Send response back to channel or user
                if channel == "PM":
                    connection.privmsg(source, response)
                else:
                    # Split long messages
                    for line in response.split('\n'):
                        if line.strip():
                            connection.privmsg(channel, line)
        except Exception as e:
            logger.error(f"Error handling command: {e}", exc_info=True)
            error_msg = "Sorry, an error occurred processing that command."
            if channel == "PM":
                connection.privmsg(source, error_msg)
            else:
                connection.privmsg(channel, error_msg)
    
    def _auto_collect(self, username: str, channel: str, message: str):
        """Auto-collect 5 or 7 syllable messages.

        Args:
            username: User who sent the message
            channel: Channel where message was sent
            message: Message text
        """
        # Check if user has opted out
        with get_session() as session:
            user = session.query(User).filter(User.username == username).first()
            if user and user.opted_out:
                logger.debug(f"User {username} has opted out, skipping auto-collect")
                return

        # Count syllables
        syllable_count = count_syllables(message)

        # Only collect 5 or 7 syllable messages
        if syllable_count not in [5, 7]:
            return

        # Validate that message contains only valid English words or approved acronyms
        is_valid, reason = validate_line_for_auto_collection(message)
        if not is_valid:
            logger.debug(f"Rejecting auto-collect for '{message}': {reason}")
            return
        
        # Store the line
        try:
            with get_session() as session:
                # Check for duplicate (case-insensitive)
                existing = session.query(Line).filter(
                    Line.text.ilike(message)
                ).first()
                
                if existing:
                    logger.debug(f"Line already exists: {message}")
                    return
                
                line = Line(
                    text=message,
                    syllable_count=syllable_count,
                    server=self.server_name,
                    channel=channel,
                    username=username,
                    timestamp=datetime.utcnow(),
                    source='auto',
                    placement='any' if syllable_count == 5 else None,
                    approved=True
                )
                
                session.add(line)
                session.commit()

                logger.info(f"[{self.server_name}][{channel}] Auto-collected {syllable_count}-syllable line from {username}: {message}")

                # Broadcast to WebSocket clients
                line_data = {
                    'id': line.id,
                    'text': line.text,
                    'syllable_count': line.syllable_count,
                    'username': line.username,
                    'channel': line.channel,
                    'server': line.server,
                    'source': line.source,
                    'timestamp': line.timestamp.isoformat()
                }

                # Import and call broadcast function
                import asyncio
                from ..api.websocket import broadcast_new_line
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(broadcast_new_line(line_data))
                    loop.close()
                except Exception as ws_error:
                    logger.error(f"Error broadcasting line to WebSocket: {ws_error}")

        except Exception as e:
            logger.error(f"Error auto-collecting line: {e}", exc_info=True)
    
    def send_message(self, target: str, text: str):
        """Send a message to a channel or user.
        
        Args:
            target: Channel or nickname to send to
            text: Message to send
        """
        self.connection.privmsg(target, text)
    
    def send_notice(self, target: str, text: str):
        """Send a notice to a user.
        
        Args:
            target: Nickname to send notice to
            text: Notice text
        """
        self.connection.notice(target, text)
