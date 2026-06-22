'''Minimal behavior tests for the public API.

These intentionally test only the public surface (syllabify,
is_legal_syllable, check_syllabification, Phone, Syllable) so internal
refactors do not break them.
'''
import pytest

from dutch_syllabifier import (Phone, Syllable, check_syllabification,
    is_legal_syllable, syllabify)


def shapes(syllables):
    '''Return syllables as lists of phone-label lists for easy comparison.'''
    return [syllable.phones for syllable in syllables]


def test_single_intervocalic_consonant():
    # taːfəl -> taː . fəl
    assert shapes(syllabify(['t', 'aː', 'f', 'ə', 'l'])) == \
        [['t', 'aː'], ['f', 'ə', 'l']]


def test_legal_onset_clusters():
    # /pr/ is a legal onset -> ɑ . prɪl
    assert shapes(syllabify(['ɑ', 'p', 'r', 'ɪ', 'l'])) == \
        [['ɑ'], ['p', 'r', 'ɪ', 'l']]
    # /str/ is a legal onset -> single syllable
    assert shapes(syllabify(['s', 't', 'r', 'aː', 't'])) == \
        [['s', 't', 'r', 'aː', 't']]


def test_sx_onset():
    # /sx/ stays together as a single onset cluster (misschien)
    assert shapes(syllabify(['m', 'ɪ', 's', 'x', 'i', 'n'])) == \
        [['m', 'ɪ'], ['s', 'x', 'i', 'n']]


def test_illegal_onset_clusters():
    assert not is_legal_syllable(['l', 'p', 'ə']).ok   # /lp/
    assert not is_legal_syllable(['r', 'm', 'ə']).ok   # /rm/


def test_complex_coda():
    # herfst -> single syllable with complex coda /rfst/
    assert shapes(syllabify(['h', 'ɛ', 'r', 'f', 's', 't'])) == \
        [['h', 'ɛ', 'r', 'f', 's', 't']]
    assert is_legal_syllable(['h', 'ɛ', 'r', 'f', 's', 't']).ok


def test_diphthongs_are_single_symbols():
    for diphthong in ('ɛi', 'œy', 'ɑu'):
        assert is_legal_syllable([diphthong]).ok
        assert shapes(syllabify(['m', diphthong])) == [['m', diphthong]]


def test_invalid_input_raises():
    with pytest.raises(ValueError):
        syllabify(['ɑ', 'Q'])              # unknown phone
    with pytest.raises(ValueError):
        syllabify(['p', 'r'])              # no nucleus
    with pytest.raises(ValueError):
        check_syllabification([])          # empty input


def test_check_already_syllabified():
    # incorrect: /pr/ is a legal onset, so maximal onset gives ɑ.prɪl
    assert not check_syllabification([['ɑ', 'p'], ['r', 'ɪ', 'l']]).ok
    # correct: /lp/ is not a legal onset but /p/ is
    assert check_syllabification([['h', 'ɛ', 'l'], ['p', 'ə']]).ok
    assert check_syllabification([['s', 't', 'r', 'aː', 't']]).ok
    assert check_syllabification([['h', 'ɛ', 'r', 'f', 's', 't']]).ok


def test_phone_object():
    assert Phone('m').label == 'm'
    assert Phone('m') == Phone('m')
    assert Phone('m') == 'm'
    assert Phone('m') != object()          # does not raise


def test_syllable_object():
    s = Syllable(['m', 'ɑ'])
    assert s.phones == ['m', 'ɑ']
    assert s.label == 'm ɑ'
    # accepts a Syllable (or any object with .phones)
    assert is_legal_syllable(Syllable(['s', 't', 'r', 'aː', 't'])).ok
