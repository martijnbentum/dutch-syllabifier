# dutch_syllabifier

`dutch_syllabifier` is a small, dependency-free Python package for Dutch
phonological syllabification. It works on IPA phone sequences and applies strict
Dutch phonotactics. It ignores spelling and morphology.

It can:

1. suggest a syllabification for a Dutch IPA phone sequence;
2. judge whether a single syllable is phonotactically legal in Dutch;
3. judge whether a sequence of syllables has correct syllable boundaries;
4. expose syllable phones through a `.phones` attribute.

## Install

```bash
pip install git+https://github.com/martijnbentum/dutch-syllabifier.git
```

or with uv:

```bash
uv pip install git+https://github.com/martijnbentum/dutch-syllabifier.git
```

After installation, import it as:

```python
import dutch_syllabifier
```

## Phone representation

* Input is always a **list of phone symbols**, never a split string.
* IPA symbols are used throughout.
* Diphthongs are single phones even when written with several characters,
  e.g. `ɛi`, `œy`, `ɑu`.
* `/sx/` as in *schild* is two phones: `['s', 'x']`.
* `/st/` is both a legal onset (*straat*) and part of legal codas (*herfst*).
* Post-vocalic glides are consonants, not vowels: use `/j/` (*fraai*
  `['f', 'r', 'aː', 'j']`) and `/w/` (*nieuw* `['n', 'i', 'w']`). This keeps a
  glide from forming a spurious second nucleus.

A phone may be an IPA string or any object with a `.label` attribute. A syllable
may be a `Syllable` object or any object with a `.phones` attribute.

## Core rule: Maximal Onset Principle

Between two vowel nuclei, the largest legal Dutch onset is assigned to the
following syllable; the remaining consonants form the coda of the preceding
syllable. See `dutch_syllabifier/data/syllabification_rules.md`.

## Usage

### Syllabify

```python
from dutch_syllabifier import syllabify

syllabify(['t', 'aː', 'f', 'ə', 'l'])
# [Syllable(['t', 'aː']), Syllable(['f', 'ə', 'l'])]

syllabify(['ɑ', 'p', 'r', 'ɪ', 'l'])
# [Syllable(['ɑ']), Syllable(['p', 'r', 'ɪ', 'l'])]

syllabify(['s', 't', 'r', 'aː', 't'])
# [Syllable(['s', 't', 'r', 'aː', 't'])]

syllabify(['h', 'ɛ', 'r', 'f', 's', 't'])
# [Syllable(['h', 'ɛ', 'r', 'f', 's', 't'])]
```

### Phone and Syllable objects

```python
from dutch_syllabifier import Phone, Syllable

p = Phone('m')
p.label
# 'm'

s = Syllable(['m', 'ɑ'])
s.phones
# ['m', 'ɑ']
s.label
# 'm ɑ'
```

### Check a single syllable

```python
from dutch_syllabifier import is_legal_syllable

is_legal_syllable(['s', 't', 'r', 'aː', 't']).ok
# True

is_legal_syllable(['l', 'p', 'ə']).ok   # /lp/ is not a legal onset
# False
```

### Check syllable boundaries

```python
from dutch_syllabifier import check_syllabification

check_syllabification([['ɑ', 'p'], ['r', 'ɪ', 'l']]).ok
# False  -> /pr/ is a legal onset, so maximal onset gives ɑ.prɪl

check_syllabification([['h', 'ɛ', 'l'], ['p', 'ə']]).ok
# True   -> /lp/ is not a legal onset but /p/ is

check_syllabification([['s', 't', 'r', 'aː', 't']]).ok
# True

check_syllabification([['h', 'ɛ', 'r', 'f', 's', 't']]).ok
# True   -> Dutch allows complex codas such as /rfst/
```

The result object exposes:

```python
result.ok          # bool
result.reason      # explanation
result.suggested   # suggested syllabification when boundaries are wrong
```

## Validating phraser segments

The package can validate segments coming from a
[phraser](https://github.com/martijnbentum/phraser) store (or any objects with
the same shape). It works purely by duck typing, so it adds **no dependency on
phraser**: a syllable only needs a `.phones` attribute (each phone exposing
`.label`), and a word or phrase only needs a `.syllables` attribute.

There are two tiers per segment:

* `is_valid_syllable` / `is_valid_word` / `is_valid_phrase` return a `bool`.
* `analyse_syllable` / `analyse_word` / `analyse_phrase` return a `Result`
  (`.ok`, `.reason`, `.suggested`).

```python
from dutch_syllabifier import (is_valid_word, is_valid_phrase,
    analyse_word, analyse_phrase)

# bool tier
is_valid_word(word)            # True if stored boundaries follow maximal onset
is_valid_phrase(phrase)        # True for the whole phrase

# detail tier
result = analyse_word(word)
result.ok                      # bool
result.reason                  # explanation
result.suggested               # suggested syllabification when boundaries differ
```

Word and phrase checks use the segment's `.syllables`, so a phrase is validated
as one sequence — boundaries that span **word boundaries** are checked too. Use
the phrase function rather than looping over words.

Both tiers are **total**: input the engine cannot check (an unknown phone label
or an empty segment) never raises here. The bool tier returns `False`; the
`analyse_*` tier returns a falsy `Result` whose `reason` starts with
`could not analyse:`, so an *uncheckable* segment stays distinguishable from an
*incorrect* one.

```python
analyse_word(empty_word).reason
# 'could not analyse: no syllables to check'
```

## Data files

Machine-readable phonotactic data ships inside the package:

```text
dutch_syllabifier/data/
  vowels.json
  diphthongs.json
  consonants.json
  legal_onsets.json
  illegal_onsets.json
  legal_codas.json
  syllabification_rules.md
```

## Scope and limitations (version 1)

* Operates only on phonological IPA phone sequences.
* Ignores spelling and morphology.
* Uses strict Dutch phonotactics.
* **Coda validation is conservative and partial**: codas are checked against a
  curated list that is not exhaustive. It is non-fatal by default —
  `is_legal_syllable` does not reject on coda alone (pass `strict_coda=True` to
  enforce it), and `check_syllabification` judges boundaries from onsets only.
* Unknown phone symbols raise a clear `ValueError`.

## Future refinements

* Optional morphology-aware syllabification for compounds and prefixed words.
* A permissive mode for loanwords, names, and dialectal variants.
* Optional support for other phone sets such as CGN/SAMPA or MAUS/BAS symbols.
* Optional probabilistic or corpus-derived syllabification when multiple
  analyses are possible.
