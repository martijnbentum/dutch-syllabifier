import pytest

from dutch_syllabifier.learned import (CountSyllabifier,
    ClassifierSyllabifier, boundary_features)
from dutch_syllabifier.phone_inventory import canonical_label


def make_count_model():
    onsets = {'': 10, 'p': 20, 'p r': 30, 'r': 5, 'l': 10, 'f': 10}
    codas = {'': 50, 'l': 10, 'p': 5, 'l p': 2}
    return CountSyllabifier({'onsets': onsets, 'codas': codas})


def test_count_syllabifier_prefers_maximal_onset():
    model = make_count_model()
    syllables = model.syllabify(['ɑ', 'p', 'r', 'ɪ', 'l'])
    assert [s.phones for s in syllables] == [['ɑ'], ['p', 'r', 'ɪ', 'l']]


def test_count_syllabifier_avoids_rare_onset():
    model = make_count_model()
    syllables = model.syllabify(['h', 'ɛ', 'l', 'p', 'ə'])
    assert [s.phones for s in syllables] == [['h', 'ɛ', 'l'], ['p', 'ə']]


def test_count_syllabifier_monosyllable():
    model = make_count_model()
    syllables = model.syllabify(['s', 't', 'r', 'aː', 't'])
    assert [s.phones for s in syllables] == [['s', 't', 'r', 'aː', 't']]


def test_count_syllabifier_unknown_phone_raises():
    with pytest.raises(ValueError):
        make_count_model().syllabify(['q', 'aː'])


def test_count_syllabifier_no_nucleus_raises():
    with pytest.raises(ValueError):
        make_count_model().syllabify(['p', 's', 't'])


def test_classifier_syllabifier_scores_boundaries():
    # weights favor a boundary right before p
    model = ClassifierSyllabifier({'intercept': -1.0,
        'weights': {'r1=p': 2.0}})
    syllables = model.syllabify(['ɑ', 'l', 'p', 'ə'])
    assert [s.phones for s in syllables] == [['ɑ', 'l'], ['p', 'ə']]
    assert model.boundary_indices(['ɑ', 'l', 'p', 'ə']) == [2]


def test_canonical_label_normalizes_input():
    assert canonical_label('w') == 'ʋ'
    assert canonical_label('g') == 'ɡ'
    assert canonical_label('e') == 'eː'
    assert canonical_label('ɛi') == 'ɛi'


def test_learned_accepts_short_tense_vowels():
    model = make_count_model()
    long_input = model.boundary_indices(['t', 'aː', 'f', 'ə', 'l'])
    short_input = model.boundary_indices(['t', 'a', 'f', 'ə', 'l'])
    assert long_input == short_input == [2]


def test_packaged_count_artifact():
    syllables = CountSyllabifier().syllabify(['t', 'aː', 'f', 'ə', 'l'])
    assert [s.phones for s in syllables] == [['t', 'aː'], ['f', 'ə', 'l']]


def test_packaged_classifier_artifact():
    model = ClassifierSyllabifier()
    syllables = model.syllabify(['t', 'aː', 'f', 'ə', 'l'])
    assert [s.phones for s in syllables] == [['t', 'aː'], ['f', 'ə', 'l']]


def test_boundary_features_window_and_padding():
    features = boundary_features(['ɑ', 'p', 'r', 'ɪ', 'l'], 1)
    assert 'l1=ɑ' in features
    assert 'l2=#' in features
    assert 'r1=p' in features
    assert 'r1r2=p r' in features
    assert 'cv=##VCCV' in features
