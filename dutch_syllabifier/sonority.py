'''Sonority of Dutch phones: every phone belongs to a sonority class
and the classes are ranked on a scale, backing sonority based rules
such as the Sonority Sequencing Principle.

Consonant class membership is symbol knowledge and lives in
data/sonority_classes.json; the vowel class is derived from the vowel
and diphthong categories, so it never needs a data entry. The scale
order is relational knowledge and lives here in code.

Sonority is a property of the phone category, not of the syllable
role: a syllabic /l/ would fill a nucleus but stay a liquid. So the
vowel class comes from the inventory, not from phonotactics.NUCLEI --
which also keeps phonotactics free to build on sonority (the planned
SSP onset lint) without a circular import.
'''

from .phone_inventory import (CONSONANTS, DIPHTHONGS, VOWELS, _load_json,
    canonical_label)
from .phones import phone_to_label

# class ranking, least -> most sonorous; the weight is the scale index
SONORITY_SCALE = ('stop', 'fricative', 'nasal', 'liquid', 'glide', 'vowel')
SONORITY_WEIGHTS = {name: i for i, name in enumerate(SONORITY_SCALE)}

_CONSONANT_CLASSES = _load_json('sonority_classes.json')


def _phone_to_class():
    '''Build the phone to class table: consonants from the data file,
    vowels and diphthongs as the vowel class.'''
    table = {}
    for name, phones in _CONSONANT_CLASSES.items():
        for phone in phones:
            table[phone] = name
    for phone in VOWELS | DIPHTHONGS:
        table[phone] = 'vowel'
    return table


PHONE_TO_SONORITY_CLASS = _phone_to_class()


def _validate_sonority_classes():
    '''Raise ValueError when sonority_classes.json drifts from the
    scale or the consonant inventory.'''
    bad_names = set(_CONSONANT_CLASSES) ^ (set(SONORITY_SCALE) - {'vowel'})
    if bad_names:
        raise ValueError(
            f'sonority_classes.json class names must match the consonant '
            f'part of SONORITY_SCALE; differing={sorted(bad_names)}')
    listed = [p for phones in _CONSONANT_CLASSES.values() for p in phones]
    duplicates = sorted(p for p in set(listed) if listed.count(p) > 1)
    if duplicates:
        raise ValueError(
            f'sonority_classes.json lists phones in more than one class: '
            f'{duplicates}')
    missing = CONSONANTS - set(listed)
    extra = set(listed) - CONSONANTS
    if missing or extra:
        raise ValueError(
            f'sonority_classes.json must classify exactly the consonants; '
            f'missing={sorted(missing)} extra={sorted(extra)}')


_validate_sonority_classes()


def sonority_class(phone):
    '''Return the sonority class name of one phone.
    phone                   IPA string or object with a .label attribute
    '''
    label = canonical_label(phone_to_label(phone))
    if label not in PHONE_TO_SONORITY_CLASS:
        raise ValueError(f'unknown phone, no sonority class: {label!r}')
    return PHONE_TO_SONORITY_CLASS[label]


def sonority_weight(phone):
    '''Return the sonority weight of one phone (higher = more sonorous).
    phone                   IPA string or object with a .label attribute
    '''
    return SONORITY_WEIGHTS[sonority_class(phone)]


def sonority_classes(phones):
    '''Return the sonority class name of each phone.
    phones                  list of IPA strings or objects with .label
    '''
    return [sonority_class(phone) for phone in phones]


def sonority_weights(phones):
    '''Return the sonority weight of each phone.
    phones                  list of IPA strings or objects with .label
    '''
    return [sonority_weight(phone) for phone in phones]
