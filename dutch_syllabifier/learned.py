'''Learned syllabifiers trained on CELEX syllable boundaries.

Two opt-in models: CountSyllabifier scores a boundary with onset and
coda log probabilities counted from CELEX; ClassifierSyllabifier scores
it with boundary classifier weights over a phone window. Both decode
under the same constraint: exactly one boundary between two nuclei, so
every syllable keeps exactly one nucleus. Neither replaces syllabify();
maximal onset stays the default. Training code lives in training/.
'''

import json
import math
from importlib import resources

from . import phone_inventory, phonotactics
from .phones import phones_to_label
from .syllables import Syllable

COUNTS_FILE = 'celex_onset_coda_counts.json'
CLASSIFIER_FILE = 'celex_boundary_classifier.json'


def load_artifact(filename):
    '''Load a trained model JSON file shipped inside the package.
    filename                name of a file in dutch_syllabifier/data
    '''
    path = resources.files('dutch_syllabifier').joinpath('data', filename)
    with path.open(encoding='utf-8') as f:
        return json.load(f)


def boundary_features(labels, boundary):
    '''Feature strings for a boundary before labels[boundary].
    labels                  list of canonical phone labels for a word
    boundary                candidate boundary index (syllable start)

    Shared between training and inference so the two always agree.
    Uses a three phone window on both sides padded with '#'.
    '''
    window = []
    for offset in (-3, -2, -1, 0, 1, 2):
        index = boundary + offset
        if 0 <= index < len(labels): window.append(labels[index])
        else: window.append('#')
    l3, l2, l1, r1, r2, r3 = window
    features = [f'l1={l1}', f'l2={l2}', f'l3={l3}', f'r1={r1}',
        f'r2={r2}', f'r3={r3}', f'l2l1={l2} {l1}', f'l1r1={l1} {r1}',
        f'r1r2={r1} {r2}', f'l2l1r1={l2} {l1} {r1}',
        f'l1r1r2={l1} {r1} {r2}']
    features.append('cv=' + ''.join(_cv_symbol(l) for l in window))
    return features


def _cv_symbol(label):
    '''V, C or # for one window label.'''
    if label == '#': return '#'
    return 'V' if phonotactics.is_nucleus(label) else 'C'


def _consonants_before(labels, boundary):
    '''Consonant labels from the previous nucleus up to the boundary.'''
    coda = []
    for index in range(boundary - 1, -1, -1):
        if phonotactics.is_nucleus(labels[index]): break
        coda.append(labels[index])
    return list(reversed(coda))


def _consonants_after(labels, boundary):
    '''Consonant labels from the boundary up to the next nucleus.'''
    onset = []
    for index in range(boundary, len(labels)):
        if phonotactics.is_nucleus(labels[index]): break
        onset.append(labels[index])
    return onset


class _LearnedSyllabifier:
    '''Shared decoding for the learned models.

    A subclass provides score(labels, boundary): the score for a
    syllable boundary before labels[boundary]. Decoding places exactly
    one boundary between two consecutive nuclei, at the best scoring
    position, so every syllable keeps exactly one nucleus.
    '''

    def syllabify(self, phones):
        '''Syllabify a phone sequence with the learned model.
        phones              list of phones (IPA strings or objects
                            with .label)

        Returns a list of Syllable objects wrapping the caller's own
        phones. Raises ValueError on unknown phones or no nucleus.
        '''
        phones = list(phones)
        boundaries = self.boundary_indices(phones)
        starts = [0] + boundaries
        ends = boundaries + [len(phones)]
        return [Syllable(phones[s:e]) for s, e in zip(starts, ends)]

    def boundary_indices(self, phones):
        '''Indices where a new syllable starts (word start excluded).
        phones              list of phones (IPA strings or objects
                            with .label)
        '''
        labels = phones_to_label(phones)
        phone_inventory.check_known(labels)
        labels = [phone_inventory.canonical_label(label)
            for label in labels]
        nuclei = phonotactics.nucleus_indices(labels)
        if not nuclei:
            raise ValueError('phone sequence has no vowel nucleus')
        boundaries = []
        for left, right in zip(nuclei, nuclei[1:]):
            candidates = range(left + 1, right + 1)
            best = max(candidates, key=lambda b: self.score(labels, b))
            boundaries.append(best)
        return boundaries


class CountSyllabifier(_LearnedSyllabifier):
    '''Probabilistic maximal onset: boundaries score as the smoothed
    log probability of the resulting coda and onset clusters, counted
    from CELEX syllables.'''

    def __init__(self, counts=None):
        '''Create the model from cluster counts.
        counts              dict with 'onsets' and 'codas' mapping
                            space joined clusters to counts; omit to
                            load the packaged CELEX counts
        '''
        if counts is None: counts = load_artifact(COUNTS_FILE)
        self.onsets = counts['onsets']
        self.codas = counts['codas']
        self._onset_total = sum(self.onsets.values())
        self._coda_total = sum(self.codas.values())

    def score(self, labels, boundary):
        '''Log probability of the coda and onset made by a boundary.'''
        coda = ' '.join(_consonants_before(labels, boundary))
        onset = ' '.join(_consonants_after(labels, boundary))
        score = self._log_prob(self.codas, self._coda_total, coda)
        score += self._log_prob(self.onsets, self._onset_total, onset)
        return score

    def _log_prob(self, table, total, cluster):
        '''Smoothed log probability of one cluster in a count table.'''
        count = table.get(cluster, 0)
        return math.log((count + 0.5) / (total + 0.5 * (len(table) + 1)))


class ClassifierSyllabifier(_LearnedSyllabifier):
    '''Boundary classifier: boundaries score as a linear model over
    boundary_features, trained on CELEX (see training/classifier.py).'''

    def __init__(self, model=None):
        '''Create the model from classifier weights.
        model               dict with 'weights' (feature name to
                            weight) and 'intercept'; omit to load the
                            packaged CELEX classifier
        '''
        if model is None: model = load_artifact(CLASSIFIER_FILE)
        self.weights = model['weights']
        self.intercept = model['intercept']

    def score(self, labels, boundary):
        '''Linear score for a boundary before labels[boundary].'''
        score = self.intercept
        for feature in boundary_features(labels, boundary):
            score += self.weights.get(feature, 0.0)
        return score

    def probability(self, labels, boundary):
        '''Sigmoid of score: boundary probability in isolation.'''
        score = self.score(labels, boundary)
        if score >= 0:
            z = math.exp(-score)
            return 1 / (1 + z)
        z = math.exp(score)
        return z / (1 + z)
