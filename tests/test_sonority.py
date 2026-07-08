import pytest

from dutch_syllabifier import Phone
from dutch_syllabifier.phone_inventory import KNOWN_PHONES
from dutch_syllabifier.sonority import (SONORITY_SCALE, sonority_class,
    sonority_classes, sonority_weight, sonority_weights)


def test_consonant_classes():
    assert sonority_class('p') == 'stop'
    assert sonority_class('s') == 'fricative'
    assert sonority_class('m') == 'nasal'
    assert sonority_class('l') == 'liquid'
    assert sonority_class('j') == 'glide'


def test_vowels_and_diphthongs_are_vowel_class():
    assert sonority_class('aː') == 'vowel'
    assert sonority_class('ɛi') == 'vowel'


def test_aliases_are_accepted():
    assert sonority_class('w') == 'glide'
    assert sonority_class('g') == 'stop'
    assert sonority_class('e') == 'vowel'


def test_phone_objects_are_accepted():
    assert sonority_class(Phone('r')) == 'liquid'
    assert sonority_weight(Phone('r')) == sonority_weight('r')


def test_weights_follow_the_scale_order():
    weights = sonority_weights(['p', 's', 'm', 'l', 'j', 'aː'])
    assert weights == sorted(weights)
    assert weights == list(range(len(SONORITY_SCALE)))


def test_sequence_helpers():
    assert sonority_classes(['s', 't', 'r']) == ['fricative', 'stop', 'liquid']
    assert sonority_weights(['s', 't', 'r']) == [1, 0, 3]


def test_unknown_phone_raises():
    with pytest.raises(ValueError):
        sonority_class('q')


def test_every_known_phone_has_a_class():
    for label in KNOWN_PHONES:
        assert sonority_class(label) in SONORITY_SCALE
