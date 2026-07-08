'''Dutch phone inventory: the known phones by category and the
accepted input aliases.

All symbol knowledge lives in the JSON files in data/. The inventory
files are single-canonical: every phone appears in exactly one form and
accepted input variants live in aliases.json, applied by
canonical_label() at lookup time. Caller phones are never rewritten.
'''

import json
from importlib import resources


def _load_json(filename):
    '''Load a JSON data file shipped inside the package.
    filename                name of a file in dutch_syllabifier/data
    '''
    path = resources.files('dutch_syllabifier').joinpath('data', filename)
    with path.open(encoding='utf-8') as f:
        return json.load(f)


# phone inventory, by category; known phones is the category union
VOWELS = set(_load_json('vowels.json'))
DIPHTHONGS = set(_load_json('diphthongs.json'))
CONSONANTS = set(_load_json('consonants.json'))
KNOWN_PHONES = VOWELS | DIPHTHONGS | CONSONANTS

# input symbols accepted as equivalent to a canonical phone: SAMPA style
# 'w' for 'ʋ', ascii 'g' for ipa 'ɡ' and the bare tense vowels for the
# long forms (vowel length never affects Dutch syllable boundaries)
ALIASES = _load_json('aliases.json')


def _validate_aliases():
    '''Raise ValueError when aliases.json drifts from the inventory.

    Alias targets must be canonical phones and alias keys may not
    shadow one. Keeps the symbol set consistent so it cannot silently
    drift.
    '''
    bad_targets = set(ALIASES.values()) - KNOWN_PHONES
    if bad_targets:
        raise ValueError(
            f'aliases.json targets unknown phones: {sorted(bad_targets)}')
    shadowed = set(ALIASES) & KNOWN_PHONES
    if shadowed:
        raise ValueError(
            f'aliases.json keys shadow canonical phones: {sorted(shadowed)}')


_validate_aliases()


def canonical_label(label):
    '''Map an accepted alias to its canonical phone (e.g. 'w' -> 'ʋ').'''
    return ALIASES.get(label, label)


def is_known(label):
    '''Return True if the label is a known Dutch phone (aliases accepted).'''
    return canonical_label(label) in KNOWN_PHONES
