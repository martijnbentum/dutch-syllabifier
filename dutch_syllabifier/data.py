import json
from importlib import resources


def _load_json(filename):
    '''Load a JSON data file shipped inside the package.
    filename                name of a file in dutch_syllabifier/data
    '''
    path = resources.files('dutch_syllabifier').joinpath('data', filename)
    with path.open(encoding='utf-8') as f:
        return json.load(f)


def _as_tuples(sequences):
    '''Turn a list of phone lists into a set of tuples for fast lookup.'''
    return set(tuple(seq) for seq in sequences)


# phone inventory, by category
VOWELS = set(_load_json('vowels.json'))
DIPHTHONGS = set(_load_json('diphthongs.json'))
CONSONANTS = set(_load_json('consonants.json'))

# nuclei is a syllable role; known phones is the category union
NUCLEI = VOWELS | DIPHTHONGS
KNOWN_PHONES = VOWELS | DIPHTHONGS | CONSONANTS

LEGAL_ONSETS = _as_tuples(_load_json('legal_onsets.json'))
LEGAL_CODAS = _as_tuples(_load_json('legal_codas.json'))


def _validate_clusters():
    '''Raise ValueError if any onset/coda cluster uses an undeclared consonant.

    Keeps the cluster data files consistent with consonants.json so the phone
    inventory cannot silently drift.
    '''
    for name, clusters in (('legal_onsets', LEGAL_ONSETS),
            ('legal_codas', LEGAL_CODAS)):
        unknown = set().union(*clusters) - CONSONANTS if clusters else set()
        if unknown:
            raise ValueError(
                f'{name}.json uses undeclared consonants: {sorted(unknown)}')


_validate_clusters()


# input aliases: symbols accepted as equivalent to a canonical phone. 'w' is
# accepted for the labiodental approximant 'ʋ' (SAMPA-style input and the
# post-vocalic offglide in nieuw/eeuw); it is not a separate Dutch phoneme, so
# it is normalised here rather than duplicated across the cluster data files,
# which keeps those files single-canonical and drift-proof.
PHONE_ALIASES = {'w': 'ʋ'}


def canonical_label(label):
    '''Map an accepted alias to its canonical phone (e.g. 'w' -> 'ʋ').'''
    return PHONE_ALIASES.get(label, label)


def is_nucleus(label):
    '''Return True if the label is a vowel or diphthong.

    Length is optional: tense vowels are accepted with or without 'ː' (e.g.
    'eː' and 'e' both count), since vowel length never affects Dutch syllable
    boundaries.
    '''
    return canonical_label(label) in NUCLEI


def is_known(label):
    '''Return True if the label is a known Dutch phone (aliases accepted).'''
    return canonical_label(label) in KNOWN_PHONES


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
