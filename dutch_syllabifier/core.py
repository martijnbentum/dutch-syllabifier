from . import data
from .phones import labels_of
from .syllables import Syllable


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


def syllabify(phones):
    '''Suggest Dutch syllabification.
    phones                  list of IPA phone symbols

    Returns a list of Syllable objects, split with the Maximal Onset Principle.
    Raises ValueError on unknown phones or when there is no nucleus.
    '''
    phones = list(phones)
    labels = labels_of(phones)
    _check_known(labels)
    nuclei = _nucleus_indices(labels)
    if not nuclei:
        raise ValueError('phone sequence has no vowel nucleus')

    boundaries = []
    for left, right in zip(nuclei, nuclei[1:]):
        cluster = list(range(left + 1, right))
        split = _maximal_onset_split(labels, cluster)
        boundaries.append(split)

    starts = [0] + boundaries
    ends = boundaries + [len(phones)]
    return [Syllable(phones[s:e]) for s, e in zip(starts, ends)]


def _maximal_onset_split(labels, cluster):
    '''Return the index where the next syllable's onset begins.
    labels                  full list of IPA labels
    cluster                 list of indices of the intervocalic consonants

    The largest legal onset is taken from the right of the cluster; the rest
    becomes the coda of the preceding syllable.
    '''
    for size in range(len(cluster), -1, -1):
        start = len(cluster) - size
        onset = [labels[i] for i in cluster[start:]]
        if data.is_legal_onset(onset):
            return cluster[start] if size else cluster[-1] + 1
    return cluster[-1] + 1


def is_legal_syllable(phones):
    '''Judge whether one syllable is phonotactically legal in Dutch.
    phones                  list of IPA phone symbols for a single syllable

    Returns a Result. Coda checking is conservative and partial.
    Raises ValueError on unknown phones.
    '''
    labels = labels_of(_as_phone_list(phones))
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

    given_labels = [labels_of(s) for s in given]
    suggested_labels = [labels_of(s.phones) for s in suggested]
    if given_labels == suggested_labels:
        return Result(True, 'correct syllable boundaries')
    pretty = ' . '.join(s.label for s in suggested)
    return Result(False, f'boundaries differ from maximal onset: {pretty}',
        suggested=suggested)
