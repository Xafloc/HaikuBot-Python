"""IRC command handlers."""

import logging
import re
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass

from ..config import get_config
from ..database import get_session, Line, User, Vote, GeneratedHaiku
from ..haiku import count_syllables, generate_haiku, generate_haiku_for_user, generate_haiku_for_channel, get_haiku_stats
from ..utils.auth import get_or_create_user, can_user_submit, is_user_admin

if TYPE_CHECKING:
    from .bot import HaikuBot

logger = logging.getLogger(__name__)


@dataclass
class Response:
    """Response from a command handler.

    Attributes:
        message: The response message text
        is_notice: If True, send as NOTICE (private error/info). If False, send publicly to channel.
    """
    message: str
    is_notice: bool = False

    @classmethod
    def error(cls, message: str) -> 'Response':
        """Create an error response (sent as NOTICE)."""
        return cls(message=message, is_notice=True)

    @classmethod
    def success(cls, message: str) -> 'Response':
        """Create a success response (sent publicly to channel)."""
        return cls(message=message, is_notice=False)

    @classmethod
    def notice(cls, message: str) -> 'Response':
        """Create a notice response (sent as private NOTICE, non-intrusive confirmation)."""
        return cls(message=message, is_notice=True)


class CommandHandler:
    """Handles IRC command parsing and execution."""
    
    def __init__(self, bot: 'HaikuBot'):
        """Initialize command handler.
        
        Args:
            bot: HaikuBot instance
        """
        self.bot = bot
        self.config = get_config()
        self.prefix = self.config.bot.trigger_prefix
    
    async def handle(self, username: str, channel: str, message: str) -> Optional[Response]:
        """Handle a command message.

        Args:
            username: User who sent command
            channel: Channel where command was sent (or "PM")
            message: Full message text

        Returns:
            Response object or None
        """
        # Remove prefix
        if not message.startswith(self.prefix):
            return None
        
        command_text = message[len(self.prefix):].strip()
        
        # Parse command and arguments
        parts = command_text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        logger.info(f"Command: {command}, Args: {args}, User: {username}, Channel: {channel}")
        
        # Route to appropriate handler
        handler_map = {
            'haiku': self._cmd_haiku,
            'haiku5': self._cmd_haiku5,
            'haiku7': self._cmd_haiku7,
            'haikumanual': self._cmd_haiku_manual,
            'haikuauto': self._cmd_haiku_auto,
            'haikustats': self._cmd_stats,
            'haikuvote': self._cmd_vote,
            'haikutop': self._cmd_top,
            'myhaiku': self._cmd_my_haiku,
            'mystats': self._cmd_my_stats,
            'haikuhelp': self._cmd_help,
            'haikulist': self._cmd_list,
            'haikusyl': self._cmd_syllable_check,
            'haikuflag': self._cmd_flag,
        }
        
        # Check for subcommands (e.g., "haiku promote")
        if command == 'haiku' and args:
            subcommand = args.split()[0].lower()
            if subcommand in ['promote', 'demote', 'editors', 'optout', 'optin', 'delete']:
                command = f'haiku_{subcommand}'
                args = args.split(maxsplit=1)[1] if len(args.split()) > 1 else ""

                handler_map.update({
                    'haiku_promote': self._cmd_promote,
                    'haiku_demote': self._cmd_demote,
                    'haiku_editors': self._cmd_editors,
                    'haiku_optout': self._cmd_optout,
                    'haiku_optin': self._cmd_optin,
                    'haiku_delete': self._cmd_delete,
                })
        
        handler = handler_map.get(command)
        if handler:
            try:
                return await handler(username, channel, args)
            except Exception as e:
                logger.error(f"Error in command handler {command}: {e}", exc_info=True)
                return Response.error(f"Error: {str(e)}")

        return None
    
    async def _cmd_haiku(self, username: str, channel: str, args: str) -> Response:
        """Generate a random haiku or retrieve specific haiku by ID.

        Supports filters:
        - !haiku @username - From specific user
        - !haiku #channel - From specific channel
        - !haiku <id> - Retrieve specific haiku by ID
        """
        with get_session() as session:
            # Parse arguments for filters
            username_filter = None
            channel_filter = None

            if args:
                # Check for numeric ID
                if args.strip().isdigit():
                    haiku_id = int(args.strip())
                    haiku = session.query(GeneratedHaiku).filter(GeneratedHaiku.id == haiku_id).first()

                    if not haiku:
                        return Response.error(f"Haiku #{haiku_id} not found.")
                # Check for @username
                elif args.startswith('@'):
                    username_filter = args[1:].strip()
                    haiku = generate_haiku_for_user(
                        session, username_filter, username,
                        self.bot.server_name, channel
                    )
                # Check for #channel
                elif args.startswith('#'):
                    channel_filter = args.strip()
                    haiku = generate_haiku_for_channel(
                        session, channel_filter, username,
                        self.bot.server_name, channel
                    )
                else:
                    return Response.error(f"Invalid filter. Use @username, #channel, or numeric ID")
            else:
                # Generate random haiku
                haiku = generate_haiku(
                    session, username, self.bot.server_name, channel
                )

            if not haiku:
                return Response.error("Not enough lines to generate a haiku. Contribute with !haiku5 or !haiku7!")

            # Get sources (usernames of each line contributor)
            sources = f"({haiku.line1.username}, {haiku.line2.username}, {haiku.line3.username})"

            # Format response with sources and URL
            web_url = self.config.bot.web_url if hasattr(self.config.bot, 'web_url') else ""
            url_part = f" -- {web_url}" if web_url else ""

            return Response.success(f"{haiku.full_text} -- `{self.prefix}haikuvote {haiku.id}` -- Sources: {sources}{url_part}")

    async def _cmd_haiku_manual(self, username: str, channel: str, args: str) -> Response:
        """Generate a haiku using only manually submitted lines."""
        with get_session() as session:
            haiku = generate_haiku(
                session, username, self.bot.server_name, channel,
                source_filter='manual'
            )

            if not haiku:
                return Response.error("Not enough manual lines to generate a haiku. Editors can submit with !haiku5 or !haiku7!")

            # Get sources (usernames of each line contributor)
            sources = f"({haiku.line1.username}, {haiku.line2.username}, {haiku.line3.username})"

            # Format response with sources and URL
            web_url = self.config.bot.web_url if hasattr(self.config.bot, 'web_url') else ""
            url_part = f" -- {web_url}" if web_url else ""

            return Response.success(f"[Manual] {haiku.full_text} -- `{self.prefix}haikuvote {haiku.id}` -- Sources: {sources}{url_part}")

    async def _cmd_haiku_auto(self, username: str, channel: str, args: str) -> Response:
        """Generate a haiku using only auto-collected lines."""
        with get_session() as session:
            haiku = generate_haiku(
                session, username, self.bot.server_name, channel,
                source_filter='auto'
            )

            if not haiku:
                return Response.error("Not enough auto-collected lines to generate a haiku. Lines are automatically collected from IRC.")

            # Get sources (usernames of each line contributor)
            sources = f"({haiku.line1.username}, {haiku.line2.username}, {haiku.line3.username})"

            # Format response with sources and URL
            web_url = self.config.bot.web_url if hasattr(self.config.bot, 'web_url') else ""
            url_part = f" -- {web_url}" if web_url else ""

            return Response.success(f"[Auto] {haiku.full_text} -- `{self.prefix}haikuvote {haiku.id}` -- Sources: {sources}{url_part}")

    async def _cmd_haiku5(self, username: str, channel: str, args: str) -> Response:
        """Submit a 5-syllable line.

        Format: !haiku5 [--first|--last] <text>
        """
        # Check authorization
        if not can_user_submit(username):
            return Response.error(f"You need editor privileges. Contact {self.config.bot.owner} for access.")

        # Parse placement flag
        placement = 'any'
        text = args.strip()

        if text.startswith('--first'):
            placement = 'first'
            text = text[7:].strip()
        elif text.startswith('--last'):
            placement = 'last'
            text = text[6:].strip()

        if not text:
            return Response.error("Usage: !haiku5 [--first|--last] <text>")

        # Verify syllable count
        syllables = count_syllables(text)
        if syllables != 5:
            return Response.error(f"Syllable check failed: {syllables} syllables (expected 5)")

        # Store line
        with get_session() as session:
            # Check for duplicate
            existing = session.query(Line).filter(Line.text.ilike(text)).first()
            if existing:
                return Response.error("That line already exists in the database.")
            
            line = Line(
                text=text,
                syllable_count=5,
                server=self.bot.server_name,
                channel=channel,
                username=username,
                timestamp=datetime.utcnow(),
                source='manual',
                placement=placement,
                approved=True
            )
            
            session.add(line)
            session.commit()

            # Broadcast to WebSocket clients
            import asyncio
            from ..api.websocket import broadcast_new_line
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
            try:
                await broadcast_new_line(line_data)
            except Exception as ws_error:
                logger.error(f"Error broadcasting line to WebSocket: {ws_error}")

            placement_str = f" ({placement} position)" if placement != 'any' else ""
            return Response.notice(f"Added 5-syllable line{placement_str}: {text}")

    async def _cmd_haiku7(self, username: str, channel: str, args: str) -> Response:
        """Submit a 7-syllable line."""
        # Check authorization
        if not can_user_submit(username):
            return Response.error(f"You need editor privileges. Contact {self.config.bot.owner} for access.")

        text = args.strip()

        if not text:
            return Response.error("Usage: !haiku7 <text>")

        # Verify syllable count
        syllables = count_syllables(text)
        if syllables != 7:
            return Response.error(f"Syllable check failed: {syllables} syllables (expected 7)")

        # Store line
        with get_session() as session:
            # Check for duplicate
            existing = session.query(Line).filter(Line.text.ilike(text)).first()
            if existing:
                return Response.error("That line already exists in the database.")
            
            line = Line(
                text=text,
                syllable_count=7,
                server=self.bot.server_name,
                channel=channel,
                username=username,
                timestamp=datetime.utcnow(),
                source='manual',
                placement=None,  # 7-syllable lines have no placement
                approved=True
            )
            
            session.add(line)
            session.commit()

            # Broadcast to WebSocket clients
            from ..api.websocket import broadcast_new_line
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
            try:
                await broadcast_new_line(line_data)
            except Exception as ws_error:
                logger.error(f"Error broadcasting line to WebSocket: {ws_error}")

            return Response.notice(f"Added 7-syllable line: {text}")

    async def _cmd_flag(self, username: str, channel: str, args: str) -> Response:
        """Flag a line for admin review/deletion."""
        # Check authorization
        if not can_user_submit(username):
            return Response.error(f"You need editor privileges. Contact {self.config.bot.owner} for access.")

        if not args or not args.strip().isdigit():
            return Response.error("Usage: !haikuflag <line_id>")

        line_id = int(args.strip())

        with get_session() as session:
            # Check if line exists
            line = session.query(Line).filter(Line.id == line_id).first()
            if not line:
                return Response.error(f"Line #{line_id} not found.")

            # Check if already flagged
            if line.flagged_for_deletion:
                return Response.error(f"Line #{line_id} is already flagged for deletion.")

            # Flag the line
            line.flagged_for_deletion = True
            session.commit()

            logger.info(f"Line {line_id} flagged by {username}: '{line.text}'")

            return Response.notice(f"Flagged line #{line_id} for admin review: {line.text}")

    async def _cmd_stats(self, username: str, channel: str, args: str) -> Response:
        """Show haiku statistics."""
        with get_session() as session:
            stats = get_haiku_stats(session)

            return Response.success(f"5-syllable lines: {stats['lines_5_syllable']} | "
                   f"7-syllable lines: {stats['lines_7_syllable']} | "
                   f"Possible permutations: {stats['possible_permutations']:,} | "
                   f"Generated haikus: {stats['generated_haikus']}")
    
    async def _cmd_vote(self, username: str, channel: str, args: str) -> Response:
        """Vote for a haiku."""
        if not args or not args.strip().isdigit():
            return Response.error("Usage: !haikuvote <haiku_id>")

        haiku_id = int(args.strip())

        with get_session() as session:
            # Check if haiku exists
            haiku = session.query(GeneratedHaiku).filter(GeneratedHaiku.id == haiku_id).first()
            if not haiku:
                return Response.error(f"Haiku #{haiku_id} not found.")

            # Check if already voted
            existing_vote = session.query(Vote).filter(
                Vote.haiku_id == haiku_id,
                Vote.username == username
            ).first()

            if existing_vote:
                return Response.error(f"You've already voted for haiku #{haiku_id}!")

            # Add vote
            vote = Vote(
                haiku_id=haiku_id,
                username=username,
                voted_at=datetime.utcnow()
            )

            session.add(vote)
            session.commit()

            # Get current vote count after committing
            vote_count = session.query(Vote).filter(Vote.haiku_id == haiku_id).count()

            return Response.notice(f"Thanks for voting! Haiku #{haiku_id} now has {vote_count} vote(s).")
    
    async def _cmd_top(self, username: str, channel: str, args: str) -> Response:
        """Show top voted haikus."""
        limit = 5
        if args and args.strip().isdigit():
            limit = min(int(args.strip()), 20)  # Cap at 20

        with get_session() as session:
            # Query top haikus by vote count
            from sqlalchemy import func, desc

            results = session.query(
                GeneratedHaiku,
                func.count(Vote.id).label('vote_count')
            ).outerjoin(Vote).group_by(GeneratedHaiku.id).order_by(
                desc('vote_count'),
                desc(GeneratedHaiku.generated_at)
            ).limit(limit).all()

            if not results:
                return Response.error("No haikus have been generated yet!")

            lines = [f"Top {len(results)} Haiku(s):"]
            for haiku, vote_count in results:
                lines.append(f"[{vote_count} votes] #{haiku.id}: {haiku.full_text}")

            lines.append(f"Vote with {self.prefix}haikuvote <id>")

            # Send as PM if in channel (return multiline for PM)
            if channel != "PM":
                # For channel messages, send notice
                for line in lines:
                    self.bot.send_notice(username, line)
                return Response.success(f"{username}: Sent top haikus via notice")
            else:
                return Response.success("\n".join(lines))
    
    async def _cmd_my_haiku(self, username: str, channel: str, args: str) -> Response:
        """Show user's contributed lines."""
        with get_session() as session:
            lines = session.query(Line).filter(Line.username == username).limit(10).all()

            if not lines:
                return Response.error(f"You haven't contributed any lines yet!")

            result = [f"Your contributions ({len(lines)} shown):"]
            for line in lines:
                result.append(f"[{line.syllable_count} syl] {line.text}")

            # Send as PM if in channel
            if channel != "PM":
                for line in result:
                    self.bot.send_notice(username, line)
                return Response.success(f"{username}: Sent your haiku lines via notice")
            else:
                return Response.success("\n".join(result))
    
    async def _cmd_my_stats(self, username: str, channel: str, args: str) -> Response:
        """Show user's personal statistics."""
        with get_session() as session:
            line_count = session.query(Line).filter(Line.username == username).count()
            haiku_count = session.query(GeneratedHaiku).filter(GeneratedHaiku.triggered_by == username).count()

            return Response.success(f"{username}: {line_count} lines contributed, {haiku_count} haikus generated")
    
    async def _cmd_help(self, username: str, channel: str, args: str) -> Response:
        """Show help information."""
        help_text = f"""HaikuBot Commands:
{self.prefix}haiku - Generate random haiku
{self.prefix}haiku @user - Generate from user's lines
{self.prefix}haiku #channel - Generate from channel's lines
{self.prefix}haikumanual - Generate from editor-submitted lines only
{self.prefix}haikuauto - Generate from auto-collected lines only
{self.prefix}haikustats - Show statistics
{self.prefix}haikuvote <id> - Vote for a haiku
{self.prefix}haikutop - Show top voted haikus
{self.prefix}myhaiku - Show your contributions
{self.prefix}mystats - Show your stats
{self.prefix}haikusyl <text> - Check syllable count

Editor Commands:
{self.prefix}haiku5 <text> - Submit 5-syllable line
{self.prefix}haiku5 --first <text> - First position only
{self.prefix}haiku5 --last <text> - Last position only
{self.prefix}haiku7 <text> - Submit 7-syllable line
{self.prefix}haikuflag <line_id> - Flag line for admin review

Admin Commands:
{self.prefix}haiku promote @user - Grant editor privileges
{self.prefix}haiku demote @user - Revoke editor privileges
{self.prefix}haiku delete line <id> - Delete a line
{self.prefix}haiku delete haiku <id> - Delete a haiku
{self.prefix}haiku editors - List editors

Web: {self.config.bot.web_url}"""

        # Send as PM if in channel
        if channel != "PM":
            for line in help_text.split('\n'):
                self.bot.send_notice(username, line)
            return Response.success(f"{username}: Sent help via notice")
        else:
            return Response.success(help_text)
    
    async def _cmd_list(self, username: str, channel: str, args: str) -> Response:
        """List generated haikus."""
        return Response.success(f"View all haikus at: {self.config.bot.web_url}")
    
    async def _cmd_promote(self, username: str, channel: str, args: str) -> Response:
        """Promote user to editor (admin only)."""
        if not is_user_admin(username, self.config.bot.owner):
            return Response.error("Admin only command.")

        if not args or not args.startswith('@'):
            return Response.error("Usage: !haiku promote @username")

        target_user = args[1:].strip()

        with get_session() as session:
            user = get_or_create_user(session, target_user)
            if user.role == 'admin':
                return Response.error(f"{target_user} is already an admin.")

            user.role = 'editor'
            session.commit()

            return Response.success(f"{target_user} promoted to editor.")
    
    async def _cmd_demote(self, username: str, channel: str, args: str) -> Response:
        """Demote user from editor (admin only)."""
        if not is_user_admin(username, self.config.bot.owner):
            return Response.error("Admin only command.")

        if not args or not args.startswith('@'):
            return Response.error("Usage: !haiku demote @username")

        target_user = args[1:].strip()

        with get_session() as session:
            user = session.query(User).filter(User.username == target_user).first()
            if not user:
                return Response.error(f"User {target_user} not found.")

            if user.role == 'admin':
                return Response.error("Cannot demote admin users.")

            user.role = 'public'
            session.commit()

            return Response.success(f"{target_user} demoted to public user.")
    
    async def _cmd_editors(self, username: str, channel: str, args: str) -> Response:
        """List all editors (admin only)."""
        if not is_user_admin(username, self.config.bot.owner):
            return Response.error("Admin only command.")

        with get_session() as session:
            editors = session.query(User).filter(User.role.in_(['editor', 'admin'])).all()

            if not editors:
                return Response.error("No editors found.")

            result = ["Editors:"]
            for user in editors:
                result.append(f"- {user.username} ({user.role})")

            return Response.success("\n".join(result))
    
    async def _cmd_optout(self, username: str, channel: str, args: str) -> Response:
        """Opt out of auto-collection."""
        with get_session() as session:
            user = get_or_create_user(session, username)
            user.opted_out = True
            session.commit()

            return Response.success("You've opted out of auto-collection. Your messages won't be collected automatically.")
    
    async def _cmd_optin(self, username: str, channel: str, args: str) -> Response:
        """Opt back into auto-collection."""
        with get_session() as session:
            user = get_or_create_user(session, username)
            user.opted_out = False
            session.commit()

            return Response.success("You've opted back into auto-collection. Your messages may be collected automatically.")

    async def _cmd_delete(self, username: str, channel: str, args: str) -> Response:
        """Delete a line or haiku (admin only).

        Usage:
            !haiku delete line <id>
            !haiku delete haiku <id>
        """
        # Check authorization
        if not is_user_admin(username, self.config.bot.owner):
            return Response.error("Admin only command.")

        if not args:
            return Response.error("Usage: !haiku delete [line|haiku] <id>")

        parts = args.split()
        if len(parts) < 2:
            return Response.error("Usage: !haiku delete [line|haiku] <id>")

        item_type = parts[0].lower()
        item_id = parts[1]

        if not item_id.isdigit():
            return Response.error("ID must be a number.")

        item_id = int(item_id)

        with get_session() as session:
            if item_type == 'line':
                # Delete a line
                line = session.query(Line).filter(Line.id == item_id).first()

                if not line:
                    return Response.error(f"Line #{item_id} not found.")

                # Check if line is used in any haikus
                haikus_using_line = session.query(GeneratedHaiku).filter(
                    (GeneratedHaiku.line1_id == item_id) |
                    (GeneratedHaiku.line2_id == item_id) |
                    (GeneratedHaiku.line3_id == item_id)
                ).all()

                if haikus_using_line:
                    haiku_ids = ', '.join(str(h.id) for h in haikus_using_line)
                    return Response.error(f"Cannot delete line #{item_id}: Used in {len(haikus_using_line)} haiku(s) (IDs: {haiku_ids}). Delete those haikus first.")

                line_text = line.text
                session.delete(line)
                session.commit()

                return Response.success(f"Deleted line #{item_id}: \"{line_text}\"")

            elif item_type == 'haiku':
                # Delete a haiku
                haiku = session.query(GeneratedHaiku).filter(GeneratedHaiku.id == item_id).first()

                if not haiku:
                    return Response.error(f"Haiku #{item_id} not found.")

                # Also delete associated votes
                vote_count = session.query(Vote).filter(Vote.haiku_id == item_id).count()
                session.query(Vote).filter(Vote.haiku_id == item_id).delete()

                haiku_text = haiku.full_text
                session.delete(haiku)
                session.commit()

                vote_msg = f" and {vote_count} vote(s)" if vote_count > 0 else ""
                return Response.success(f"Deleted haiku #{item_id}{vote_msg}: \"{haiku_text}\"")

            else:
                return Response.error("Invalid type. Use 'line' or 'haiku'.")

    async def _cmd_syllable_check(self, username: str, channel: str, args: str) -> Response:
        """Check syllable count of provided text.

        Usage: !haikusyl <text>
        """
        if not args or not args.strip():
            return Response.error("Usage: !haikusyl <text>")

        from backend.haiku.syllable_counter import count_syllables

        text = args.strip()
        syllable_count = count_syllables(text)

        return Response.success(f"Syllable Count: {syllable_count}")

