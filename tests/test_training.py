import pytest

celex = pytest.importorskip('celex')

from dutch_syllabifier.learned import ClassifierSyllabifier, CountSyllabifier
from dutch_syllabifier.training.classifier import (candidate_positions,
    train_classifier)
from dutch_syllabifier.training.counts import count_onsets_codas
from dutch_syllabifier.training.dataset import (normalize_phones,
    split_examples, syllable_groups, _one_nucleus_per_syllable)
from dutch_syllabifier.training.evaluate import (evaluate, gold_boundaries,
    rule_boundaries)

# aːx-jə, ɑ-pril, taː-fəl, hɛlp, straːt as (phones, labels, key)
EXAMPLES = [
    (['aː', 'x', 'j', 'ə'], [0, 1, 0], 'l1'),
    (['ɑ', 'p', 'r', 'ɪ', 'l'], [1, 0, 0, 0], 'l2'),
    (['t', 'aː', 'f', 'ə', 'l'], [0, 1, 0, 0], 'l3'),
    (['h', 'ɛ', 'l', 'p'], [0, 0, 0], 'l4'),
    (['s', 't', 'r', 'aː', 't'], [0, 0, 0, 0], 'l5'),
]


def test_normalize_phones():
    assert normalize_phones(['ʉ', 'g', 'ɒː']) == ['ʏ', 'ɡ', 'ɔː']
    assert normalize_phones(['iːː', 'yːː']) == ['iː', 'yː']
    assert normalize_phones(['d', 'dʒ']) is None


def test_syllable_groups():
    groups = syllable_groups(['aː', 'x', 'j', 'ə'], [0, 1, 0])
    assert groups == [['aː', 'x'], ['j', 'ə']]


def test_one_nucleus_per_syllable():
    assert _one_nucleus_per_syllable(['aː', 'x', 'j', 'ə'], [0, 1, 0])
    assert not _one_nucleus_per_syllable(['p', 's', 't'], [0, 0])
    # vowel hiatus needs a boundary between the two nuclei
    assert not _one_nucleus_per_syllable(['aː', 'ə'], [0])
    assert _one_nucleus_per_syllable(['aː', 'ə'], [1])


def test_split_examples_is_lemma_disjoint():
    examples = EXAMPLES + [(['aː', 'x'], [0], 'l1')]
    train, dev, test = split_examples(examples)
    assert len(train) + len(dev) + len(test) == len(examples)
    keys = [set(e[2] for e in part) for part in (train, dev, test)]
    assert not keys[0] & keys[1]
    assert not keys[0] & keys[2]
    assert not keys[1] & keys[2]


def test_count_onsets_codas():
    counts = count_onsets_codas(EXAMPLES)
    assert counts['onsets']['p r'] == 1
    assert counts['onsets']['s t r'] == 1
    assert counts['codas'][''] >= 3
    assert counts['codas']['l p'] == 1


def test_candidate_positions_targets():
    phones, labels, _ = EXAMPLES[1]  # ɑ-pril
    candidates = list(candidate_positions(phones, labels))
    boundaries = [(b, t) for _, b, t in candidates]
    assert boundaries == [(1, 1), (2, 0), (3, 0)]


def test_trained_models_fit_training_set():
    counts = CountSyllabifier(count_onsets_codas(EXAMPLES))
    model = train_classifier(EXAMPLES, min_count=1, c=100.0,
        verbose=False)
    classifier = ClassifierSyllabifier(model)
    for phones, labels, _ in EXAMPLES:
        gold = gold_boundaries(labels)
        assert counts.boundary_indices(phones) == gold
        assert classifier.boundary_indices(phones) == gold


def test_evaluate_baseline():
    scores = evaluate(rule_boundaries, EXAMPLES)
    assert scores['n'] == len(EXAMPLES)
    assert scores['word_accuracy'] == 1.0
    assert scores['failed'] == 0
