"""Admin API routes for HaikuBot maintenance."""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

from ..config import get_config
from ..database import get_session, Line, GeneratedHaiku
from ..haiku.syllable_counter import count_syllables

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# Request/Response Models
class LoginRequest(BaseModel):
    """Admin login request."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Admin login response."""
    success: bool
    token: str


class LineUpdate(BaseModel):
    """Line update request."""
    text: Optional[str] = None
    syllable_count: Optional[int] = None
    placement: Optional[str] = None


class SyllableCheckResult(BaseModel):
    """Result of syllable check for a line."""
    id: int
    text: str
    stored_syllables: int
    actual_syllables: int
    matches: bool
    username: str
    channel: str
    timestamp: str
    method: str  # Which counting method was used


# Simple authentication (just checks credentials from config)
def verify_admin_token(authorization: str = Header(None)) -> bool:
    """Verify admin token from Authorization header.

    Token format: "Bearer username:password"
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization[7:]  # Remove "Bearer "
    try:
        username, password = token.split(":", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    config = get_config()
    if username != config.admin.username or password != config.admin.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return True


@router.post("/login")
def admin_login(request: LoginRequest) -> LoginResponse:
    """Admin login endpoint.

    Returns a simple token (username:password) for subsequent requests.
    """
    config = get_config()

    if request.username != config.admin.username or request.password != config.admin.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Simple token: just base64 would be better, but keeping it simple
    token = f"{request.username}:{request.password}"

    return LoginResponse(success=True, token=token)


@router.get("/lines")
def list_lines(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    syllable_count: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    _authenticated: bool = Depends(verify_admin_token)
) -> List[dict]:
    """List lines with optional filters.

    Query params:
    - start_date: ISO format date (YYYY-MM-DD)
    - end_date: ISO format date (YYYY-MM-DD)
    - syllable_count: Filter by syllable count
    - skip: Offset for pagination
    - limit: Max results to return
    """
    with get_session() as session:
        query = session.query(Line)

        # Apply filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(Line.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(Line.timestamp <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")

        if syllable_count:
            query = query.filter(Line.syllable_count == syllable_count)

        # Get results
        lines = query.order_by(Line.timestamp.desc()).offset(skip).limit(limit).all()

        return [
            {
                "id": line.id,
                "text": line.text,
                "syllable_count": line.syllable_count,
                "placement": line.placement,
                "username": line.username,
                "channel": line.channel,
                "server": line.server,
                "source": line.source,
                "timestamp": line.timestamp.isoformat(),
            }
            for line in lines
        ]


@router.delete("/lines/{line_id}")
def delete_line(
    line_id: int,
    cascade: bool = False,
    _authenticated: bool = Depends(verify_admin_token)
) -> dict:
    """Delete a line by ID.

    Args:
        line_id: ID of line to delete
        cascade: If True, also delete all haikus using this line
    """
    with get_session() as session:
        line = session.query(Line).filter(Line.id == line_id).first()

        if not line:
            raise HTTPException(status_code=404, detail="Line not found")

        # Check if line is used in any haikus
        haikus_using_line = session.query(GeneratedHaiku).filter(
            (GeneratedHaiku.line1_id == line_id) |
            (GeneratedHaiku.line2_id == line_id) |
            (GeneratedHaiku.line3_id == line_id)
        ).all()

        if haikus_using_line and not cascade:
            # Return error with details about haikus using this line
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Line is used in haikus",
                    "message": f"This line is used in {len(haikus_using_line)} haiku(s)",
                    "haiku_count": len(haikus_using_line),
                    "haiku_ids": [h.id for h in haikus_using_line],
                    "line_text": line.text
                }
            )

        # If cascade, delete all haikus using this line first
        if cascade and haikus_using_line:
            for haiku in haikus_using_line:
                session.delete(haiku)
            logger.info(f"Admin cascade deleted {len(haikus_using_line)} haiku(s) using line {line_id}")

        session.delete(line)
        session.commit()

        logger.info(f"Admin deleted line {line_id}: {line.text}")

        return {
            "success": True,
            "message": f"Deleted line {line_id}",
            "cascade_deleted_haikus": len(haikus_using_line) if cascade else 0
        }


@router.patch("/lines/{line_id}")
def update_line(
    line_id: int,
    update: LineUpdate,
    _authenticated: bool = Depends(verify_admin_token)
) -> dict:
    """Update a line by ID."""
    with get_session() as session:
        line = session.query(Line).filter(Line.id == line_id).first()

        if not line:
            raise HTTPException(status_code=404, detail="Line not found")

        # Update fields
        if update.text is not None:
            line.text = update.text
        if update.syllable_count is not None:
            line.syllable_count = update.syllable_count
        if update.placement is not None:
            line.placement = update.placement

        session.commit()

        logger.info(f"Admin updated line {line_id}")

        return {
            "success": True,
            "line": {
                "id": line.id,
                "text": line.text,
                "syllable_count": line.syllable_count,
                "placement": line.placement,
            }
        }


@router.delete("/haikus/{haiku_id}")
def delete_haiku(
    haiku_id: int,
    _authenticated: bool = Depends(verify_admin_token)
) -> dict:
    """Delete a generated haiku by ID."""
    with get_session() as session:
        haiku = session.query(GeneratedHaiku).filter(GeneratedHaiku.id == haiku_id).first()

        if not haiku:
            raise HTTPException(status_code=404, detail="Haiku not found")

        session.delete(haiku)
        session.commit()

        logger.info(f"Admin deleted haiku {haiku_id}")

        return {"success": True, "message": f"Deleted haiku {haiku_id}"}


@router.post("/lines/{line_id}/validate")
def validate_line_syllables(
    line_id: int,
    _authenticated: bool = Depends(verify_admin_token)
) -> dict:
    """Mark a line as human-validated (syllable count is correct despite algorithm disagreement)."""
    with get_session() as session:
        line = session.query(Line).filter(Line.id == line_id).first()

        if not line:
            raise HTTPException(status_code=404, detail="Line not found")

        line.human_validated = True
        session.commit()

        logger.info(f"Admin validated line {line_id}: '{line.text}'")

        return {
            "success": True,
            "line_id": line_id,
            "message": "Line marked as validated"
        }


@router.post("/syllable-check")
def check_syllables(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    method: str = "perl",
    include_validated: bool = False,
    _authenticated: bool = Depends(verify_admin_token)
) -> List[SyllableCheckResult]:
    """Check syllable counts for lines in date range.

    Args:
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)
        method: Syllable counting method - "perl" (most accurate) or "python"
        include_validated: Include human-validated lines in results (default: False)

    Returns lines where stored syllable count doesn't match actual count.
    """
    with get_session() as session:
        query = session.query(Line)

        # Apply date filters
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(Line.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(Line.timestamp <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")

        # Filter human-validated lines unless explicitly included
        if not include_validated:
            query = query.filter(Line.human_validated == False)

        lines = query.all()

        # Check each line
        results = []
        for line in lines:
            actual_count = count_syllables(line.text, method=method)

            # Only include if counts don't match
            if actual_count != line.syllable_count:
                results.append(SyllableCheckResult(
                    id=line.id,
                    text=line.text,
                    stored_syllables=line.syllable_count,
                    actual_syllables=actual_count,
                    matches=False,
                    username=line.username,
                    channel=line.channel,
                    timestamp=line.timestamp.isoformat(),
                    method=method
                ))

        return results
