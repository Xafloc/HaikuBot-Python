#!/usr/bin/env python3
"""Compare python-cmudict library against current libraries."""

import sys
sys.path.insert(0, '.')

import cmudict
import pyphen
from syllables import estimate as syllables_estimate

# Initialize pyphen
_hyphenator = pyphen.Pyphen(lang='en_US')

# Load CMU dict
d = cmudict.dict()

def count_pyphen(word):
    """Count using pyphen."""
    try:
        hyphenated = _hyphenator.inserted(word.lower())
        if hyphenated:
            return hyphenated.count('-') + 1
    except:
        pass
    return 0

def count_syllables_lib(word):
    """Count using syllables library."""
    try:
        return max(0, syllables_estimate(word.lower()))
    except:
        return 0

def count_cmudict(word):
    """Count using python-cmudict library."""
    try:
        phonemes = d.get(word.lower())
        if phonemes:
            # Take first pronunciation, count stress markers (0,1,2)
            count = sum(1 for phone in phonemes[0] if phone[-1].isdigit())
            return count
    except:
        pass
    return 0

def count_phrase(phrase, counter_func):
    """Count syllables in phrase using given counter."""
    import re
    words = re.split(r'[\s\-]+', re.sub(r'[^\w\s\-]', '', phrase))
    total = 0
    for word in words:
        if word:
            count = counter_func(word)
            if count > 0:
                total += count
    return total

# Test phrases from screenshot
test_phrases = [
    ("overpowering it all", 7),
    ("overpowering", 5),
    ("confused by reality", 5),
    ("time can be irrelavent", 7),
    ("clarification required", 7),
    ("entering denial phase", 7),
]

print("Library Accuracy Comparison")
print("=" * 90)
print(f"{'Phrase':<30} {'Correct':<8} {'pyphen':<8} {'syllables':<10} {'cmudict':<8}")
print("=" * 90)

pyphen_correct = 0
syllables_correct = 0
cmudict_correct = 0

for phrase, correct in test_phrases:
    p_count = count_phrase(phrase, count_pyphen)
    s_count = count_phrase(phrase, count_syllables_lib)
    c_count = count_phrase(phrase, count_cmudict)

    p_mark = "✓" if p_count == correct else "✗"
    s_mark = "✓" if s_count == correct else "✗"
    c_mark = "✓" if c_count == correct else "✗"

    if p_count == correct: pyphen_correct += 1
    if s_count == correct: syllables_correct += 1
    if c_count == correct: cmudict_correct += 1

    print(f"{phrase:<30} {correct:<8} {p_count} {p_mark:<6} {s_count} {s_mark:<8} {c_count} {c_mark:<6}")

print("=" * 90)
print(f"{'Accuracy:':<30} {'':8} {pyphen_correct}/6 ({pyphen_correct*100//6}%)  "
      f"{syllables_correct}/6 ({syllables_correct*100//6}%)    "
      f"{cmudict_correct}/6 ({cmudict_correct*100//6}%)")
print("=" * 90)

# Also test word-by-word for one problematic phrase
print("\nWord-by-word breakdown for 'overpowering':")
print("-" * 70)
word = "overpowering"
print(f"pyphen:    {count_pyphen(word)}")
print(f"syllables: {count_syllables_lib(word)}")
print(f"cmudict:   {count_cmudict(word)}")
print(f"CORRECT:   5 (o-ver-pow-er-ing)")
