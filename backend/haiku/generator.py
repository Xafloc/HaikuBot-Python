"""Haiku generation logic with placement awareness."""

import logging
import random
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.models import Line, GeneratedHaiku

logger = logging.getLogger(__name__)


def generate_haiku(
    session: Session,
    triggered_by: str,
    server: str,
    channel: str,
    username_filter: Optional[str] = None,
    channel_filter: Optional[str] = None,
    server_filter: Optional[str] = None,
    source_filter: Optional[str] = None
) -> Optional[GeneratedHaiku]:
    """Generate a random haiku from available lines.

    Implements smart placement logic:
    - Line 1 (5 syl): Cannot have placement='last'
    - Line 2 (7 syl): Any 7-syllable line
    - Line 3 (5 syl): Cannot have placement='first'

    Args:
        session: Database session
        triggered_by: Username who triggered generation
        server: Server where generation was triggered
        channel: Channel where generation was triggered
        username_filter: Optional filter by username
        channel_filter: Optional filter by channel
        server_filter: Optional filter by server
        source_filter: Optional filter by source ('auto' or 'manual')

    Returns:
        GeneratedHaiku object or None if insufficient lines
    """
    # Build base query filters
    filters_5_first = [Line.syllable_count == 5, Line.approved == True, Line.flagged_for_deletion == False]
    filters_7 = [Line.syllable_count == 7, Line.approved == True, Line.flagged_for_deletion == False]
    filters_5_last = [Line.syllable_count == 5, Line.approved == True, Line.flagged_for_deletion == False]
    
    # Add placement restrictions
    filters_5_first.append(or_(Line.placement == None, Line.placement.in_(['any', 'first'])))
    filters_5_last.append(or_(Line.placement == None, Line.placement.in_(['any', 'last'])))
    
    # Apply optional filters
    if username_filter:
        filters_5_first.append(Line.username == username_filter)
        filters_7.append(Line.username == username_filter)
        filters_5_last.append(Line.username == username_filter)
    
    if channel_filter:
        filters_5_first.append(Line.channel == channel_filter)
        filters_7.append(Line.channel == channel_filter)
        filters_5_last.append(Line.channel == channel_filter)
    
    if server_filter:
        filters_5_first.append(Line.server == server_filter)
        filters_7.append(Line.server == server_filter)
        filters_5_last.append(Line.server == server_filter)

    if source_filter:
        filters_5_first.append(Line.source == source_filter)
        filters_7.append(Line.source == source_filter)
        filters_5_last.append(Line.source == source_filter)

    # Query for available lines
    line1_candidates = session.query(Line).filter(and_(*filters_5_first)).all()
    line2_candidates = session.query(Line).filter(and_(*filters_7)).all()
    line3_candidates = session.query(Line).filter(and_(*filters_5_last)).all()
    
    # Log counts
    logger.info(f"Line candidates: 1st={len(line1_candidates)}, "
                f"2nd={len(line2_candidates)}, 3rd={len(line3_candidates)}")
    
    # Check if we have enough lines
    if not line1_candidates:
        logger.warning("No valid 5-syllable lines for position 1")
        return None
    if not line2_candidates:
        logger.warning("No valid 7-syllable lines for position 2")
        return None
    if not line3_candidates:
        logger.warning("No valid 5-syllable lines for position 3")
        return None
    
    # Randomly select lines
    line1 = random.choice(line1_candidates)
    line2 = random.choice(line2_candidates)

    # Ensure line3 is different from line1 (avoid duplicate 5-syllable lines)
    line3_candidates_filtered = [line for line in line3_candidates if line.id != line1.id]

    # If filtering removed all candidates and we have more than one candidate total, retry
    if not line3_candidates_filtered and len(line3_candidates) > 1:
        # This shouldn't happen, but fallback to original list
        line3_candidates_filtered = line3_candidates
    elif not line3_candidates_filtered:
        # Only one 5-syllable line available, must use it even if duplicate
        logger.warning(f"Only one 5-syllable line available, allowing duplicate")
        line3_candidates_filtered = line3_candidates

    line3 = random.choice(line3_candidates_filtered)

    # Log if we ended up with duplicate despite filtering
    if line1.id == line3.id:
        logger.warning(f"Haiku has duplicate line (only one 5-syllable line available): '{line1.text}'")

    # Construct full haiku text
    full_text = f"{line1.text} / {line2.text} / {line3.text}"
    
    # Create haiku record
    haiku = GeneratedHaiku(
        line1_id=line1.id,
        line2_id=line2.id,
        line3_id=line3.id,
        full_text=full_text,
        triggered_by=triggered_by,
        server=server,
        channel=channel
    )
    
    session.add(haiku)
    session.commit()
    session.refresh(haiku)
    
    logger.info(f"Generated haiku #{haiku.id}: {full_text[:50]}...")
    
    return haiku


def generate_haiku_for_user(
    session: Session,
    username: str,
    triggered_by: str,
    server: str,
    channel: str
) -> Optional[GeneratedHaiku]:
    """Generate a haiku using only lines from a specific user.
    
    Args:
        session: Database session
        username: Username to filter by
        triggered_by: Username who triggered generation
        server: Server where generation was triggered
        channel: Channel where generation was triggered
        
    Returns:
        GeneratedHaiku object or None if insufficient lines
    """
    logger.info(f"Generating haiku for user: {username}")
    return generate_haiku(
        session=session,
        triggered_by=triggered_by,
        server=server,
        channel=channel,
        username_filter=username
    )


def generate_haiku_for_channel(
    session: Session,
    target_channel: str,
    triggered_by: str,
    server: str,
    channel: str,
    server_name: Optional[str] = None
) -> Optional[GeneratedHaiku]:
    """Generate a haiku using only lines from a specific channel.
    
    Args:
        session: Database session
        target_channel: Channel to filter by
        triggered_by: Username who triggered generation
        server: Server where generation was triggered
        channel: Channel where generation was triggered
        server_name: Optional server name to filter by
        
    Returns:
        GeneratedHaiku object or None if insufficient lines
    """
    logger.info(f"Generating haiku for channel: {target_channel}")
    return generate_haiku(
        session=session,
        triggered_by=triggered_by,
        server=server,
        channel=channel,
        channel_filter=target_channel,
        server_filter=server_name
    )


def get_haiku_stats(session: Session) -> dict:
    """Get statistics about available haiku lines.
    
    Args:
        session: Database session
        
    Returns:
        Dictionary with statistics
    """
    # Count 5-syllable lines by placement
    lines_5_any = session.query(Line).filter(
        Line.syllable_count == 5,
        or_(Line.placement == None, Line.placement == 'any')
    ).count()
    
    lines_5_first = session.query(Line).filter(
        Line.syllable_count == 5,
        Line.placement == 'first'
    ).count()
    
    lines_5_last = session.query(Line).filter(
        Line.syllable_count == 5,
        Line.placement == 'last'
    ).count()
    
    # Count 7-syllable lines
    lines_7 = session.query(Line).filter(Line.syllable_count == 7).count()
    
    # Calculate valid line counts for each position
    lines_pos1 = lines_5_any + lines_5_first  # Can use 'any' or 'first'
    lines_pos2 = lines_7
    lines_pos3 = lines_5_any + lines_5_last   # Can use 'any' or 'last'
    
    # Calculate possible permutations (avoiding double-counting 'any' lines)
    # For now, simplified calculation
    possible_permutations = lines_pos1 * lines_pos2 * lines_pos3
    
    # Count generated haikus
    total_haikus = session.query(GeneratedHaiku).count()
    
    return {
        "lines_5_syllable": lines_5_any + lines_5_first + lines_5_last,
        "lines_5_any": lines_5_any,
        "lines_5_first_only": lines_5_first,
        "lines_5_last_only": lines_5_last,
        "lines_7_syllable": lines_7,
        "lines_position_1": lines_pos1,
        "lines_position_2": lines_pos2,
        "lines_position_3": lines_pos3,
        "possible_permutations": possible_permutations,
        "generated_haikus": total_haikus
    }

