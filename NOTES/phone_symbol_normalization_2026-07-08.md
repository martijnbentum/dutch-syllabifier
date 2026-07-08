# Phone symbol inventory, CELEX clashes and normalization plan

Date: 2026-07-08. Findings from comparing this repo's phone inventory
against the symbols the CELEX Dutch training pipeline actually emits
(celex package -> phone_mapper disc_to_ipa -> training_examples), plus
a review of how symbol normalization is currently organised.

## Inventory of this repo (data/*.json)

- lax vowels (6):            ɪ ʏ ɛ ə ɔ ɑ
- tense vowels, long (7):    aː eː iː oː uː yː øː
- marginal long vowels (3):  ɛː œː ɔː
- bare tense duplicates (8): a e i o u y ø œ
- diphthongs (3):            ɛi œy ɑu
- consonants (22):           p b t d k ɡ f v s z ʃ ʒ x ɣ h m n ŋ l r ʋ j

vowels.json holds 24 entries for 16 vowel phonemes: the 8 bare forms
duplicate the long forms. The cluster files (legal_onsets, legal_codas)
are single-canonical; the vowel inventory is not.

## Clashes with CELEX Dutch

CELEX Dutch emits 43 distinct ipa symbols. Most match this repo
exactly, including ʋ and the three diphthongs. The clashes (all
covered by training/dataset.py CELEX_TO_IPA, except dʒ which is
skipped):

| celex emits | count  | repo uses | nature                            |
|-------------|--------|-----------|-----------------------------------|
| ʉ           | 23,446 | ʏ         | disc } (put/hut); transcription   |
|             |        |           | convention disagreement           |
| g           |  2,299 | ɡ         | ascii g vs ipa script ɡ codepoint |
| ɒː          |    390 | ɔː        | disc < (zone), collapsed          |
| iːː         |    101 | iː        | disc ! extra long i (analyse)     |
| yːː         |      8 | yː        | disc ( extra long y (centrifuge)  |
| dʒ          |    196 | (skipped) | affricate, no single phone here   |

ʉ, ɒː, iːː and yːː are faithful renderings of four genuinely distinct
DISC symbols (}, <, !, (), verified in phone_mapper's disc_to_ipa
data. CELEX_TO_IPA is therefore not patching upstream bugs: it is a
deliberate projection from phone_mapper's transcription-faithful ipa
onto this repo's coarser, syllabification-oriented phoneme inventory.
That projection belongs in this repo. Only g vs ɡ is arguably a
phone_mapper-level codepoint question.

Systematic difference: CELEX only emits tense vowels in long form; the
bare forms exist purely for this repo's users. That is why learned.py
needed TENSE_TO_LONG to talk to its own model artifacts.

## Diphthongs as single symbols

ɛi, œy, ɑu are one phone each. The boundary algorithm counts nuclei
(one boundary per nucleus pair), so a diphthong entered as two vowels
(ɛ + i) would count as two nuclei and produce a spurious boundary
inside the diphthong. No difference with CELEX: DISC encodes each
diphthong as a single character (K, L, M) and phone_mapper renders
them as the identical single symbols. Near-diphthongs (haai, mooi,
eeuw, nieuw) are vowel + glide (j or ʋ) in both systems. The only
single-symbol divergence is the affricate dʒ, which CELEX has and
this repo refuses.

## The w alias

Dutch has one labiodental approximant phoneme ʋ (water); SAMPA and
CELEX notation write it w, and the offglide in eeuw/nieuw/uw is also
often written w. The repo accepts w as an alias, normalised to ʋ by
canonical_label() inside every lookup; cluster files store only ʋ;
caller phone objects are never rewritten. The CELEX training path
never needs the alias because phone_mapper already maps celex w to ʋ.

Assessment: solved well. Single canonical form in the data files,
tolerant input at every entry point, caller objects preserved.
Folding the eeuw-offglide into ʋ is a phonetic simplification but
harmless for syllabification (both behave as coda consonants). The
problem is not w; it is that tense vowels did not get the same
treatment.

## Current normalization setup

One concept (these symbols are the same phone) is implemented three
ways in three modules:

1. data.py PHONE_ALIASES: w -> ʋ via canonical_label (the clean one)
2. learned.py TENSE_TO_LONG + inventory duplication in vowels.json;
   exists only because the model artifacts inherited CELEX's long
   vowel convention -- the one place training dictates core code
3. training/dataset.py CELEX_TO_IPA: the CELEX projection (correct
   location, wrong target: it should emit repo-canonical labels)

Validation is asymmetric: _validate_clusters checks consonants
against the cluster files, but nothing checks aliases or model
artifact symbols against the inventory.

phone_mapper as runtime source of truth was considered and rejected:
its contract is transcription fidelity (it must keep ʉ, ɒː, iːː
because DISC distinguishes them); this repo's contract is a coarser
phoneme inventory where those distinctions are deliberately
collapsed. phone_mapper stays the upstream of the training pipeline
(already the case via celex) and can serve as a dev-only test oracle.

## Plan (implemented 2026-07-08)

- data.py renamed to phonology.py: it holds Dutch phonology facts
  (inventory, aliases, phonotactic legality), contrasting with
  phones.py which holds phone objects and label plumbing
- long forms become the canonical tense vowels; the 8 bare
  duplicates are dropped from vowels.json
- one alias table in data (aliases.json): w -> ʋ, ascii g -> ɡ and
  the 8 bare tense forms -> long forms; canonical_label derives
  from it, so the symbol set stays fully editable as data
- PHONE_ALIASES (absorbed) and learned.py model_label /
  TENSE_TO_LONG (obsolete, artifacts are repo-canonical) deleted;
  CELEX_TO_IPA keeps only the four genuine projections
- training/dataset.normalize_phones emits canonical labels, so
  retrained artifacts are repo-canonical by construction
- import-time validation extended: alias targets must be canonical
  phones, alias keys must not collide with canonical phones
- bug fixed on the way: phones.is_ipa_phone ignored aliases, so
  Phone('w') warned unknown while syllabify(['w', ...]) accepted it
- train_classifier now seeds liblinear (random_state=0): retraining
  on identical data previously jittered weights at the zero
  threshold, causing spurious artifact diffs; metrics unchanged
  (word accuracy 0.9461, boundary f1 0.9773 on the test split)

Class-based symbol definitions (Phone base class, Consonant/Vowel
subclasses, instances carrying their aliases) were considered and
rejected: phones in this package are values, every operation is set
membership or table lookup on a label string, and the public api
accepts plain strings and duck-typed foreign objects. Classes would
re-encode two predicates (is_nucleus, is_known) as a type hierarchy,
add a second internal representation, and move symbol definitions
from editable data into code. Editability is preserved the other way
round: normalization moves into the data files, not data into code.
