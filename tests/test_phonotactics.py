'''Tests for the sonority based onset and coda rules and the lint that
cross-checks the whitelists against them (docs/sonority_onset_fallback.md).

The whitelists stay authoritative: whitelisted clusters the rules
reject are data errors and fail hard; sonority-valid clusters attested
in CELEX but missing from a whitelist are candidate gaps for human
review, reported as an informational skip.
'''

import pytest

from dutch_syllabifier.learned import COUNTS_FILE, load_artifact
from dutch_syllabifier.phonotactics import (LEGAL_CODAS, LEGAL_ONSETS,
    is_legal_coda, is_legal_onset, is_sonority_legal_coda,
    is_sonority_legal_onset, is_sonority_legal_syllable)


def test_empty_and_single_consonant_onsets_are_valid():
    assert is_sonority_legal_onset([])
    assert is_sonority_legal_onset(['p'])
    assert is_sonority_legal_onset(['r'])


def test_rising_clusters_are_valid():
    assert is_sonority_legal_onset(['t', 'r'])
    assert is_sonority_legal_onset(['k', 'n'])
    assert is_sonority_legal_onset(['f', 'l'])
    assert is_sonority_legal_onset(['k', 'ʋ'])


def test_s_appendix_is_allowed():
    assert is_sonority_legal_onset(['s', 'p'])
    assert is_sonority_legal_onset(['s', 'x'])
    assert is_sonority_legal_onset(['s', 't', 'r'])
    assert is_sonority_legal_onset(['s', 'p', 'l'])


def test_only_a_leading_s_is_an_appendix():
    assert not is_sonority_legal_onset(['f', 't'])
    assert not is_sonority_legal_onset(['x', 't'])
    assert not is_sonority_legal_onset(['ʃ', 'p'])


def test_falling_or_flat_sonority_is_rejected():
    assert not is_sonority_legal_onset(['r', 't'])
    assert not is_sonority_legal_onset(['ʋ', 'r'])
    assert not is_sonority_legal_onset(['p', 't'])
    assert not is_sonority_legal_onset(['f', 's'])


def test_engma_never_fills_an_onset():
    assert not is_sonority_legal_onset(['ŋ'])
    assert not is_sonority_legal_onset(['ŋ', 'r'])


def test_vowels_cannot_fill_an_onset():
    assert not is_sonority_legal_onset(['aː'])
    assert not is_sonority_legal_onset(['p', 'aː'])


def test_onsets_longer_than_three_are_rejected():
    assert not is_sonority_legal_onset(['s', 'p', 'r', 'ʋ'])


def test_aliases_are_accepted():
    assert is_sonority_legal_onset(['g', 'r'])


def test_empty_and_single_consonant_codas_are_valid():
    assert is_sonority_legal_coda([])
    assert is_sonority_legal_coda(['t'])
    assert is_sonority_legal_coda(['ŋ'])
    assert is_sonority_legal_coda(['ʋ'])


def test_falling_codas_are_valid():
    assert is_sonority_legal_coda(['m', 'p'])
    assert is_sonority_legal_coda(['r', 'k'])
    assert is_sonority_legal_coda(['l', 'm'])


def test_coda_plateaus_are_valid():
    assert is_sonority_legal_coda(['r', 'l'])


def test_coda_s_t_appendix_is_allowed():
    assert is_sonority_legal_coda(['t', 's'])
    assert is_sonority_legal_coda(['k', 't'])
    assert is_sonority_legal_coda(['x', 't', 's'])
    assert is_sonority_legal_coda(['r', 'n', 's', 't'])
    assert is_sonority_legal_coda(['r', 'f', 's', 't'])


def test_rising_codas_are_rejected():
    assert not is_sonority_legal_coda(['t', 'r'])
    assert not is_sonority_legal_coda(['k', 'n'])
    assert not is_sonority_legal_coda(['s', 'm'])


def test_voiced_obstruents_never_fill_a_coda():
    assert not is_sonority_legal_coda(['b'])
    assert not is_sonority_legal_coda(['z'])
    assert not is_sonority_legal_coda(['r', 'd'])
    assert not is_sonority_legal_coda(['g'])


def test_h_and_vowels_never_fill_a_coda():
    assert not is_sonority_legal_coda(['h'])
    assert not is_sonority_legal_coda(['aː'])
    assert not is_sonority_legal_coda(['r', 'aː'])


def test_codas_longer_than_four_are_rejected():
    assert not is_sonority_legal_coda(['r', 'n', 's', 't', 's'])


def test_sonority_legal_syllables():
    assert is_sonority_legal_syllable(['s', 't', 'r', 'aː', 't'])
    assert is_sonority_legal_syllable(['h', 'ɛ', 'r', 'f', 's', 't'])
    assert is_sonority_legal_syllable(['aː'])


def test_syllable_needs_exactly_one_nucleus():
    assert not is_sonority_legal_syllable(['s', 't'])
    assert not is_sonority_legal_syllable(['aː', 'p', 'aː'])
    assert not is_sonority_legal_syllable([])


def test_syllable_rejects_bad_onset_or_coda():
    assert not is_sonority_legal_syllable(['ʋ', 'r', 'aː', 'k'])
    assert not is_sonority_legal_syllable(['aː', 'b'])
    assert not is_sonority_legal_syllable(['k', 'aː', 't', 'r'])


def test_lint_whitelisted_onsets_satisfy_the_sonority_rule():
    '''A whitelisted onset the rule rejects is a candidate data error
    in legal_onsets.json, so it fails hard.'''
    rejected = sorted(
        onset for onset in LEGAL_ONSETS if not is_sonority_legal_onset(onset))
    assert rejected == []


def test_lint_report_attested_onsets_missing_from_the_whitelist():
    '''Report CELEX-attested, SSP-valid onsets the whitelist omits:
    candidate gaps for human review, never auto-added. Informational,
    so it skips with the report instead of failing.'''
    counts = load_artifact(COUNTS_FILE)['onsets']
    gaps = []
    for key, count in counts.items():
        onset = tuple(key.split())
        if not onset or is_legal_onset(onset):
            continue
        if is_sonority_legal_onset(onset):
            gaps.append((count, key))
    if not gaps:
        return
    report = ', '.join(
        f'{key} ({count})' for count, key in sorted(gaps, reverse=True))
    pytest.skip(f'{len(gaps)} candidate onset gaps for review: {report}')


def test_lint_whitelisted_codas_satisfy_the_sonority_rule():
    '''A whitelisted coda the rule rejects is a candidate data error
    in legal_codas.json, so it fails hard.'''
    rejected = sorted(
        coda for coda in LEGAL_CODAS if not is_sonority_legal_coda(coda))
    assert rejected == []


# reviewed and rejected gap candidates (NOTES/sonority_lint_2026-07-08.md):
# rŋ is n -> ŋ assimilation before a velar across a compound seam in
# CELEX (hoorngeschal, kernconcept), never a word-final Dutch coda
KNOWN_CODA_ARTIFACTS = {('r', 'ŋ')}


def test_lint_report_attested_codas_missing_from_the_whitelist():
    '''Report CELEX-attested, sonority-valid codas the whitelist omits:
    candidate gaps for human review, never auto-added. Informational,
    so it skips with the report instead of failing.'''
    counts = load_artifact(COUNTS_FILE)['codas']
    gaps = []
    for key, count in counts.items():
        coda = tuple(key.split())
        if not coda or is_legal_coda(coda):
            continue
        if coda in KNOWN_CODA_ARTIFACTS:
            continue
        if is_sonority_legal_coda(coda):
            gaps.append((count, key))
    if not gaps:
        return
    report = ', '.join(
        f'{key} ({count})' for count, key in sorted(gaps, reverse=True))
    pytest.skip(f'{len(gaps)} candidate coda gaps for review: {report}')
