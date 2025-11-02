"""Syllable counting using multiple methods with voting for accuracy."""

import re
import logging
from typing import Optional, List
from collections import Counter
import pyphen
from syllables import estimate as syllables_estimate
import pronouncing

logger = logging.getLogger(__name__)

# Initialize pyphen dictionary for English
_hyphenator = pyphen.Pyphen(lang='en_US')

# Acronym cache - loaded on first use
_acronym_cache: Optional[dict] = None


def _load_acronym_cache() -> dict:
    """Load acronyms from database into memory cache.

    Returns:
        Dictionary mapping acronym to syllable count
    """
    global _acronym_cache

    if _acronym_cache is not None:
        return _acronym_cache

    _acronym_cache = {}

    try:
        from ..database import get_session, Acronym

        with get_session() as session:
            acronyms = session.query(Acronym).all()
            for acronym in acronyms:
                _acronym_cache[acronym.acronym.lower()] = acronym.syllable_count

        logger.info(f"Loaded {len(_acronym_cache)} acronyms into cache")
    except Exception as e:
        logger.warning(f"Failed to load acronym cache: {e}")
        _acronym_cache = {}

    return _acronym_cache


def _check_acronym(word: str) -> int:
    """Check if word is a known acronym and return syllable count.

    Args:
        word: Single word to check

    Returns:
        Syllable count if found in acronym database, 0 otherwise
    """
    cache = _load_acronym_cache()
    return cache.get(word.lower(), 0)


def _split_camelcase(word: str) -> List[str]:
    """Split CamelCase word into separate words.

    Examples:
        "EvilB" -> ["Evil", "B"]
        "DarkScience" -> ["Dark", "Science"]
        "hello" -> ["hello"] (no change)

    Args:
        word: Word that might be in CamelCase

    Returns:
        List of words after splitting
    """
    # Match pattern: lowercase followed by uppercase, or uppercase followed by uppercase+lowercase
    # This handles both "evilB" and "EvilB" and "XMLParser" patterns
    parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', word)

    if not parts:
        # No CamelCase detected, return original word
        return [word]

    # Check if we actually split anything
    joined = ''.join(parts)
    if joined.lower() == word.lower() and len(parts) > 1:
        # Successfully split CamelCase
        logger.debug(f"Split CamelCase: '{word}' -> {parts}")
        return parts

    # No split occurred, return original
    return [word]


def count_syllables(text: str) -> int:
    """Count syllables in text using multiple methods.

    Process:
    1. Check if word is a known acronym (from database)
    2. Split CamelCase words (e.g., "EvilB" -> "Evil" + "B")
    3. Use 3-way voting (pyphen, syllables, CMU dict) for accuracy
    4. Fallback to heuristic if all methods fail

    Args:
        text: Text to count syllables in

    Returns:
        Total syllable count
    """
    if not text or not text.strip():
        return 0

    # Clean and normalize text - but preserve original case for CamelCase detection
    text = text.strip()

    # Remove punctuation but keep spaces and hyphens (for compound words)
    # Keep original case for now
    cleaned = re.sub(r'[^\w\s\-]', '', text)

    # Split into words (split on spaces and hyphens)
    words = re.split(r'[\s\-]+', cleaned)

    if not words:
        return 0

    total = 0

    for word in words:
        if not word:
            continue

        # Priority 1: Check if it's a known acronym
        acronym_count = _check_acronym(word)
        if acronym_count > 0:
            total += acronym_count
            logger.debug(f"Word: '{word}' -> acronym={acronym_count}")
            continue

        # Priority 2: Try to split CamelCase
        parts = _split_camelcase(word)

        # Process each part (will be single word if no CamelCase)
        for part in parts:
            part_lower = part.lower()

            # Check if part is an acronym (e.g., "B" in "EvilB")
            acronym_count = _check_acronym(part_lower)
            if acronym_count > 0:
                total += acronym_count
                logger.debug(f"Part: '{part}' -> acronym={acronym_count}")
                continue

            # Try all three syllable counting methods
            syllables_count = _count_syllables_library(part_lower)
            pyphen_count = _count_syllables_pyphen(part_lower)
            cmu_count = _count_syllables_cmu(part_lower)

            # Voting logic: use majority consensus
            counts = []
            if pyphen_count > 0:
                counts.append(pyphen_count)
            if syllables_count > 0:
                counts.append(syllables_count)
            if cmu_count > 0:
                counts.append(cmu_count)

            if len(counts) == 0:
                # No library could count, use heuristic
                word_count = _count_syllables_heuristic(part_lower)
            elif len(counts) == 1:
                # Only one library returned a count, trust it
                word_count = counts[0]
            else:
                # Multiple libraries returned counts - use majority vote
                count_freq = Counter(counts)
                # Get the most common count (majority vote)
                word_count = count_freq.most_common(1)[0][0]

            total += word_count

            logger.debug(f"Part: '{part}' -> syllables={syllables_count}, "
                        f"pyphen={pyphen_count}, cmu={cmu_count}, chosen={word_count}")

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


def _count_syllables_cmu(word: str) -> int:
    """Count syllables using CMU Pronouncing Dictionary.

    Args:
        word: Single word

    Returns:
        Syllable count (0 if unable to determine)
    """
    try:
        # Get phonetic representations for the word
        phones = pronouncing.phones_for_word(word.lower())
        if phones:
            # Use the first pronunciation
            # CMU dict counts syllables by stress markers on vowels
            return pronouncing.syllable_count(phones[0])
    except Exception as e:
        logger.debug(f"CMU dict failed for '{word}': {e}")

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

