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
ILLEGAL_ONSETS = _as_tuples(_load_json('illegal_onsets.json'))
LEGAL_CODAS = _as_tuples(_load_json('legal_codas.json'))


def _validate_clusters():
    '''Raise ValueError if any onset/coda cluster uses an undeclared consonant.

    Keeps the cluster data files consistent with consonants.json so the phone
    inventory cannot silently drift.
    '''
    for name, clusters in (('legal_onsets', LEGAL_ONSETS),
            ('illegal_onsets', ILLEGAL_ONSETS),
            ('legal_codas', LEGAL_CODAS)):
        unknown = set().union(*clusters) - CONSONANTS if clusters else set()
        if unknown:
            raise ValueError(
                f'{name}.json uses undeclared consonants: {sorted(unknown)}')


_validate_clusters()


def is_nucleus(label):
    '''Return True if the label is a vowel or diphthong.'''
    return label in NUCLEI


def is_known(label):
    '''Return True if the label is a known Dutch phone.'''
    return label in KNOWN_PHONES


def is_legal_onset(labels):
    '''Return True if a sequence of labels is a legal Dutch onset.
    labels                  list or tuple of consonant labels (empty is legal)
    '''
    return len(labels) == 0 or tuple(labels) in LEGAL_ONSETS


def is_legal_coda(labels):
    '''Return True if a sequence of labels is a legal Dutch coda.
    labels                  list or tuple of consonant labels (empty is legal)

    Coda validation is conservative and partial in version 1.
    '''
    return len(labels) == 0 or tuple(labels) in LEGAL_CODAS
