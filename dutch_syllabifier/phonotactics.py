'''Phonotactic facts about Dutch syllables: which phones can fill the
nucleus role and which onset and coda clusters are legal.

The legal clusters are whitelists in data/legal_onsets.json and
data/legal_codas.json; they may only use phones declared in the
consonant inventory, validated at import time. A sonority based onset
rule backs the offline onset lint (docs/sonority_onset_fallback.md);
the whitelist stays authoritative for boundary placement.
'''

from .phone_inventory import (CONSONANTS, DIPHTHONGS, VOWELS, _load_json,
    canonical_label)
from .sonority import sonority_weight

# nucleus is a syllable role; vowels and diphthongs can fill it
NUCLEI = VOWELS | DIPHTHONGS


def _as_tuples(sequences):
    '''Turn a list of phone lists into a set of tuples for fast lookup.'''
    return set(tuple(seq) for seq in sequences)


LEGAL_ONSETS = _as_tuples(_load_json('legal_onsets.json'))
LEGAL_CODAS = _as_tuples(_load_json('legal_codas.json'))


def _validate_clusters():
    '''Raise ValueError when a cluster file uses undeclared consonants.'''
    for name, clusters in (('legal_onsets', LEGAL_ONSETS),
            ('legal_codas', LEGAL_CODAS)):
        unknown = set().union(*clusters) - CONSONANTS if clusters else set()
        if unknown:
            raise ValueError(
                f'{name}.json uses undeclared consonants: {sorted(unknown)}')


_validate_clusters()


def is_nucleus(label):
    '''Return True if the label is a vowel or diphthong.

    Length is optional: tense vowels are accepted with or without 'ː' (e.g.
    'eː' and 'e' both count), since vowel length never affects Dutch syllable
    boundaries.
    '''
    return canonical_label(label) in NUCLEI


def nucleus_indices(labels):
    '''Return the indices of nucleus (vowel or diphthong) labels.
    labels                  list of IPA labels
    '''
    return [i for i, label in enumerate(labels) if is_nucleus(label)]


def is_legal_onset(labels):
    '''Return True if a sequence of labels is a legal Dutch onset.
    labels                  list or tuple of consonant labels (empty is legal)
    '''
    onset = tuple(canonical_label(l) for l in labels)
    return len(onset) == 0 or onset in LEGAL_ONSETS


# Sonority Sequencing Principle parameters for Dutch onsets and codas
MAX_ONSET_LENGTH = 3
MIN_SONORITY_RISE = 1
MAX_CODA_LENGTH = 4
MIN_SONORITY_FALL = 0    # plateaus allowed (rl); rises are rejected
CODA_APPENDICES = ('s', 't')

# final devoicing: voiced obstruents never surface in a Dutch coda,
# and /h/ never fills a coda at all
VOICED_OBSTRUENTS = frozenset(('b', 'd', 'ɡ', 'v', 'z', 'ʒ', 'ɣ'))
_NON_CODA_PHONES = VOICED_OBSTRUENTS | {'h'} | NUCLEI


def is_sonority_legal_onset(labels):
    '''Return True if a sequence of labels is an SSP-valid Dutch onset.
    labels                  list or tuple of consonant labels (empty is legal)

    Advisory companion to is_legal_onset: sonority must rise strictly
    toward the nucleus, after allowing one leading /s/ appendix
    (sp, str, ...); /ŋ/ never fills an onset. Overgenerates (tl, dl),
    so boundary placement keeps using the whitelist; this rule backs
    the onset lint that cross-checks the whitelist.
    '''
    onset = [canonical_label(l) for l in labels]
    if len(onset) > MAX_ONSET_LENGTH:
        return False
    if 'ŋ' in onset or any(label in NUCLEI for label in onset):
        return False
    if len(onset) >= 2 and onset[0] == 's':
        onset = onset[1:]
    weights = [sonority_weight(label) for label in onset]
    return all(later - earlier >= MIN_SONORITY_RISE
        for earlier, later in zip(weights, weights[1:]))


def is_legal_coda(labels):
    '''Return True if a sequence of labels is a legal Dutch coda.
    labels                  list or tuple of consonant labels (empty is legal)

    The list covers every CELEX-attested, sonority-valid word-final coda.
    '''
    coda = tuple(canonical_label(l) for l in labels)
    return len(coda) == 0 or coda in LEGAL_CODAS


def is_sonority_legal_coda(labels):
    '''Return True if a sequence of labels is a sonority-valid Dutch coda.
    labels                  list or tuple of consonant labels (empty is legal)

    Advisory companion to is_legal_coda: sonority may not rise away
    from the nucleus, after stripping a trailing /s/ /t/ appendix
    (herfst, ernst, ...); final devoicing bans voiced obstruents and
    /h/ never fills a coda. Backs the coda lint; is_legal_coda keeps
    using the whitelist.
    '''
    coda = [canonical_label(l) for l in labels]
    if len(coda) > MAX_CODA_LENGTH:
        return False
    if any(label in _NON_CODA_PHONES for label in coda):
        return False
    while coda and coda[-1] in CODA_APPENDICES:
        coda.pop()
    weights = [sonority_weight(label) for label in coda]
    return all(earlier - later >= MIN_SONORITY_FALL
        for earlier, later in zip(weights, weights[1:]))


def is_sonority_legal_syllable(labels):
    '''Return True if a sequence of labels is a sonority-valid syllable.
    labels                  list or tuple of phone labels of one syllable

    Requires exactly one nucleus, an SSP-valid onset before it and a
    sonority-valid coda after it: sonority rises to the nucleus and
    does not rise again toward the edge. Advisory, like the onset and
    coda rules it combines.
    '''
    syllable = [canonical_label(l) for l in labels]
    nuclei = [i for i, label in enumerate(syllable) if label in NUCLEI]
    if len(nuclei) != 1:
        return False
    nucleus = nuclei[0]
    return (is_sonority_legal_onset(syllable[:nucleus])
        and is_sonority_legal_coda(syllable[nucleus + 1:]))
