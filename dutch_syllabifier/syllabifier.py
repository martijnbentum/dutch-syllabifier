from . import data
from .phones import phones_to_label
from .syllables import Syllable


def syllabify(phones):
    '''Suggest Dutch syllabification.
    phones                  list of IPA phone symbols

    Returns a list of Syllable objects, split with the Maximal Onset Principle.
    Raises ValueError on unknown phones or when there is no nucleus.
    '''
    phones = list(phones)
    labels = phones_to_label(phones)
    _check_known(labels)
    nuclei = _nucleus_indices(labels)
    if not nuclei:
        raise ValueError('phone sequence has no vowel nucleus')

    boundaries = []
    for left, right in zip(nuclei, nuclei[1:]):
        boundaries.append(_maximal_onset_split(labels, left, right))

    starts = [0] + boundaries
    ends = boundaries + [len(phones)]
    return [Syllable(phones[s:e]) for s, e in zip(starts, ends)]


def is_legal_syllable(phones):
    '''Judge whether one syllable is phonotactically legal in Dutch.
    phones                  a single syllable: a Syllable object or a list of
                            IPA phone symbols

    Returns a Result. Coda checking is conservative and partial.
    Raises ValueError on unknown phones.
    '''
    labels = phones_to_label(_as_phone_list(phones))
    _check_known(labels)
    nuclei = _nucleus_indices(labels)
    if len(nuclei) == 0:
        return Result(False, 'syllable has no vowel nucleus')
    if len(nuclei) > 1:
        return Result(False, 'syllable has more than one nucleus')

    n = nuclei[0]
    onset = labels[:n]
    coda = labels[n + 1:]
    if not data.is_legal_onset(onset):
        return Result(False, f'illegal onset: {" ".join(onset)}')
    if not data.is_legal_coda(coda):
        return Result(False, f'illegal coda (conservative): {" ".join(coda)}')
    return Result(True, 'legal syllable')


def check_syllabification(syllables):
    '''Judge whether a sequence of syllables has correct boundaries.
    syllables               list of Syllable objects or lists of phones

    Returns a Result. When the boundaries differ from the Maximal Onset
    Principle, ``result.suggested`` holds the suggested syllabification.
    Raises ValueError on unknown phones.
    '''
    given = [list(_as_phone_list(s)) for s in syllables]
    for syllable in given:
        legal = is_legal_syllable(syllable)
        if not legal.ok:
            return Result(False, legal.reason)

    flat = [phone for syllable in given for phone in syllable]
    suggested = syllabify(flat)

    given_labels = [phones_to_label(s) for s in given]
    suggested_labels = [phones_to_label(s.phones) for s in suggested]
    if given_labels == suggested_labels:
        return Result(True, 'correct syllable boundaries')
    pretty = ' . '.join(s.label for s in suggested)
    return Result(False, f'boundaries differ from maximal onset: {pretty}',
        suggested=suggested)


class Result:
    '''Outcome of a legality or syllabification check.

    ok                      True if the check passed
    reason                  human readable explanation
    suggested               suggested correction, if any
    '''

    def __init__(self, ok, reason='', suggested=None):
        self.ok = ok
        self.reason = reason
        self.suggested = suggested

    def __bool__(self):
        return self.ok

    def __repr__(self):
        return f'Result(ok={self.ok}, reason={self.reason!r})'


def _maximal_onset_split(labels, left, right):
    '''Return the index where the syllable at nucleus `right` begins.
    labels                  full list of IPA labels
    left, right             indices of two consecutive nuclei

    The largest legal onset (a suffix of the consonants between the nuclei) is
    assigned to the second syllable; the rest becomes the coda of the first.
    When no consonant suffix is a legal onset (including no consonants at all),
    the boundary sits just before the second nucleus.
    '''
    for size in range(right - left - 1, 0, -1):
        onset = labels[right - size:right]
        if data.is_legal_onset(onset):
            return right - size
    return right


def _check_known(labels):
    '''Raise ValueError if any label is not a known Dutch phone.
    labels                  list of IPA labels
    '''
    for lab in labels:
        if not data.is_known(lab):
            raise ValueError(f'unknown phone symbol: {lab!r}')


def _nucleus_indices(labels):
    '''Return the indices of nucleus (vowel or diphthong) phones.'''
    return [i for i, lab in enumerate(labels) if data.is_nucleus(lab)]


def _as_phone_list(syllable):
    '''Return the phone list of a Syllable object or pass through a list.'''
    if hasattr(syllable, 'phones'):
        return syllable.phones
    return syllable
