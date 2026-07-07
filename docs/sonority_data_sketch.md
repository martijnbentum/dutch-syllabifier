# Sketch: sonority data in `data.py`

Status: **sketch / first version.** This is a proposed *first* implementation of
a sonority scale as reference data, to back both the syllabic-consonant nuclei
(`syllabic_consonant_nuclei.md`) and the future onset lint
(`sonority_onset_fallback.md`). Tiers and scope below are a starting point and
will likely change as the onset rule is built out.

## Data file

```json
// dutch_syllabifier/data/sonority.json  (tiers, least -> most sonorous)
[
  ["p", "b", "t", "d", "k", "ɡ"],
  ["f", "v", "s", "z", "ʃ", "ʒ", "x", "ɣ", "h"],
  ["m", "n", "ŋ"],
  ["l", "r"],
  ["ʋ", "j"]
]
```

## `data.py` additions

```python
# sonority tiers, least -> most sonorous; rank is the tier index
_SONORITY_TIERS = _load_json('sonority.json')
SONORITY = {ph: rank for rank, tier in enumerate(_SONORITY_TIERS) for ph in tier}

# sonorants that may become a syllabic nucleus in reduced syllables (-el/-en/-er).
# A deliberate subset, not "all sonorants": excludes /ŋ/, optionally add 'm' (-em).
SYLLABIC_SONORANTS = ('l', 'n', 'r')


def _validate_sonority():
    '''Raise ValueError if any consonant lacks a sonority rank (or vice versa).'''
    missing = CONSONANTS - set(SONORITY)
    extra = set(SONORITY) - CONSONANTS
    if missing or extra:
        raise ValueError(
            f'sonority.json must rank exactly the consonants; '
            f'missing={sorted(missing)} extra={sorted(extra)}')


_validate_clusters()
_validate_sonority()


def sonority(label):
    '''Sonority rank of a consonant (higher = more sonorous). KeyError on a
    non-consonant, which callers use to mean "not a consonant".'''
    return SONORITY[canonical_label(label)]
```

## Notes / open questions for the next version

- **Consonant-only scope (deliberate, for now).** Vowels have no rank. The
  syllabic-nucleus peak test relies on `label in SONORITY` meaning "is a
  consonant", so a vowel neighbour correctly fails. When the onset lint needs a
  full scale, add a top vowel tier and switch that guard to `is_nucleus(...)`.
- **Tiers are coarse.** Five tiers (stop / fricative / nasal / liquid / glide)
  are enough for the syllabic-consonant peak test; the onset rule may want a
  finer split (e.g. voiced vs voiceless obstruents) and a tunable minimum
  sonority distance.
- **`SYLLABIC_SONORANTS` is curated, not derived.** It is intentionally not
  "every sonorant" -- `/ŋ/` is excluded and `/m/` is optional (-em: bezem).
