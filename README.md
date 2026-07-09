# dutch_syllabifier

`dutch_syllabifier` is a small, dependency-free Python package for Dutch
phonological syllabification. It works on IPA phone sequences and applies strict
Dutch phonotactics. It ignores spelling and morphology.

It can:

1. suggest a syllabification for a Dutch IPA phone sequence;
2. judge whether a single syllable is phonotactically legal, returning a
   `Legality` verdict with the reason;
3. judge whether a sequence of syllables has correct syllable boundaries
   (optionally respecting word boundaries for a phrase);
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
  `['f', 'r', 'aː', 'j']`) and `/ʋ/` (*nieuw* `['n', 'i', 'ʋ']`). This keeps a
  glide from forming a spurious second nucleus. `w` is accepted on input as an
  alias of `ʋ` (it is not a separate Dutch phoneme), so `['n', 'i', 'w']` works
  too.
* Vowel length marks are optional: tense vowels are accepted with or without
  `ː` (`eː` ≡ `e`, `aː` ≡ `a`), since length never changes a syllable boundary.

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

`is_legal_syllable` returns a plain `bool`:

```python
from dutch_syllabifier import is_legal_syllable

is_legal_syllable(['s', 't', 'r', 'aː', 't'])
# True

is_legal_syllable(['l', 'p', 'ə'])   # /lp/ is not a legal onset
# False
```

For the reason behind a judgment, use `Legality` (see below).

### Legality: the per-syllable verdict

`Legality.judge` returns a `Legality` describing *why* a syllable passes or
fails. It exposes one boolean flag per finding, so you branch on a stable
attribute instead of parsing a message:

```python
from dutch_syllabifier import Legality

v = Legality.judge(['l', 'p', 'ə'])
v.ok                # False  -- derived from the flags
v.illegal_onset     # True
v.reason            # 'illegal onset: l p'  (derived from the finding)
str(v)              # 'illegal onset: l p'

Legality.judge(['s', 't', 'r', 'aː', 't']).ok   # True
Legality.legal().ok                              # True (a passing verdict)
```

The findings are:

| flag              | meaning                                            | clears `ok`? |
| ----------------- | -------------------------------------------------- | ------------ |
| `no_nucleus`      | syllable has no vowel nucleus                      | yes          |
| `multiple_nuclei` | syllable has more than one nucleus                 | yes          |
| `illegal_onset`   | onset is not a legal Dutch onset cluster           | yes          |
| `unlisted_coda`   | coda is not in the vetted list (tolerated)         | no           |

`unlisted_coda` is **noted but tolerated**: it is set, yet `ok` stays `True`.
The coda list covers every CELEX-attested, sonority-valid word-final coda, so
this finding is rare and usually points at a loanword, a name, or a
transcription error (see Scope and limitations). `offending_phones` holds the
onset or coda that triggered the finding.

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

The result object derives `ok` and `reason` from its data and exposes:

```python
result.ok          # bool: all syllables legal and boundaries follow maximal onset
result.reason      # explanation (points at the first illegal syllable, else boundaries)
result.current     # the given segmentation as Syllable objects
result.suggested   # the maximal-onset segmentation as Syllable objects
result.uncheckable # True only for input that could not be analysed at all
```

Each syllable in `result.current` carries its own `.legality` verdict, so you
can inspect a specific syllable:

```python
r = check_syllabification([['ɑ'], ['l', 'p', 'ə']])
r.ok                            # False
r.current[1].legality.illegal_onset   # True
r.suggested                     # [Syllable(['ɑ', 'l']), Syllable(['p', 'ə'])]
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
  (`.ok`, `.reason`, `.suggested`, `.uncheckable`).

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

By default a phrase is treated as connected speech, so a consonant may
resyllabify across a word boundary (e.g. *het ei* → `hɛ.tɛi`). To keep each word
intact, pass `cross_word_boundaries=False`; then every word is syllabified on
its own and no boundary moves across words. This path reads the phrase's
`.words` (each a word with `.syllables`) instead of the flat `.syllables`.

```python
analyse_phrase(phrase)                              # hɛ.tɛi  (crosses boundary)
analyse_phrase(phrase, cross_word_boundaries=False) # hɛt.ɛi  (word-respecting)
```

Both tiers are **total**: input the engine cannot check (an unknown phone label
or an empty segment) never raises here. The bool tier returns `False`; the
`analyse_*` tier returns a falsy `Result` with `.uncheckable` set to `True`, so
an *uncheckable* segment stays distinguishable from an *incorrect* one (whose
`.uncheckable` is `False`). The `.reason` still explains it for humans.

```python
result = analyse_word(empty_word)
result.uncheckable
# True
result.reason
# 'could not analyse: no syllables to check'
```

## Learned syllabifiers (trained on CELEX)

Besides the rule-based `syllabify`, the package ships two **opt-in** models
trained on the syllable boundaries of the Dutch
[CELEX-2](https://github.com/martijnbentum/celex) lexicon. They do not replace
`syllabify`; maximal onset remains the default.

* `CountSyllabifier` — probabilistic maximal onset: a boundary scores as the
  smoothed log probability of the coda and onset clusters it creates, counted
  over CELEX syllables.
* `ClassifierSyllabifier` — an L1 logistic regression over a three-phone
  window around each candidate boundary, so it can pick up cues (e.g. compound
  boundaries) that pure phonotactics cannot.

Both decode under the same constraint as the rule engine: exactly one boundary
between two nuclei, so every syllable keeps exactly one nucleus. Both take the
same input as `syllabify` and return the same `Syllable` objects:

```python
from dutch_syllabifier import ClassifierSyllabifier, CountSyllabifier

model = ClassifierSyllabifier()          # loads the packaged weights
model.syllabify(['t', 'aː', 'f', 'ə', 'l'])
# [Syllable(['t', 'aː']), Syllable(['f', 'ə', 'l'])]
model.boundary_indices(['t', 'aː', 'f', 'ə', 'l'])
# [2]

CountSyllabifier().syllabify(['ɑ', 'p', 'r', 'ɪ', 'l'])
# [Syllable(['ɑ']), Syllable(['p', 'r', 'ɪ', 'l'])]
```

On a lemma-disjoint CELEX Dutch test set (word accuracy / boundary F1):

| model                   | word accuracy | boundary F1 |
| ----------------------- | ------------- | ----------- |
| maximal onset baseline  | 0.799         | 0.909       |
| `CountSyllabifier`      | 0.840         | 0.930       |
| `ClassifierSyllabifier` | 0.946         | 0.977       |

The gap between the baseline and the classifier is mostly morphology: CELEX
respects morpheme boundaries in compounds and prefixed words (*uit.ein.de* and
*loop.af.stand*, not maximal onset *ui.tein.de* and *loo.paf.stand*), which the
phone window can partly learn and pure phonotactics cannot.

The model artifacts are aggregate statistics (cluster counts and feature
weights) shipped as JSON in `dutch_syllabifier/data/`; the licensed CELEX
lexicon itself is not included. Inference is pure Python and needs no extra
dependencies.

### Retraining

Training code lives in `dutch_syllabifier/training/` and needs the `train`
dependency group (scikit-learn and a local `celex` checkout next to this
repository, with the licensed CELEX data):

```bash
uv sync --group train
.venv/bin/python -m dutch_syllabifier.training
```

This rewrites the two artifacts in `dutch_syllabifier/data/` and prints the
evaluation table above. Training skips multiword entries, words with a phone
that has no single-phone equivalent here (e.g. the loanword affricate `dʒ`)
and words where a syllable does not have exactly one nucleus; splits are
lemma-disjoint so inflectional families never straddle train and test.

## Data files

Machine-readable phonotactic data ships inside the package:

```text
dutch_syllabifier/data/
  vowels.json
  diphthongs.json
  consonants.json
  legal_onsets.json
  legal_codas.json
  syllabification_rules.md
  celex_onset_coda_counts.json      ← CountSyllabifier artifact
  celex_boundary_classifier.json    ← ClassifierSyllabifier artifact
```

## Scope and limitations (version 1)

* Operates only on phonological IPA phone sequences.
* Ignores spelling and morphology.
* Uses strict Dutch phonotactics.
* **Coda validation is non-fatal**: codas are checked against a vetted list
  covering every CELEX-attested, sonority-valid word-final coda. An unlisted
  coda sets `Legality.unlisted_coda` but does not clear `ok`, so
  `is_legal_syllable` never rejects on coda alone, and `check_syllabification`
  judges boundaries from onsets only. Expect this finding to be rare — mostly
  loanwords, names, and transcription errors.
* Unknown phone symbols raise a clear `ValueError`.

## Future refinements

* A strict mode that treats an unlisted coda as fatal, now that the coda list
  is vetted against CELEX.
* Optional morphology-aware syllabification for compounds and prefixed words.
* A permissive mode for loanwords, names, and dialectal variants.
* Optional support for other phone sets such as CGN/SAMPA or MAUS/BAS symbols.
* A CRF or other structured sequence model trained on CELEX, as a next step
  beyond the boundary classifier (the literature standard for this task).
* Handling ambisyllabic phones in the learned models.
