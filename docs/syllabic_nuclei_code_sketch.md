# Sketch: syllabic-nucleus detection in `syllabifier.py`

Status: **sketch.** Proposed helpers for promoting a trailing `/l n r/` to a
syllabic nucleus (the MVP described in `syllabic_consonant_nuclei.md`). Depends
on the sonority data in `sonority_data_sketch.md`.

```python
# dutch_syllabifier/syllabifier.py

def _rank(label):
    '''Sonority rank of a consonant, or None if it is not a consonant
    (vowels/diphthongs have no rank, so callers read None as "not a consonant").'''
    if label is None:
        return None
    return phonology.SONORITY.get(phonology.canonical_label(label))


def _is_sonority_peak(labels, i):
    '''True if labels[i] is a local sonority peak, so it can be a syllabic nucleus.

    A peak rises in sonority from the segment on its left and does not fall below
    a more sonorous segment on its right (a word edge counts as falling). Because
    a vowel neighbour has no consonant rank, a consonant is never a peak next to
    a vowel -- that vowel is the real nucleus.
    '''
    peak = _rank(labels[i])
    left = _rank(labels[i - 1]) if i > 0 else None
    right = _rank(labels[i + 1]) if i + 1 < len(labels) else None
    rises_from_left = left is not None and left < peak
    holds_over_right = right is None or right <= peak
    return rises_from_left and holds_over_right


def _syllabic_nuclei(labels, vowels):
    '''Indices of trailing /l n r/ to treat as syllabic nuclei -- reduced,
    schwa-less syllables such as appel ['ɑ','p','l'] -> ɑ . pl̩.

    Conservative MVP: scan only the consonant tail after the last vowel, right
    to left, and promote the first sonorant that is a local sonority peak. At
    most one promotion per word.
    labels                  full list of IPA labels
    vowels                  indices of the true vowel/diphthong nuclei
    '''
    last_vowel = vowels[-1] if vowels else -1
    tail = range(len(labels) - 1, last_vowel, -1)       # after last vowel, R->L
    for i in tail:
        if labels[i] in data.SYLLABIC_SONORANTS and _is_sonority_peak(labels, i):
            return [i]
    return []
```

## Note: consider moving this onto the `Phone` class

These helpers pass bare label lists around and look ranks up by string. It may
be cleaner to explore enriching the `Phone` class instead, e.g.:

- a `Phone.sonority` property (and `is_nucleus` / `is_syllabic_sonorant`), so a
  phone carries its own phonological features rather than every function doing a
  `phonology.SONORITY` lookup on a string;
- `_is_sonority_peak` / `_syllabic_nuclei` could then operate on `Phone` objects
  and read `phone.sonority`, making the peak test read like the linguistics.

The current sketch is index-and-string based to match the existing code; the
`Phone`-based structure is worth evaluating before this lands.
