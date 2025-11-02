"""Syllable counting using multiple methods for accuracy."""

import re
import logging
from typing import Optional
import pyphen
from syllables import estimate as syllables_estimate

logger = logging.getLogger(__name__)

# Initialize pyphen dictionary for English
_hyphenator = pyphen.Pyphen(lang='en_US')


def count_syllables(text: str) -> int:
    """Count syllables in text using multiple methods.
    
    Uses both pyphen (hyphenation-based) and syllables library,
    with fallback heuristics for edge cases.
    
    Args:
        text: Text to count syllables in
        
    Returns:
        Total syllable count
    """
    if not text or not text.strip():
        return 0
    
    # Clean and normalize text
    text = text.strip().lower()

    # Remove punctuation but keep spaces and hyphens (for compound words)
    text = re.sub(r'[^\w\s\-]', '', text)

    # Split into words (split on spaces and hyphens)
    words = re.split(r'[\s\-]+', text)
    
    if not words:
        return 0
    
    total = 0
    
    for word in words:
        if not word:
            continue

        # Try both methods
        syllables_count = _count_syllables_library(word)
        pyphen_count = _count_syllables_pyphen(word)

        # Use pyphen first (more accurate for common words like "going", "earlier")
        # Fall back to syllables library, then heuristic
        if pyphen_count > 0:
            word_count = pyphen_count
        elif syllables_count > 0:
            word_count = syllables_count
        else:
            # Fallback to heuristic method
            word_count = _count_syllables_heuristic(word)

        total += word_count

        logger.debug(f"Word: '{word}' -> syllables={syllables_count}, "
                    f"pyphen={pyphen_count}, chosen={word_count}")
    
    return total


def _count_syllables_pyphen(word: str) -> int:
    """Count syllables using pyphen hyphenation.
    
    Args:
        word: Single word
        
    Returns:
        Syllable count (0 if unable to determine)
    """
    try:
        hyphenated = _hyphenator.inserted(word)
        if hyphenated:
            # Count hyphens + 1 = syllable count
            return hyphenated.count('-') + 1
    except Exception as e:
        logger.debug(f"pyphen failed for '{word}': {e}")
    
    return 0


def _count_syllables_library(word: str) -> int:
    """Count syllables using syllables library.
    
    Args:
        word: Single word
        
    Returns:
        Syllable count (0 if unable to determine)
    """
    try:
        count = syllables_estimate(word)
        return max(0, count)
    except Exception as e:
        logger.debug(f"syllables library failed for '{word}': {e}")
    
    return 0


def _count_syllables_heuristic(word: str) -> int:
    """Count syllables using heuristic rules (fallback).
    
    Basic algorithm:
    - Count vowel groups
    - Adjust for silent 'e'
    - Minimum of 1 syllable per word
    
    Args:
        word: Single word
        
    Returns:
        Estimated syllable count
    """
    if not word:
        return 0
    
    word = word.lower()
    
    # Count vowel groups
    vowels = "aeiouy"
    syllable_count = 0
    previous_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel
    
    # Adjust for silent 'e'
    if word.endswith('e') and syllable_count > 1:
        syllable_count -= 1
    
    # Adjust for 'le' ending
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        syllable_count += 1
    
    # Every word has at least one syllable
    return max(1, syllable_count)


def is_haiku_line(text: str, target_syllables: int) -> bool:
    """Check if text matches target syllable count.
    
    Args:
        text: Text to check
        target_syllables: Target syllable count (5 or 7)
        
    Returns:
        True if text has exactly target_syllables syllables
    """
    return count_syllables(text) == target_syllables


def validate_haiku(line1: str, line2: str, line3: str) -> tuple[bool, Optional[str]]:
    """Validate that three lines form a proper 5-7-5 haiku.
    
    Args:
        line1: First line (should be 5 syllables)
        line2: Second line (should be 7 syllables)
        line3: Third line (should be 5 syllables)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    counts = [
        count_syllables(line1),
        count_syllables(line2),
        count_syllables(line3)
    ]
    
    if counts[0] != 5:
        return False, f"Line 1 has {counts[0]} syllables (expected 5)"
    
    if counts[1] != 7:
        return False, f"Line 2 has {counts[1]} syllables (expected 7)"
    
    if counts[2] != 5:
        return False, f"Line 3 has {counts[2]} syllables (expected 5)"
    
    return True, None

