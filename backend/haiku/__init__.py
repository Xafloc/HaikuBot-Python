"""Haiku logic: syllable counting and generation."""

from .syllable_counter import count_syllables, validate_line_for_auto_collection
from .generator import generate_haiku, generate_haiku_for_user, generate_haiku_for_channel, get_haiku_stats

__all__ = [
    "count_syllables",
    "validate_line_for_auto_collection",
    "generate_haiku",
    "generate_haiku_for_user",
    "generate_haiku_for_channel",
    "get_haiku_stats",
]

