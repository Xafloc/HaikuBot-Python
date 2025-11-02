"""SQLAlchemy database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    UniqueConstraint, Index, Text
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Line(Base):
    """Individual 5 or 7 syllable line.
    
    Can be auto-collected from IRC or manually submitted by editors.
    """
    __tablename__ = "lines"
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    syllable_count = Column(Integer, nullable=False)  # 5 or 7
    server = Column(String(100), nullable=False)
    channel = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    source = Column(String(20), nullable=False)  # 'auto' or 'manual'
    placement = Column(String(10), nullable=True)  # 'any', 'first', 'last', or NULL (for 7-syl)
    approved = Column(Boolean, default=True)
    
    # Indexes for query performance
    __table_args__ = (
        UniqueConstraint('text', name='uq_line_text', sqlite_on_conflict='IGNORE'),
        Index('idx_syllable_placement', 'syllable_count', 'placement'),
        Index('idx_server_channel', 'server', 'channel'),
        Index('idx_username', 'username'),
    )
    
    def __repr__(self):
        return f"<Line(id={self.id}, text='{self.text[:30]}...', syl={self.syllable_count})>"


class GeneratedHaiku(Base):
    """A complete haiku generated from three lines.
    
    References three Line records to form a 5-7-5 haiku.
    """
    __tablename__ = "generated_haikus"
    
    id = Column(Integer, primary_key=True)
    line1_id = Column(Integer, ForeignKey('lines.id'), nullable=False)
    line2_id = Column(Integer, ForeignKey('lines.id'), nullable=False)
    line3_id = Column(Integer, ForeignKey('lines.id'), nullable=False)
    full_text = Column(Text, nullable=False)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    triggered_by = Column(String(100), nullable=False)
    server = Column(String(100), nullable=False)
    channel = Column(String(100), nullable=False)
    
    # Relationships
    line1 = relationship("Line", foreign_keys=[line1_id])
    line2 = relationship("Line", foreign_keys=[line2_id])
    line3 = relationship("Line", foreign_keys=[line3_id])
    votes = relationship("Vote", back_populates="haiku", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_generated_at', 'generated_at'),
        Index('idx_triggered_by', 'triggered_by'),
    )
    
    def __repr__(self):
        return f"<GeneratedHaiku(id={self.id}, text='{self.full_text[:40]}...')>"
    
    @property
    def vote_count(self):
        """Get the number of votes for this haiku."""
        return len(self.votes)


class Vote(Base):
    """Vote for a generated haiku.
    
    One vote per username per haiku.
    """
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True)
    haiku_id = Column(Integer, ForeignKey('generated_haikus.id'), nullable=False)
    username = Column(String(100), nullable=False)
    voted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship
    haiku = relationship("GeneratedHaiku", back_populates="votes")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('haiku_id', 'username', name='uq_vote_haiku_user'),
        Index('idx_voted_at', 'voted_at'),
    )
    
    def __repr__(self):
        return f"<Vote(haiku_id={self.haiku_id}, username='{self.username}')>"


class User(Base):
    """User authorization and preferences.
    
    Tracks user roles and privacy preferences.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), nullable=False, default='public')  # 'public', 'editor', 'admin'
    opted_out = Column(Boolean, default=False)  # Privacy: opt out of auto-collection
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_role', 'role'),
        Index('idx_opted_out', 'opted_out'),
    )
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"
    
    def can_submit(self) -> bool:
        """Check if user can manually submit lines."""
        return self.role in ['editor', 'admin']
    
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == 'admin'


class Server(Base):
    """IRC server configuration.

    Mirrors config.yaml but stored in DB for runtime management.
    """
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    host = Column(String(200), nullable=False)
    port = Column(Integer, nullable=False)
    ssl = Column(Boolean, default=False)
    nick = Column(String(50), nullable=False)
    password = Column(String(200), nullable=True)
    channels = Column(Text, nullable=False)  # JSON array as string
    enabled = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Server(name='{self.name}', host='{self.host}')>"


class Acronym(Base):
    """Known acronyms and their syllable counts.

    Used to properly count syllables for internet slang and abbreviations.
    When an acronym is pronounced letter-by-letter (e.g., 'irl' = 'i-r-l'),
    the syllable count is usually the number of letters.
    """
    __tablename__ = "acronyms"

    id = Column(Integer, primary_key=True)
    acronym = Column(String(20), unique=True, nullable=False)
    syllable_count = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)  # Optional: what it stands for

    # Indexes
    __table_args__ = (
        Index('idx_acronym', 'acronym'),
    )

    def __repr__(self):
        return f"<Acronym(acronym='{self.acronym}', syllables={self.syllable_count})>"

