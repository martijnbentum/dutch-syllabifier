'''Count onset and coda clusters for the CountSyllabifier.'''

from collections import Counter

from .. import phone_inventory
from .dataset import syllable_groups


def count_onsets_codas(examples):
    '''Count onset and coda clusters over all syllables.
    examples                list of (phones, labels, key)

    Returns {'onsets': ..., 'codas': ...} mapping space joined
    clusters (empty string for none) to counts, the artifact format
    of learned.CountSyllabifier.
    '''
    onsets, codas = Counter(), Counter()
    for phones, labels, _ in examples:
        for group in syllable_groups(phones, labels):
            onset, coda = _split_syllable(group)
            onsets[' '.join(onset)] += 1
            codas[' '.join(coda)] += 1
    return {'onsets': dict(onsets), 'codas': dict(codas)}


def _split_syllable(group):
    '''Onset and coda consonants around the nucleus of one syllable.'''
    nucleus = [i for i, p in enumerate(group)
        if phone_inventory.is_nucleus(p)]
    first, last = nucleus[0], nucleus[-1]
    return group[:first], group[last + 1:]
