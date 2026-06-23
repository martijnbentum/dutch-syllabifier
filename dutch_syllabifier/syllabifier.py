from . import data
from .phones import phones_to_label
from .syllables import Syllable


def syllabify(phones):
    '''Suggest Dutch syllabification.
    phones                  list of phones (IPA strings or objects with .label)

    Returns a list of Syllable objects, split with the Maximal Onset Principle.
    This is the single source of the boundary logic; resyllabify_phones derives
    its groups from this output. Raises ValueError on unknown phones or when
    there is no nucleus.
    '''
    phones = list(phones)
    labels = phones_to_label(phones)
    _check_known(labels)
    nuclei = _nucleus_indices(labels)
    if not nuclei:
        raise ValueError('phone sequence has no vowel nucleus')

    boundaries = [_maximal_onset_split(labels, left, right)
        for left, right in zip(nuclei, nuclei[1:])]
    starts = [0] + boundaries
    ends = boundaries + [len(phones)]
    return [Syllable(phones[s:e]) for s, e in zip(starts, ends)]


def resyllabify_phones(phones):
    '''Regroup phones into syllables by the Maximal Onset Principle.
    phones                  flat list of phones (IPA strings or objects with a
                            .label attribute)

    Returns a list of lists holding the SAME phone objects, regrouped at the
    suggested boundaries -- so caller objects (e.g. phraser phones) keep their
    identity. Derived from syllabify(), so the two always agree.
    Raises ValueError on unknown phones or when there is no nucleus.
    '''
    return [syllable.phones for syllable in syllabify(phones)]


def is_legal_syllable(phones, strict_coda=False):
    '''Judge whether one syllable is phonotactically legal in Dutch.
    phones                  a single syllable: a Syllable object or a list of
                            IPA phone symbols
    strict_coda             if True, a coda not in the conservative list makes
                            the result False; otherwise (default) an unlisted
                            coda is allowed but noted in the reason

    Coda validation is conservative and partial, so by default it never
    rejects a syllable on coda grounds alone. Onset and nucleus checks are
    reliable. Raises ValueError on unknown phones.
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
        reason = f'coda not in conservative list: {" ".join(coda)}'
        if strict_coda:
            return Result(False, reason)
        return Result(True, reason)
    return Result(True, 'legal syllable')


def _try_syllabify(flat):
    '''Maximal-onset suggestion, or None when the phones can't be split.'''
    try:
        return syllabify(flat)
    except ValueError:
        return None


def _first_illegal_syllable(given):
    '''Legality Result of the first illegal syllable, or None if all legal.'''
    for syllable in given:
        legal = is_legal_syllable(syllable)
        if not legal.ok:
            return legal
    return None


def _boundaries_match(given, suggested):
    '''True when the given split already matches the suggested split.'''
    given_labels = [phones_to_label(s) for s in given]
    suggested_labels = [phones_to_label(s.phones) for s in suggested]
    return given_labels == suggested_labels


def check_syllabification(syllables):
    '''Judge whether a sequence of syllables has correct boundaries.
    syllables               non-empty list of Syllable objects or lists of
                            phones

    Returns a Result. When the boundaries differ from the Maximal Onset
    Principle, ``result.suggested`` holds the suggested syllabification.
    Raises ValueError on unknown phones or empty input.
    '''
    if not syllables:
        raise ValueError('no syllables to check')
    original = list(syllables)
    given = [list(_as_phone_list(s)) for s in original]
    current = [Syllable(s) for s in given]
    flat = [phone for syllable in given for phone in syllable]
    # flat may not syllabify; the legality check below reports why
    suggested = _try_syllabify(flat)

    illegal = _first_illegal_syllable(given)
    if illegal is not None:
        ok, reason = False, illegal.reason
    elif _boundaries_match(given, suggested):
        ok, reason = True, 'correct syllable boundaries'
    else:
        ok, reason = False, 'boundaries differ from maximal onset'

    return Result(ok, reason, suggested=suggested, current=current,
        input=original)


class Result:
    '''Outcome of a legality or syllabification check.

    ok                      True if the check passed
    reason                  human readable explanation
    current                 given segmentation as repo Syllable objects
    suggested               maximal-onset segmentation as repo Syllable objects
    input                   the original objects passed in, exactly as given

    current and suggested are symmetric lists of repo Syllable objects, each
    wrapping the caller's own phone objects; current_groups / suggested_groups
    expose those phones directly (ready to apply to phraser objects). repr()
    stays on one line and omits the segmentation; str() shows current and
    suggested, aligned in a column.
    '''

    def __init__(self, ok, reason='', suggested=None, current=None,
            input=None):
        self.ok = ok
        self.reason = reason
        self.suggested = suggested
        self.current = current
        self.input = input

    def __bool__(self):
        return self.ok

    def __repr__(self):
        return f'Result(ok={self.ok}, reason={self.reason!r})'

    def __str__(self):
        width = len('suggested')
        lines = [repr(self)]
        if self.current is not None:
            lines.append(f'  {"current":>{width}}: '
                f'{self._segmentation(self.current)}')
        if self.suggested is not None:
            lines.append(f'  {"suggested":>{width}}: '
                f'{self._segmentation(self.suggested)}')
        return '\n'.join(lines)

    @staticmethod
    def _segmentation(syllables):
        return ' . '.join(s.label for s in syllables)

    @property
    def current_groups(self):
        '''Given segmentation as lists of the input phone objects, or None.
        Each group is current[i].phones -- the caller's own phones.'''
        if self.current is None:
            return None
        return [s.phones for s in self.current]

    @property
    def suggested_groups(self):
        '''Suggested segmentation as lists of the input phone objects, or None.
        Each group is suggested[i].phones -- the caller's own phones regrouped
        at the new boundaries, ready to apply to phraser objects.'''
        if self.suggested is None:
            return None
        return [s.phones for s in self.suggested]


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
