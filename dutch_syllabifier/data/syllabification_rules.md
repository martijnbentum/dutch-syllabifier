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

## Nuclei

* Vowels (`vowels.json`) and diphthongs (`diphthongs.json`) are nuclei.
* A legal syllable has exactly one nucleus.

## Post-vocalic glides

Transcribe an offglide as a consonant, not as a second vowel, so that it does
not form a spurious extra nucleus:

* `/j/` after a vowel, as in *aai*, *ooi*, *oei*:
  *fraai* `['f', 'r', 'aː', 'j']`, *mooi* `['m', 'oː', 'j']`.
* `/w/` after a vowel, as in *eeuw*, *ieuw*, *uw*:
  *nieuw* `['n', 'i', 'w']`, *ruw* `['r', 'y', 'w']`.

`/j/` and `/w/` are legal codas. The vowel symbols `i`, `u`, etc. are reserved
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

Because the list is incomplete, coda checking is **non-fatal by default**:
`is_legal_syllable` does not reject a syllable on coda grounds alone (it returns
``ok`` with a note in the reason), and `check_syllabification` judges syllable
boundaries from nucleus count and onset legality only — never from coda
membership. Pass `strict_coda=True` to `is_legal_syllable` to make an unlisted
coda fail.

## Out of scope (version 1)

* Orthography and morphology.
* Compound and prefix boundaries.
* Loanword, name, and dialect permissiveness.
* Probabilistic or corpus-derived analyses.
