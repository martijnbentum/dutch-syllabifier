'''Phonotactic legality of Dutch onset and coda clusters.

The legal clusters are whitelists in data/legal_onsets.json and
data/legal_codas.json; they may only use phones declared in the
consonant inventory, validated at import time.
'''

from .phone_inventory import CONSONANTS, _load_json, canonical_label


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


def is_legal_onset(labels):
    '''Return True if a sequence of labels is a legal Dutch onset.
    labels                  list or tuple of consonant labels (empty is legal)
    '''
    onset = tuple(canonical_label(l) for l in labels)
    return len(onset) == 0 or onset in LEGAL_ONSETS


def is_legal_coda(labels):
    '''Return True if a sequence of labels is a legal Dutch coda.
    labels                  list or tuple of consonant labels (empty is legal)

    Coda validation is conservative and partial in version 1.
    '''
    coda = tuple(canonical_label(l) for l in labels)
    return len(coda) == 0 or coda in LEGAL_CODAS
