"""REST API routes."""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, desc

from ..database import get_session, Line, GeneratedHaiku, Vote, User
from ..haiku import generate_haiku, get_haiku_stats
from ..utils.auth import get_or_create_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for API responses

class LineResponse(BaseModel):
    """Line response model."""
    id: int
    text: str
    syllable_count: int
    server: str
    channel: str
    username: str
    timestamp: datetime
    source: str
    placement: Optional[str]
    
    class Config:
        from_attributes = True


class HaikuResponse(BaseModel):
    """Haiku response model."""
    id: int
    full_text: str
    generated_at: datetime
    triggered_by: str
    server: str
    channel: str
    vote_count: int
    line1: LineResponse
    line2: LineResponse
    line3: LineResponse
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """Statistics response model."""
    lines_5_syllable: int
    lines_7_syllable: int
    lines_position_1: int
    lines_position_2: int
    lines_position_3: int
    possible_permutations: int
    generated_haikus: int


class UserStatsResponse(BaseModel):
    """User statistics response model."""
    username: str
    lines_contributed: int
    haikus_generated: int
    role: str


# Routes

@router.get("/haikus", response_model=List[HaikuResponse])
async def list_haikus(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    server: Optional[str] = None,
    channel: Optional[str] = None,
    username: Optional[str] = None,
    search: Optional[str] = None
):
    """List generated haikus with pagination and filters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        server: Optional server filter
        channel: Optional channel filter
        username: Optional username filter (triggered_by)
        search: Search by haiku text or ID

    Returns:
        List of haikus
    """
    with get_session() as session:
        query = session.query(GeneratedHaiku)

        # Apply filters
        if server:
            query = query.filter(GeneratedHaiku.server == server)
        if channel:
            query = query.filter(GeneratedHaiku.channel == channel)
        if username:
            query = query.filter(GeneratedHaiku.triggered_by == username)
        if search:
            # Search in haiku text or ID
            search_term = f"%{search}%"
            query = query.filter(
                (GeneratedHaiku.full_text.ilike(search_term)) |
                (GeneratedHaiku.id == int(search) if search.isdigit() else False)
            )
        
        # Order by most recent
        query = query.order_by(desc(GeneratedHaiku.generated_at))
        
        # Pagination
        haikus = query.offset(skip).limit(limit).all()
        
        # Build response with vote counts
        results = []
        for haiku in haikus:
            results.append(HaikuResponse(
                id=haiku.id,
                full_text=haiku.full_text,
                generated_at=haiku.generated_at,
                triggered_by=haiku.triggered_by,
                server=haiku.server,
                channel=haiku.channel,
                vote_count=len(haiku.votes),
                line1=LineResponse.from_orm(haiku.line1),
                line2=LineResponse.from_orm(haiku.line2),
                line3=LineResponse.from_orm(haiku.line3)
            ))
        
        return results


@router.get("/haikus/{haiku_id}", response_model=HaikuResponse)
async def get_haiku(haiku_id: int):
    """Get a specific haiku by ID.
    
    Args:
        haiku_id: Haiku ID
        
    Returns:
        Haiku details
    """
    with get_session() as session:
        haiku = session.query(GeneratedHaiku).filter(GeneratedHaiku.id == haiku_id).first()
        
        if not haiku:
            raise HTTPException(status_code=404, detail="Haiku not found")
        
        return HaikuResponse(
            id=haiku.id,
            full_text=haiku.full_text,
            generated_at=haiku.generated_at,
            triggered_by=haiku.triggered_by,
            server=haiku.server,
            channel=haiku.channel,
            vote_count=len(haiku.votes),
            line1=LineResponse.from_orm(haiku.line1),
            line2=LineResponse.from_orm(haiku.line2),
            line3=LineResponse.from_orm(haiku.line3)
        )


@router.get("/haikus/random", response_model=HaikuResponse)
async def get_random_haiku():
    """Get a random generated haiku.
    
    Returns:
        Random haiku
    """
    with get_session() as session:
        haiku = session.query(GeneratedHaiku).order_by(func.random()).first()
        
        if not haiku:
            raise HTTPException(status_code=404, detail="No haikus available")
        
        return HaikuResponse(
            id=haiku.id,
            full_text=haiku.full_text,
            generated_at=haiku.generated_at,
            triggered_by=haiku.triggered_by,
            server=haiku.server,
            channel=haiku.channel,
            vote_count=len(haiku.votes),
            line1=LineResponse.from_orm(haiku.line1),
            line2=LineResponse.from_orm(haiku.line2),
            line3=LineResponse.from_orm(haiku.line3)
        )


class GenerateHaikuRequest(BaseModel):
    """Request model for generating haiku."""
    username_filter: Optional[str] = None
    channel_filter: Optional[str] = None
    server_filter: Optional[str] = None


@router.post("/haikus/generate", response_model=HaikuResponse)
async def generate_haiku_api(request: GenerateHaikuRequest):
    """Generate a new haiku via API.
    
    Args:
        request: Generation parameters
        
    Returns:
        Newly generated haiku
    """
    with get_session() as session:
        haiku = generate_haiku(
            session=session,
            triggered_by="web_api",
            server="web",
            channel="web",
            username_filter=request.username_filter,
            channel_filter=request.channel_filter,
            server_filter=request.server_filter
        )
        
        if not haiku:
            raise HTTPException(status_code=400, detail="Not enough lines to generate haiku")
        
        return HaikuResponse(
            id=haiku.id,
            full_text=haiku.full_text,
            generated_at=haiku.generated_at,
            triggered_by=haiku.triggered_by,
            server=haiku.server,
            channel=haiku.channel,
            vote_count=0,
            line1=LineResponse.from_orm(haiku.line1),
            line2=LineResponse.from_orm(haiku.line2),
            line3=LineResponse.from_orm(haiku.line3)
        )


class VoteRequest(BaseModel):
    """Request model for voting."""
    username: str


@router.post("/haikus/{haiku_id}/vote")
async def vote_for_haiku(haiku_id: int, request: VoteRequest):
    """Vote for a haiku.
    
    Args:
        haiku_id: Haiku ID
        request: Vote request with username
        
    Returns:
        Success message and vote count
    """
    with get_session() as session:
        # Check if haiku exists
        haiku = session.query(GeneratedHaiku).filter(GeneratedHaiku.id == haiku_id).first()
        if not haiku:
            raise HTTPException(status_code=404, detail="Haiku not found")
        
        # Check if already voted
        existing = session.query(Vote).filter(
            Vote.haiku_id == haiku_id,
            Vote.username == request.username
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Already voted for this haiku")
        
        # Add vote
        vote = Vote(
            haiku_id=haiku_id,
            username=request.username,
            voted_at=datetime.utcnow()
        )
        
        session.add(vote)
        session.commit()
        
        # Get updated vote count
        vote_count = session.query(Vote).filter(Vote.haiku_id == haiku_id).count()
        
        return {"message": "Vote recorded", "vote_count": vote_count}


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get global statistics.
    
    Returns:
        Statistics about lines and haikus
    """
    with get_session() as session:
        stats = get_haiku_stats(session)
        return StatsResponse(**stats)


@router.get("/lines", response_model=List[LineResponse])
async def list_lines(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    syllable_count: Optional[int] = Query(None, ge=5, le=7),
    username: Optional[str] = None
):
    """List haiku lines with pagination and filters.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        syllable_count: Optional syllable count filter (5 or 7)
        username: Optional username filter
        
    Returns:
        List of lines
    """
    with get_session() as session:
        query = session.query(Line)
        
        # Apply filters
        if syllable_count:
            query = query.filter(Line.syllable_count == syllable_count)
        if username:
            query = query.filter(Line.username == username)
        
        # Order by most recent
        query = query.order_by(desc(Line.timestamp))
        
        # Pagination
        lines = query.offset(skip).limit(limit).all()
        
        return [LineResponse.from_orm(line) for line in lines]


@router.get("/users/{username}/stats", response_model=UserStatsResponse)
async def get_user_stats(username: str):
    """Get statistics for a specific user.
    
    Args:
        username: Username to look up
        
    Returns:
        User statistics
    """
    with get_session() as session:
        user = session.query(User).filter(User.username == username).first()
        
        line_count = session.query(Line).filter(Line.username == username).count()
        haiku_count = session.query(GeneratedHaiku).filter(GeneratedHaiku.triggered_by == username).count()
        
        return UserStatsResponse(
            username=username,
            lines_contributed=line_count,
            haikus_generated=haiku_count,
            role=user.role if user else "public"
        )


@router.get("/users/{username}/lines", response_model=List[LineResponse])
async def get_user_lines(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get lines contributed by a specific user.
    
    Args:
        username: Username to look up
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of user's lines
    """
    with get_session() as session:
        lines = session.query(Line).filter(
            Line.username == username
        ).order_by(desc(Line.timestamp)).offset(skip).limit(limit).all()
        
        return [LineResponse.from_orm(line) for line in lines]


@router.get("/users/{username}/haikus", response_model=List[HaikuResponse])
async def get_user_haikus(
    username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get haikus generated by a specific user.
    
    Args:
        username: Username to look up
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of user's generated haikus
    """
    with get_session() as session:
        haikus = session.query(GeneratedHaiku).filter(
            GeneratedHaiku.triggered_by == username
        ).order_by(desc(GeneratedHaiku.generated_at)).offset(skip).limit(limit).all()
        
        results = []
        for haiku in haikus:
            results.append(HaikuResponse(
                id=haiku.id,
                full_text=haiku.full_text,
                generated_at=haiku.generated_at,
                triggered_by=haiku.triggered_by,
                server=haiku.server,
                channel=haiku.channel,
                vote_count=len(haiku.votes),
                line1=LineResponse.from_orm(haiku.line1),
                line2=LineResponse.from_orm(haiku.line2),
                line3=LineResponse.from_orm(haiku.line3)
            ))
        
        return results


@router.get("/leaderboard")
async def get_leaderboard(limit: int = Query(10, ge=1, le=50)):
    """Get user leaderboard by lines contributed.
    
    Args:
        limit: Maximum number of users to return
        
    Returns:
        List of users with contribution counts
    """
    with get_session() as session:
        results = session.query(
            Line.username,
            func.count(Line.id).label('line_count')
        ).group_by(Line.username).order_by(desc('line_count')).limit(limit).all()
        
        leaderboard = []
        for username, count in results:
            leaderboard.append({
                "username": username,
                "lines_contributed": count
            })
        
        return leaderboard


class FlagLineRequest(BaseModel):
    """Request model for flagging a line."""
    username: str
    reason: Optional[str] = None


@router.post("/lines/{line_id}/flag")
async def flag_line(line_id: int, request: FlagLineRequest):
    """Flag a line for admin review/deletion.

    Only editors and admins can flag lines.

    Args:
        line_id: Line ID to flag
        request: Flag request with username

    Returns:
        Success message
    """
    with get_session() as session:
        # Check if user has editor or admin role
        user = get_or_create_user(session, request.username)
        if not user.can_submit():
            raise HTTPException(
                status_code=403,
                detail="Only editors and admins can flag lines"
            )

        # Check if line exists
        line = session.query(Line).filter(Line.id == line_id).first()
        if not line:
            raise HTTPException(status_code=404, detail="Line not found")

        # Check if already flagged
        if line.flagged_for_deletion:
            raise HTTPException(status_code=400, detail="Line is already flagged")

        # Flag the line
        line.flagged_for_deletion = True
        session.commit()

        logger.info(f"Line {line_id} flagged by {request.username}: '{line.text}'")

        return {
            "message": "Line flagged for review",
            "line_id": line_id,
            "line_text": line.text
        }

