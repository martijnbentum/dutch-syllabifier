# Sonority data: implemented in `sonority.py`

Status: **implemented** (originally a sketch for `phonology.py`, since split
into `phone_inventory.py` and `phonotactics.py`). The scale backs the
syllabic-consonant nuclei plan (`syllabic_consonant_nuclei.md`) and the future
onset lint (`sonority_onset_fallback.md`).

## Design as implemented

The implementation deviates from the original sketch in three ways:

- **Named classes instead of anonymous tiers.** The data file maps class
  names to phones (`stop`, `fricative`, `nasal`, `liquid`, `glide`) instead
  of an ordered list of lists. Names keep the file self-describing and leave
  room for a finer split later (e.g. voiced vs voiceless fricatives, per
  `sonority_onset_fallback.md`).
- **Scale order lives in code.** `SONORITY_SCALE` in `sonority.py` ranks the
  class names, least to most sonorous; weights are the scale index. Symbol
  knowledge stays in JSON, relational knowledge stays in code.
- **Vowels are on the scale.** The `vowel` class (top of the scale) is derived
  from the nucleus inventory (vowels + diphthongs), so it needs no data entry
  and adding a vowel never touches sonority data. The original consonant-only
  scope is gone: "is a consonant" tests must use `is_nucleus(...)`, not
  membership in the sonority table (which now covers all known phones).

## Data file

```json
// dutch_syllabifier/data/sonority_classes.json
{
  "stop":      ["p", "b", "t", "d", "k", "ɡ"],
  "fricative": ["f", "v", "s", "z", "ʃ", "ʒ", "x", "ɣ", "h"],
  "nasal":     ["m", "n", "ŋ"],
  "liquid":    ["l", "r"],
  "glide":     ["ʋ", "j"]
}
```

Import-time validation (`_validate_sonority_classes`) requires the class
names to match the consonant part of `SONORITY_SCALE`, each phone to appear
in exactly one class, and the classified phones to equal the consonant
inventory exactly -- drift between the data files is a loud import error.

## API

```python
sonority_class('p')                 # 'stop'
sonority_class('w')                 # 'glide'  (alias -> 'ʋ')
sonority_class('ɛi')                # 'vowel'
sonority_weight('l')                # 3
sonority_classes(['s', 't', 'r'])   # ['fricative', 'stop', 'liquid']
sonority_weights(['s', 't', 'aː'])  # [1, 0, 5]
```

## Still open (for the syllabic-nuclei work)

- **`SYLLABIC_SONORANTS` is not implemented.** The curated subset of
  sonorants that may become a syllabic nucleus (`l n r`, excluding `/ŋ/`,
  `/m/` optional) belongs to the syllabic-nuclei feature, not the scale.
