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


class Legality:
    '''Phonotactic legality of one syllable: a boolean flag per finding.

    Build it from a syllable with Legality.judge(syllable); the bare
    constructor takes explicit flags. Findings (no_nucleus, multiple_nuclei,
    illegal_onset, unlisted_coda) are plain booleans you can branch on; ok and
    reason are derived. unlisted_coda is tolerated by default, so it does not
    clear ok. offending_phones holds the phones that triggered the finding (the
    onset or coda), shown in reason.
    '''

    # findings in priority order; the attribute name doubles as the message
    _FINDINGS = ('no_nucleus', 'multiple_nuclei', 'illegal_onset', 'unlisted_coda')
    _FATAL = ('no_nucleus', 'multiple_nuclei', 'illegal_onset')

    def __init__(self, no_nucleus=False, multiple_nuclei=False,
            illegal_onset=False, unlisted_coda=False, offending_phones=()):
        '''Create a legality verdict from explicit finding flags.
        no_nucleus              syllable has no vowel nucleus
        multiple_nuclei         syllable has more than one nucleus
        illegal_onset           onset is not a legal Dutch onset cluster
        unlisted_coda           coda is not in the conservative list (tolerated)
        offending_phones        the phones that triggered the finding (the
                                onset or coda), shown in reason
        '''
        self.no_nucleus = no_nucleus
        self.multiple_nuclei = multiple_nuclei
        self.illegal_onset = illegal_onset
        self.unlisted_coda = unlisted_coda
        self.offending_phones = list(offending_phones)

    @classmethod
    def legal(cls):
        '''A passing legality: no findings set.'''
        return cls()

    @classmethod
    def judge(cls, syllable):
        '''Apply the Dutch phonotactic rules to one syllable.
        syllable                a Syllable or list of phones

        Returns a Legality with at most one finding set. Coda validation is
        conservative, so an unlisted coda is noted but tolerated. Raises
        ValueError on unknown phones.
        '''
        labels = phones_to_label(_as_phone_list(syllable))
        _check_known(labels)
        nuclei = _nucleus_indices(labels)
        if len(nuclei) == 0:
            return cls(no_nucleus=True)
        if len(nuclei) > 1:
            return cls(multiple_nuclei=True)
        n = nuclei[0]
        onset, coda = labels[:n], labels[n + 1:]
        if not data.is_legal_onset(onset):
            return cls(illegal_onset=True, offending_phones=onset)
        if not data.is_legal_coda(coda):
            return cls(unlisted_coda=True, offending_phones=coda)
        return cls.legal()

    @property
    def ok(self):
        '''True unless a fatal finding fired (unlisted coda is tolerated).'''
        return not any(getattr(self, f) for f in self._FATAL)

    @property
    def finding(self):
        '''Name of the first active finding, in priority order, or None.'''
        return next((f for f in self._FINDINGS if getattr(self, f)), None)

    @property
    def reason(self):
        '''Human readable summary, derived from the active finding's name.'''
        if self.finding is None:
            return 'legal syllable'
        text = self.finding.replace('_', ' ')
        if self.offending_phones:
            return f'{text}: {" ".join(self.offending_phones)}'
        return text

    def __bool__(self):
        return self.ok

    def __repr__(self):
        return f'Legality({self.finding or "legal"})'

    def __str__(self):
        return self.reason


def is_legal_syllable(syllable):
    '''True if the syllable is phonotactically legal (unlisted coda tolerated).
    syllable                a Syllable object or a list of IPA phone symbols

    Onset and nucleus checks are reliable; coda validation is conservative and
    never rejects on coda grounds alone. Raises ValueError on unknown phones.
    '''
    return Legality.judge(syllable).ok


def _try_syllabify(flat):
    '''Maximal-onset suggestion, or None when the phones can't be split.'''
    try:
        return syllabify(flat)
    except ValueError:
        return None


def check_syllabification(syllables):
    '''Judge whether a sequence of syllables has correct boundaries.
    syllables               non-empty list of Syllable objects or lists of
                            phones

    Returns a Result. Each current syllable carries its .legality, and the
    Result derives ok/reason from those plus the maximal-onset suggestion.
    Raises ValueError on unknown phones or empty input.
    '''
    if not syllables:
        raise ValueError('no syllables to check')
    original = list(syllables)
    current = [Syllable(list(_as_phone_list(s))) for s in original]
    for syllable in current:
        syllable.legality = Legality.judge(syllable)
    flat = [phone for syllable in current for phone in syllable.phones]
    suggested = _try_syllabify(flat)
    return Result(current=current, suggested=suggested, input=original)


class Result:
    '''Outcome of a syllabification check, with ok/reason derived from data.

    current                 given segmentation as repo Syllable objects, each
                            carrying its .legality
    suggested               maximal-onset segmentation as repo Syllable objects
    input                   the original objects passed in, exactly as given

    ok and reason are computed: ok is True when every current syllable is legal
    and the boundaries match the maximal-onset suggestion; reason points at the
    first illegal syllable, else describes the boundary outcome. uncheckable is
    True for the degenerate result built with error= (no current/suggested),
    used when the input could not be analysed at all (e.g. unknown phone or
    empty input).

    current and suggested are symmetric lists of repo Syllable objects, each
    wrapping the caller's own phone objects; current_groups / suggested_groups
    expose those phones directly (ready to apply to phraser objects). repr()
    stays on one line and omits the segmentation; str() shows current and
    suggested, aligned in a column.
    '''

    def __init__(self, current=None, suggested=None, input=None, error=None):
        self.current = current
        self.suggested = suggested
        self.input = input
        self.error = error

    @property
    def uncheckable(self):
        '''True for a result built with error= (input could not be analysed).'''
        return self.error is not None

    @property
    def _bad_syllable(self):
        '''First current syllable that failed legality, or None.'''
        if self.current is None:
            return None
        return next((s for s in self.current
            if s.legality is not None and not s.legality.ok), None)

    @property
    def boundaries_match(self):
        '''True when the given split already matches the maximal-onset split.'''
        if self.current is None or self.suggested is None:
            return False
        given = [phones_to_label(s.phones) for s in self.current]
        return given == [phones_to_label(s.phones) for s in self.suggested]

    @property
    def ok(self):
        if self.error is not None:
            return False
        return self._bad_syllable is None and self.boundaries_match

    @property
    def reason(self):
        if self.error is not None:
            return self.error
        if self._bad_syllable is not None:
            return self._bad_syllable.legality.reason
        return ('correct syllable boundaries' if self.boundaries_match
            else 'boundaries differ from maximal onset')

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
