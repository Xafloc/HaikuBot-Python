#!/usr/bin/env python3
"""Test hybrid syllable counting approach with multiple libraries."""

import sys
sys.path.insert(0, '.')

# Test imports to see what's available
available_libraries = []

# Test pysyllables
try:
    from pysyllables import get_syllable_count
    available_libraries.append("pysyllables")
    print("✓ pysyllables available")
except ImportError:
    print("✗ pysyllables NOT installed (pip install pysyllables)")
    get_syllable_count = None

# Test meooow25's syllable library
try:
    import syllable as meooow_syllable
    available_libraries.append("syllable (meooow25)")
    print("✓ syllable (meooow25) available")
except ImportError:
    print("✗ syllable (meooow25) NOT installed (pip install syllable)")
    meooow_syllable = None

# Test current libraries
try:
    from syllables import estimate as syllables_estimate
    available_libraries.append("syllables")
    print("✓ syllables available")
except ImportError:
    print("✗ syllables NOT available")
    syllables_estimate = None

try:
    import pyphen
    _hyphenator = pyphen.Pyphen(lang='en_US')
    available_libraries.append("pyphen")
    print("✓ pyphen available")
except ImportError:
    print("✗ pyphen NOT available")
    _hyphenator = None

print(f"\nAvailable libraries: {len(available_libraries)}/4\n")

# Define counting functions
def count_pysyllables(word):
    """Count using pysyllables (CMU dict lookup)."""
    if get_syllable_count is None:
        return None
    try:
        return get_syllable_count(word.lower())
    except:
        return None

def count_meooow_syllable(word):
    """Count using meooow25's ML model."""
    if meooow_syllable is None:
        return None
    try:
        return meooow_syllable.count(word.lower())
    except:
        return None

def count_syllables_lib(word):
    """Count using syllables library."""
    if syllables_estimate is None:
        return None
    try:
        return max(0, syllables_estimate(word.lower()))
    except:
        return None

def count_pyphen(word):
    """Count using pyphen."""
    if _hyphenator is None:
        return None
    try:
        hyphenated = _hyphenator.inserted(word.lower())
        if hyphenated:
            return hyphenated.count('-') + 1
    except:
        pass
    return None

def count_hybrid(word):
    """Hybrid approach: pysyllables → meooow25 → syllables → pyphen."""
    # Try pysyllables first (100% accurate for known words)
    count = count_pysyllables(word)
    if count is not None:
        return count, "pysyllables"

    # Try meooow25's ML model (95% accurate)
    count = count_meooow_syllable(word)
    if count is not None and count > 0:
        return count, "meooow25"

    # Try syllables library (66% on test)
    count = count_syllables_lib(word)
    if count is not None and count > 0:
        return count, "syllables"

    # Try pyphen as last resort
    count = count_pyphen(word)
    if count is not None and count > 0:
        return count, "pyphen"

    # Heuristic fallback
    return 1, "heuristic"

def count_phrase_hybrid(phrase):
    """Count syllables in phrase using hybrid approach."""
    import re
    words = re.split(r'[\s\-]+', re.sub(r'[^\w\s\-]', '', phrase))
    total = 0
    details = []
    for word in words:
        if word:
            count, method = count_hybrid(word)
            total += count
            details.append(f"{word}={count}({method})")
    return total, details

# Test phrases from screenshot
test_phrases = [
    ("overpowering it all", 7),
    ("overpowering", 5),
    ("confused by reality", 5),
    ("time can be irrelavent", 7),
    ("clarification required", 7),
    ("entering denial phase", 7),
]

print("=" * 100)
print("HYBRID APPROACH TEST")
print("=" * 100)
print(f"{'Phrase':<30} {'Expected':<10} {'Hybrid':<10} {'Result':<8} {'Details'}")
print("=" * 100)

correct = 0
for phrase, expected in test_phrases:
    actual, details = count_phrase_hybrid(phrase)
    match = "✓" if actual == expected else "✗"
    if actual == expected:
        correct += 1

    print(f"{phrase:<30} {expected:<10} {actual:<10} {match:<8} {', '.join(details)}")

print("=" * 100)
print(f"Hybrid Accuracy: {correct}/{len(test_phrases)} ({correct*100//len(test_phrases)}%)")
print("=" * 100)

# Also test individual word comparisons
print("\nDetailed word analysis for 'overpowering':")
print("-" * 70)
word = "overpowering"
print(f"pysyllables:      {count_pysyllables(word)}")
print(f"meooow25:         {count_meooow_syllable(word)}")
print(f"syllables:        {count_syllables_lib(word)}")
print(f"pyphen:           {count_pyphen(word)}")
print(f"EXPECTED:         5")
