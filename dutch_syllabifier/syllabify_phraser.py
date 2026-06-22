'''Validate phraser segments against Dutch syllabification.

Works with any object exposing the minimal phraser shape:
  - a syllable has a ``.phones`` attribute (each phone has ``.label``)
  - a word or phrase has a ``.syllables`` attribute (and ``.phones``)

No phraser import is needed, so this module stays dependency-free; it relies
only on duck typing and works equally with phraser objects, your own objects,
or plain lists.

Two tiers per segment:
  - ``is_valid_*``   returns a bool
  - ``analyse_*``    returns a Result (.ok, .reason, .suggested)

Both tiers are total: input the engine cannot check (an unknown phone label or
an empty segment) never raises here. The bool tier reports it as False; the
analyse tier returns a falsy Result whose reason starts with 'could not
analyse:' so 'uncheckable' stays distinguishable from 'incorrect'.
'''
from .syllabifier import Result, check_syllabification, is_legal_syllable


def analyse_syllable(syllable):
    '''Return a Result for one syllable's phonotactic legality.
    syllable                a phraser Syllable (anything with .phones)
    '''
    try:
        return is_legal_syllable(syllable)
    except ValueError as e:
        return Result(False, f'could not analyse: {e}')


def analyse_word(word):
    '''Return a Result for a word's stored syllable boundaries.
    word                    a phraser Word (uses word.syllables)
    '''
    try:
        return check_syllabification(word.syllables)
    except ValueError as e:
        return Result(False, f'could not analyse: {e}')


def analyse_phrase(phrase):
    '''Return a Result for a phrase's syllable boundaries, including across
    word boundaries.
    phrase                  a phraser Phrase (uses phrase.syllables)
    '''
    try:
        return check_syllabification(phrase.syllables)
    except ValueError as e:
        return Result(False, f'could not analyse: {e}')


def is_valid_syllable(syllable):
    '''Return True if the syllable is phonotactically legal.
    syllable                a phraser Syllable (anything with .phones)
    '''
    return analyse_syllable(syllable).ok


def is_valid_word(word):
    '''Return True if the word's stored boundaries follow maximal onset.
    word                    a phraser Word (uses word.syllables)
    '''
    return analyse_word(word).ok


def is_valid_phrase(phrase):
    '''Return True if the phrase's boundaries follow maximal onset, including
    across word boundaries.
    phrase                  a phraser Phrase (uses phrase.syllables)
    '''
    return analyse_phrase(phrase).ok
