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
    '''A word or phrase. Pass syllables (a list of label-lists) for a word, or
    words (a list of words, each a list of syllables) for a phrase; in the
    latter case .syllables is derived by flattening the words.'''
    def __init__(self, syllables=None, words=None):
        if words is not None:
            self.words = [FakeSegment(w) for w in words]
            self.syllables = [s for w in self.words for s in w.syllables]
        else:
            self.syllables = [FakeSyllable(labels) for labels in syllables]


def test_valid_syllable():
    assert is_valid_syllable(FakeSyllable(['s', 't', 'r', 'aː', 't']))
    assert not is_valid_syllable(FakeSyllable(['l', 'p', 'ə']))   # /lp/ onset


def test_analyse_syllable_reports_legality_reason():
    # a single syllable has no boundaries to judge; reason is its legality
    assert analyse_syllable(FakeSyllable(['s', 't', 'r', 'aː', 't'])).reason \
        == 'legal syllable'
    assert analyse_syllable(FakeSyllable(['l', 'p', 'ə'])).reason \
        == 'illegal onset: l p'


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


def test_phrase_crosses_word_boundaries_by_default():
    # het + ei: connected speech moves /t/ into the next word -> hɛ.tɛi,
    # so the stored hɛt.ɛi is judged incorrect
    phrase = FakeSegment(words=[[['h', 'ɛ', 't']], [['ɛi']]])
    r = analyse_phrase(phrase)
    assert not r.ok
    assert [s.label for s in r.suggested] == ['h ɛ', 't ɛi']


def test_phrase_respects_word_boundaries_when_disabled():
    # same input, but each word is syllabified on its own: /t/ stays in het
    phrase = FakeSegment(words=[[['h', 'ɛ', 't']], [['ɛi']]])
    r = analyse_phrase(phrase, cross_word_boundaries=False)
    assert r.ok
    assert [s.label for s in r.suggested] == ['h ɛ t', 'ɛi']


def test_phrase_word_respecting_is_total_on_empty():
    # no words -> uncheckable, not a spurious 'valid'
    assert analyse_phrase(FakeSegment(words=[]),
        cross_word_boundaries=False).uncheckable


def test_total_on_bad_input():
    # unknown phone and empty segment never raise here; the .uncheckable flag
    # (not a substring of the reason) distinguishes 'uncheckable' from 'wrong'
    assert not is_valid_syllable(FakeSyllable(['Q']))
    bad = analyse_syllable(FakeSyllable(['Q']))
    assert not bad.ok and bad.uncheckable
    assert not is_valid_word(FakeSegment([]))
    assert analyse_phrase(FakeSegment([])).uncheckable
