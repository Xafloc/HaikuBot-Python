"""Authorization and user management utilities."""

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from ..database.models import User
from ..config import get_config

logger = logging.getLogger(__name__)


def get_or_create_user(session: Session, username: str) -> User:
    """Get or create a user record.
    
    Args:
        session: Database session
        username: Username to look up or create
        
    Returns:
        User object
    """
    user = session.query(User).filter(User.username == username).first()
    
    if not user:
        logger.info(f"Creating new user record for: {username}")
        
        # Check if this is the bot owner (make admin)
        config = get_config()
        role = 'admin' if username == config.bot.owner else 'public'
        
        user = User(
            username=username,
            role=role,
            opted_out=False,
            created_at=datetime.utcnow()
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
    
    return user


def can_user_submit(username: str) -> bool:
    """Check if user can manually submit haiku lines.
    
    Args:
        username: Username to check
        
    Returns:
        True if user is editor or admin
    """
    from ..database import get_session
    
    with get_session() as session:
        user = get_or_create_user(session, username)
        return user.can_submit()


def is_user_admin(username: str, owner_nick: str) -> bool:
    """Check if user is an admin.
    
    Args:
        username: Username to check
        owner_nick: Bot owner nickname
        
    Returns:
        True if user is admin or bot owner
    """
    # Bot owner is always admin
    if username == owner_nick:
        return True
    
    from ..database import get_session
    
    with get_session() as session:
        user = session.query(User).filter(User.username == username).first()
        return user and user.is_admin()


def promote_user(session: Session, username: str, role: str = 'editor') -> User:
    """Promote a user to a specific role.
    
    Args:
        session: Database session
        username: Username to promote
        role: Role to assign ('editor' or 'admin')
        
    Returns:
        Updated User object
    """
    if role not in ['editor', 'admin']:
        raise ValueError(f"Invalid role: {role}")
    
    user = get_or_create_user(session, username)
    user.role = role
    session.commit()
    session.refresh(user)
    
    logger.info(f"Promoted {username} to {role}")
    
    return user


def demote_user(session: Session, username: str) -> User:
    """Demote a user to public role.
    
    Args:
        session: Database session
        username: Username to demote
        
    Returns:
        Updated User object
    """
    user = session.query(User).filter(User.username == username).first()
    
    if not user:
        raise ValueError(f"User not found: {username}")
    
    if user.role == 'admin':
        raise ValueError("Cannot demote admin users through this function")
    
    user.role = 'public'
    session.commit()
    session.refresh(user)
    
    logger.info(f"Demoted {username} to public")
    
    return user


def set_opt_out(session: Session, username: str, opted_out: bool) -> User:
    """Set user's opt-out status for auto-collection.
    
    Args:
        session: Database session
        username: Username
        opted_out: True to opt out, False to opt in
        
    Returns:
        Updated User object
    """
    user = get_or_create_user(session, username)
    user.opted_out = opted_out
    session.commit()
    session.refresh(user)
    
    logger.info(f"Set opt-out for {username}: {opted_out}")
    
    return user

