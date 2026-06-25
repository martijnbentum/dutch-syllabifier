# Dutch syllabification rules (version 1)

These notes describe the phonological rules used by `dutch_syllabifier`. The
package operates on IPA phone sequences only. It ignores spelling and
morphology.

## Phone representation

* Input is always a list of phone symbols (never a split string).
* Diphthongs are single phones even when written with multiple characters,
  e.g. `ɛi`, `œy`, `ɑu`.
* `/sx/` as in *schild* is two phones: `['s', 'x']`.
* `/st/` is both a legal onset cluster (*straat*) and part of legal coda
  clusters (*herfst*).
* `w` is accepted on input as an alias of `ʋ` (it is not a separate Dutch
  phoneme); it is normalised to `ʋ` before any lookup.
* Vowel length is optional: tense vowels are accepted with or without `ː`
  (`eː` ≡ `e`, `aː` ≡ `a`). Length never affects a syllable boundary, so the
  two forms are interchangeable as nuclei.

## Nuclei

* Vowels (`vowels.json`) and diphthongs (`diphthongs.json`) are nuclei.
* A legal syllable has exactly one nucleus.

## Post-vocalic glides

Transcribe an offglide as a consonant, not as a second vowel, so that it does
not form a spurious extra nucleus:

* `/j/` after a vowel, as in *aai*, *ooi*, *oei*:
  *fraai* `['f', 'r', 'aː', 'j']`, *mooi* `['m', 'oː', 'j']`.
* `/ʋ/` after a vowel, as in *eeuw*, *ieuw*, *uw*:
  *nieuw* `['n', 'i', 'ʋ']`, *ruw* `['r', 'y', 'ʋ']` (input `w` is accepted and
  normalised to `ʋ`).

`/j/` and `/ʋ/` are legal codas. The vowel symbols `i`, `u`, etc. are reserved
for nuclei. The three true diphthongs `ɛi`, `œy`, `ɑu` remain single nucleus
phones.

## Maximal Onset Principle

Between two vowel nuclei, assign the largest possible consonant cluster to the
onset of the following syllable, provided that this onset is legal in Dutch
(`legal_onsets.json`). The remaining consonants belong to the coda of the
preceding syllable.

Consonants before the first nucleus always belong to the onset of the first
syllable. Consonants after the last nucleus always belong to the coda of the
last syllable.

### Examples

```
['t', 'aː', 'f', 'ə', 'l']      -> taː . fəl
['ɑ', 'p', 'r', 'ɪ', 'l']       -> ɑ . prɪl   (/pr/ is a legal onset)
['s', 't', 'r', 'aː', 't']      -> straːt     (/str/ legal onset, /t/ legal coda)
['h', 'ɛ', 'r', 'f', 's', 't']  -> hɛrfst     (complex coda /rfst/)
```

## Onset legality

An onset is legal when it is empty or present in `legal_onsets.json`. All single
consonants except `ŋ` are legal onsets. Clusters are restricted to the curated
native Dutch inventory plus a few common loan clusters.

## Coda legality

Coda validation is **conservative and partial** in version 1. A coda is treated
as legal when it is empty or present in `legal_codas.json`. The list covers the
common Dutch codas and selected complex clusters (e.g. `/rfst/` in *herfst*),
but it is not exhaustive. Voiced obstruents are excluded from codas because of
Dutch final devoicing.

Because the list is incomplete, coda checking is **non-fatal**: an unlisted coda
is always tolerated. `is_legal_syllable` (which returns a plain `bool`) never
rejects a syllable on coda grounds alone, and `check_syllabification` judges
syllable boundaries from nucleus count and onset legality only — never from coda
membership. There is intentionally no strict-coda mode; callers that need to
detect an unlisted coda can inspect `Legality.judge(syllable).unlisted_coda`.

## Out of scope (version 1)

* Orthography and morphology.
* Compound and prefix boundaries.
* Loanword, name, and dialect permissiveness.
* Probabilistic or corpus-derived analyses.
