# Sonority lint findings: whitelists vs sonority rules

Date: 2026-07-08. Output of the sonority lint in
`tests/test_phonotactics.py`, which cross-checks `legal_onsets.json`
and `legal_codas.json` against the advisory sonority rules in
`phonotactics.py` (`is_sonority_legal_onset`, `is_sonority_legal_coda`)
and against the CELEX-attested clusters in
`data/celex_onset_coda_counts.json`. The whitelists stay authoritative;
gaps listed here are candidates for human review, never auto-added.
Design background: `docs/sonority_onset_fallback.md`.

## Rule parameters

- Onset: strict sonority rise (min distance 1), one leading /s/
  appendix, max 3 segments, /ŋ/ and vowels banned.
- Coda: non-rising sonority (plateaus allowed, so whitelisted `r l`
  passes), trailing /s/ /t/ appendix run, max 4 segments, voiced
  obstruents (final devoicing), /h/ and vowels banned.

## Onsets

**Whitelisted but rule-rejected: none.** `legal_onsets.json` is clean
under the SSP rule.

**CELEX-attested, SSP-valid, not whitelisted (47), by token count:**

    t j (4141), t s (3376), t ʃ (724), p s (289), p j (276), k j (137),
    l j (94), k s (62), f j (55), p l ʋ (50), n j (49), v ʋ (44),
    v j (40), ɡ ʋ (38), ɣ n (28), x n (28), ʃ m (24), m j (24),
    p n (23), p ʋ (21), ʃ n (20), r ʋ (18), f n (18), m ʋ (16),
    f r ʋ (13), d j (13), ʃ l (12), b ʋ (12), ɣ j (11), s t j (10),
    s k ʋ (10), l ʋ (10), ʒ ʋ (8), b j (6), k r ʋ (5), t l (3),
    s k l (3), n ʋ (3), d z (3), ʃ ʋ (2), r j (2), d r ʋ (2),
    ʒ j (1), t s ʋ (1), s f r (1), p f (1), k l ʋ (1)

Reading of the top entries: `t j`, `p j`, `k j`, `n j`, `m j` are
almost certainly diminutive `-tje/-pje/-kje` sequences syllabified as
onsets, and `t s` / `t ʃ` look like affricate-ish loan material —
extraction artifacts rather than whitelist gaps. Plausible genuine
candidates further down: `f n` (fnuiken), `x n` / `ɣ n` (gniffelen),
`ʃ m` / `ʃ n` / `ʃ l` (loans: sjmoel, snoezig-type sj-words).

**Known blind spot:** `ʋ r` (wreken-type words, 622 tokens) is neither
whitelisted nor SSP-valid (glide -> liquid falls), so it appears in no
lint direction. If /ʋr/ is wanted, it is a deliberate whitelist
addition.

## Codas

**Whitelisted but rule-rejected: none.** `legal_codas.json` is clean
under the coda rule (the plateau allowance exists for `r l`).

**CELEX-attested, sonority-valid, not whitelisted (80), by token count:**

    j t (606), n t s (544), n t s t (495), r t s (482), ʋ t (472),
    x s (448), t s t (422), ŋ t (252), r t s t (187), ʃ (89),
    r m t (88), ʋ s (84), r x t (75), r n s (72), x t s t (66),
    ŋ k s (63), n ʃ (59), r p s (57), l f s (54), k t s t (48),
    j s (43), ʋ s t (42), l m t (42), l t s t (41), l t s (36),
    r n t (35), m t s (31), s p t (30), f t s (30), l x t (29),
    p s t (28), m f (28), r ʃ (26), s t s (25), m t s t (22),
    r k s (19), f t s t (19), r ŋ (17), j n (17), r m s t (16),
    s t s t (15), ŋ k s t (14), j s t (11), p t s t (10), ʃ t (9),
    r x s (9), r m s (9), n ʃ t (9), k t s (8), m p s (7), j t s (7),
    j m (7), m ʃ (6), j t s t (6), j f (6), ʋ t s t (5), s k s t (5),
    r p s t (5), j n s (5), j f s (5), s k s (4), r l s (4),
    m p s t (4), l p s (4), r l t (3), m ʃ t (3), l m s t (3),
    j p (3), j n t s (3), j n t (3), j k (2), ŋ t s t (1), s p s (1),
    p t s (1), l p s t (1), l k s t (1), l f t s (1), j l s (1),
    j l (1), j k s (1)

The top entries look like real gaps in the conservative list:
inflected forms (`j t` sneeuwt-type glide+t is actually /ʋ t/; `j t`
is aai-type vowel+j+t, `ŋ t` hangt-type, `r t s` -(r)ts genitives and
plurals, `n t s` / `n t s t` -ntst superlatives) plus the plain `ʃ`
coda (89) from loans.

**Context: attested codas rejected by the rule (92 types).** Dominated
by voiced obstruents: `ɣ` (4028), `d` (2643), `v` (1909), `z` (1692),
`n d` (1390), `ɡ` (902), `b` (662), `r d` (605)... These are
word-internal codas in CELEX transcriptions (ad.mi.raal-type), where
final devoicing has not applied. The rule describes surface word-final
codas, matching the whitelist's stance, so these are excluded by
design — but it means the coda rule (and whitelist) undershoots for
word-internal syllable judgments.

## Coda gap review outcome (2026-07-08)

All 80 candidates were reviewed against the actual CELEX words that
carry them (full-corpus scan, not just the training split the counts
artifact covers). 81 codas were added to `legal_codas.json` (71 -> 152
entries), in three groups:

- **Native inflection on already-legal bases (57):** verb -t and
  devoiced participles (draait, duwt, hangt, stormt, filmt, bezorgt,
  volgt, tornt, gespt, marlt, riskt), plural/genitive/linking -s
  (aanstonds, aards, alledaags, nieuws, hoorns, links, dorps, zelfs,
  moois, balts, ambts-, hoofds, acts, kerks, platforms, voorzorgs-,
  pumps, wulps, tests, disks, crisps, scripts, copyrights, delfts),
  superlatives -st (flauwst, mooist, armst, flinkst, diepst, stompst,
  kalmst, scherpst, wulpst, schalkst, groteskst) and -tst on d/t-final
  stems (fietst, aanhoudendst, absurdst, bevoegdst, abstractst,
  bemiddeldst, beroemdst, beleefdst, bedeesdst, abruptst, gemengdst,
  berooidst, benauwdst), plus the lexical gap `m f` (nimf, lymf).
- **/ʃ/ loan codas (7):** douche, lunch, doucht/gecrasht, geluncht,
  demarche, ramsj, ramsjt — consistent with ʃ and ʃr already being
  legal onsets.
- **English /j/+C loans (17):** design, part-time, drive, type-,
  spike, file with their -s/-t inflections, plus girls (`r l s`) and
  timet (`j m t`).

`s k t` (riskt) and `j m t` (timet) came from the full-corpus scan;
they have count 0 in the artifact because their lemmas fell in the
dev/test split.

**Rejected: `r ŋ` (17).** Never word-final; the carriers are
hoorngeschal/kernconcept-type compounds where /n/ assimilates to [ŋ]
before a velar across the seam. Excluded from the gap report via
KNOWN_CODA_ARTIFACTS in tests/test_phonotactics.py.

After the additions the coda gap report is empty; the informational
skip now fires only for the 47 onset gaps.
