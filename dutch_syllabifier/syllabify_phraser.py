'''Validate phraser segments against Dutch syllabification.

Works with any object exposing the minimal phraser shape:
  - a syllable has a ``.phones`` attribute (each phone has ``.label``)
  - a word or phrase has a ``.syllables`` attribute (and ``.phones``)
  - a phrase additionally has a ``.words`` attribute (each a word) when
    analyse_phrase is called with cross_word_boundaries=False

No phraser import is needed, so this module stays dependency-free; it relies
only on duck typing and works equally with phraser objects, your own objects,
or plain lists.

Two tiers per segment:
  - ``is_valid_*``   returns a bool
  - ``analyse_*``    returns a Result (.ok, .reason, .suggested)

Both tiers are total: input the engine cannot check (an unknown phone label or
an empty segment) never raises here. The bool tier reports it as False; the
analyse tier returns a falsy Result with .uncheckable True (and a reason that
starts with 'could not analyse:') so 'uncheckable' stays distinguishable from
'incorrect'.
'''
from .syllabifier import Result, check_syllabification


def analyse_syllable(syllable):
    '''Return a Result for one syllable's phonotactic legality.
    syllable                a phraser Syllable (anything with .phones)
    '''
    try:
        return check_syllabification([syllable])
    except ValueError as e:
        return Result(error=f'could not analyse: {e}')


def analyse_word(word):
    '''Return a Result for a word's stored syllable boundaries.
    word                    a phraser Word (uses word.syllables)
    '''
    try:
        return check_syllabification(word.syllables)
    except ValueError as e:
        return Result(error=f'could not analyse: {e}')


def analyse_phrase(phrase, cross_word_boundaries=True):
    '''Return a Result for a phrase's syllable boundaries.
    phrase                  a phraser Phrase
    cross_word_boundaries   if True (default), the phrase is syllabified as one
                            connected sequence, so a consonant may resyllabify
                            across a word boundary (e.g. het ei -> hɛ.tɛi). If
                            False, each word is syllabified on its own and no
                            boundary moves across words.

    The True path needs phrase.syllables; the False path needs phrase.words.
    '''
    try:
        if cross_word_boundaries:
            return check_syllabification(phrase.syllables)
        words = phrase.words
        if not words:
            raise ValueError('no words to check')
        return _analyse_phrase_per_word(words)
    except ValueError as e:
        return Result(error=f'could not analyse: {e}')


def _analyse_phrase_per_word(words):
    '''Syllabify each of a phrase's words on its own and merge into one Result,
    so a boundary is never moved across words. Helper for analyse_phrase's
    cross_word_boundaries=False path; assumes a non-empty word list.

    Because Result derives ok/reason from current + suggested, concatenating the
    per-word tiers yields a correct phrase Result: ok only when every word is
    legal and every word already matches its own maximal-onset split.
    '''
    per_word = [check_syllabification(w.syllables) for w in words]
    current = [s for r in per_word for s in r.current]
    inputs = [s for r in per_word for s in r.input]
    # a word with no nucleus has no suggestion; then neither does the phrase
    if any(r.suggested is None for r in per_word):
        suggested = None
    else:
        suggested = [s for r in per_word for s in r.suggested]
    return Result(current=current, suggested=suggested, input=inputs)


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
