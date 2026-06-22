'''Behavior tests for the phraser validation helpers.

Stand-in objects mimic the minimal phraser shape (a phone has .label, a
segment has .syllables) so no phraser install is needed.
'''
from dutch_syllabifier import (analyse_phrase, analyse_syllable, analyse_word,
    is_valid_phrase, is_valid_syllable, is_valid_word)


class FakePhone:
    def __init__(self, label):
        self.label = label


class FakeSyllable:
    def __init__(self, labels):
        self.phones = [FakePhone(label) for label in labels]


class FakeSegment:
    def __init__(self, syllables):
        self.syllables = [FakeSyllable(labels) for labels in syllables]


def test_valid_syllable():
    assert is_valid_syllable(FakeSyllable(['s', 't', 'r', 'aː', 't']))
    assert not is_valid_syllable(FakeSyllable(['l', 'p', 'ə']))   # /lp/ onset


def test_word_boundaries():
    wrong = FakeSegment([['ɑ', 'p'], ['r', 'ɪ', 'l']])
    assert not is_valid_word(wrong)
    assert analyse_word(wrong).suggested is not None
    right = FakeSegment([['ɑ'], ['p', 'r', 'ɪ', 'l']])
    assert is_valid_word(right)


def test_phrase_across_word_boundaries():
    # a phrase's syllables span words; check them as one sequence
    phrase = FakeSegment([['ɑ'], ['p', 'r', 'ɪ', 'l']])
    assert is_valid_phrase(phrase)


def test_total_on_bad_input():
    # unknown phone and empty segment never raise here
    assert not is_valid_syllable(FakeSyllable(['Q']))
    assert analyse_syllable(FakeSyllable(['Q'])).reason.startswith(
        'could not analyse:')
    assert not is_valid_word(FakeSegment([]))
    assert analyse_phrase(FakeSegment([])).reason.startswith(
        'could not analyse:')
