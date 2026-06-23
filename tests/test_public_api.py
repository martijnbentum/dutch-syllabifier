'''Minimal behavior tests for the public API.

These intentionally test only the public surface (syllabify,
is_legal_syllable, check_syllabification, Phone, Syllable) so internal
refactors do not break them.
'''
import pytest

from dutch_syllabifier import (Legality, Phone, Result, Syllable,
    check_syllabification, is_legal_syllable, resyllabify_phones, syllabify)


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
    assert not is_legal_syllable(['l', 'p', 'ə'])   # /lp/
    assert not is_legal_syllable(['r', 'm', 'ə'])   # /rm/


def test_complex_coda():
    # herfst -> single syllable with complex coda /rfst/
    assert shapes(syllabify(['h', 'ɛ', 'r', 'f', 's', 't'])) == \
        [['h', 'ɛ', 'r', 'f', 's', 't']]
    assert is_legal_syllable(['h', 'ɛ', 'r', 'f', 's', 't'])


def test_diphthongs_are_single_symbols():
    for diphthong in ('ɛi', 'œy', 'ɑu'):
        assert is_legal_syllable([diphthong])
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


def test_result_current_and_suggested_are_syllables():
    # incorrect boundaries: ɑp.rɪl -> maximal onset ɑ.prɪl
    r = check_syllabification([['ɑ', 'p'], ['r', 'ɪ', 'l']])
    assert not r.ok
    assert shapes(r.current) == [['ɑ', 'p'], ['r', 'ɪ', 'l']]
    assert shapes(r.suggested) == [['ɑ'], ['p', 'r', 'ɪ', 'l']]
    # both tiers are lists of Syllable objects
    assert all(isinstance(s, Syllable) for s in r.current)
    assert all(isinstance(s, Syllable) for s in r.suggested)


def test_result_input_preserves_original_objects():
    a, b = Syllable(['h', 'ɛ', 'l']), Syllable(['p', 'ə'])
    r = check_syllabification([a, b])
    assert r.ok
    # input holds the exact objects passed in (identity preserved)
    assert r.input[0] is a and r.input[1] is b
    # current is a normalised copy, not the original objects
    assert r.current[0] is not a


def test_illegal_syllable_still_reports_correction():
    # ɑ.lpə is illegal (/lp/ onset) but maximal onset gives ɑl.pə;
    # the correction must survive the legality failure, not be dropped
    r = check_syllabification([['ɑ'], ['l', 'p', 'ə']])
    assert not r.ok
    # branch on the structured handle, not a substring of the message
    assert r.current[1].legality.illegal_onset
    assert shapes(r.suggested) == [['ɑ', 'l'], ['p', 'ə']]
    assert shapes(r.current) == [['ɑ'], ['l', 'p', 'ə']]


def test_illegal_syllable_preserves_input_objects():
    a, b = Syllable(['ɑ']), Syllable(['l', 'p', 'ə'])
    r = check_syllabification([a, b])
    assert not r.ok
    # identity of the originals is preserved even on the failure path
    assert r.input[0] is a and r.input[1] is b


def test_illegal_syllable_without_vowel_has_no_suggestion():
    # no nucleus anywhere -> nothing to syllabify, but current/input
    # are still populated (defensive _try_syllabify branch)
    r = check_syllabification([['l'], ['p']])
    assert not r.ok
    assert r.suggested is None
    assert shapes(r.current) == [['l'], ['p']]
    assert r.input == [['l'], ['p']]


def test_result_repr_omits_segmentation_str_shows_it():
    r = check_syllabification([['ɑ', 'p'], ['r', 'ɪ', 'l']])
    assert ' . ' not in repr(r)        # repr carries no segmentation
    assert ' . ' in str(r)             # str does


def test_resyllabify_phones_regroups_same_objects():
    # ɑprɪl -> ɑ . prɪl, holding the exact phone objects passed in
    phones = [Phone('ɑ'), Phone('p'), Phone('r'), Phone('ɪ'), Phone('l')]
    groups = resyllabify_phones(phones)
    assert [[p.label for p in g] for g in groups] == \
        [['ɑ'], ['p', 'r', 'ɪ', 'l']]
    # identity preserved: same objects, just regrouped
    assert groups[0][0] is phones[0]
    assert groups[1][0] is phones[1]


def test_resyllabify_phones_agrees_with_syllabify():
    phones = ['ɑ', 'p', 'r', 'ɪ', 'l']
    assert resyllabify_phones(phones) == [s.phones for s in syllabify(phones)]


def test_result_groups_expose_input_phones():
    r = check_syllabification([['ɑ', 'p'], ['r', 'ɪ', 'l']])
    assert r.current_groups == [s.phones for s in r.current]
    assert r.suggested_groups == [s.phones for s in r.suggested]
    assert r.suggested_groups == resyllabify_phones(['ɑ', 'p', 'r', 'ɪ', 'l'])


def test_phone_object():
    assert Phone('m').label == 'm'
    assert Phone('m') == Phone('m')
    assert Phone('m') == 'm'
    assert Phone('m') != object()          # does not raise


def test_syllable_object():
    s = Syllable(['m', 'ɑ'])
    assert s.phones == ['m', 'ɑ']
    assert s.label == 'm ɑ'
    # a fresh syllable is unjudged until check_syllabification sets it
    assert s.legality is None
    # accepts a Syllable (or any object with .phones)
    assert is_legal_syllable(Syllable(['s', 't', 'r', 'aː', 't']))


def test_legality_findings():
    # each finding fires on the right input; only one flag set at a time
    assert Legality.judge(['l', 'p', 'ə']).illegal_onset       # /lp/ onset
    assert Legality.judge(['p']).no_nucleus                    # no vowel
    assert Legality.judge(['ɑ', 't', 'ɑ']).multiple_nuclei     # two nuclei
    assert Legality.judge(['s', 't', 'r', 'aː', 't']).finding is None


def test_legality_ok_and_reason_are_derived():
    legal = Legality.legal()
    assert legal.ok and legal.finding is None and legal.reason == 'legal syllable'
    bad = Legality.judge(['l', 'p', 'ə'])
    assert not bad.ok
    # reason is derived from the finding name plus the offending phones
    assert bad.reason == 'illegal onset: l p'
    assert str(bad) == bad.reason
    assert 'illegal_onset' in repr(bad)


def test_unlisted_coda_is_tolerated():
    # a coda not in the conservative list is noted but does not clear ok
    v = Legality.judge(['ɑ', 'l', 'f', 's', 't'])
    assert v.ok and bool(v)
    assert v.unlisted_coda
    assert v.reason == 'unlisted coda: l f s t'


def test_legality_attached_to_current_not_suggested():
    r = check_syllabification([['ɑ'], ['l', 'p', 'ə']])
    # every current syllable carries its verdict
    assert all(isinstance(s.legality, Legality) for s in r.current)
    assert r.current[1].legality.illegal_onset
    # suggested syllables are unjudged (judging them would be circular)
    assert all(s.legality is None for s in r.suggested)


def test_result_uncheckable_flag():
    # error= builds a falsy, uncheckable result carrying an explicit reason
    bad = Result(error='could not analyse: boom')
    assert bad.uncheckable
    assert not bad.ok and not bad
    assert bad.reason == 'could not analyse: boom'
    # a normal derived result is checkable
    assert not check_syllabification([['ɑ', 'p'], ['r', 'ɪ', 'l']]).uncheckable
