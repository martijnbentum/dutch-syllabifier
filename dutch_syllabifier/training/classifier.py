'''Train the boundary classifier for the ClassifierSyllabifier.

Only candidate positions are used for training: positions between two
nuclei, the same positions the decoder scores. The features come from
learned.boundary_features, so training and inference always agree.
'''

from collections import Counter

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression

from ..learned import boundary_features, model_label, _nucleus_indices


def candidate_positions(phones, labels):
    '''Yield (boundary, target) for every position between two nuclei.
    phones                  list of phone labels for one word
    labels                  per position boundary labels

    boundary is a candidate syllable start index; target is 1 when the
    gold boundary of that intervowel gap sits there.
    '''
    model_labels = [model_label(p) for p in phones]
    nuclei = _nucleus_indices(model_labels)
    for left, right in zip(nuclei, nuclei[1:]):
        for boundary in range(left + 1, right + 1):
            yield model_labels, boundary, labels[boundary - 1]


def _feature_counts(examples):
    '''Count feature occurrences over all candidate positions.'''
    counts = Counter()
    for phones, labels, _ in examples:
        for model_labels, boundary, _ in candidate_positions(phones,
                labels):
            counts.update(boundary_features(model_labels, boundary))
    return counts


def _build_matrix(examples, vocabulary):
    '''Sparse feature matrix and target vector for all candidates.'''
    indices, indptr, targets = [], [0], []
    for phones, labels, _ in examples:
        for model_labels, boundary, target in candidate_positions(
                phones, labels):
            features = boundary_features(model_labels, boundary)
            row = [vocabulary[f] for f in features if f in vocabulary]
            indices.extend(sorted(set(row)))
            indptr.append(len(indices))
            targets.append(target)
    values = np.ones(len(indices), dtype=np.float64)
    shape = (len(targets), len(vocabulary))
    matrix = csr_matrix((values, indices, indptr), shape=shape)
    return matrix, np.array(targets)


def train_classifier(examples, min_count=3, c=1.0, verbose=True):
    '''Train an l1 logistic regression boundary classifier.
    examples                list of (phones, labels, key)
    min_count               drop features seen fewer times than this
    c                       inverse regularization strength
    verbose                 print dataset and model sizes

    Returns the learned.ClassifierSyllabifier artifact: a dict with
    'weights' (feature name to weight, zeros dropped) and 'intercept'.
    '''
    counts = _feature_counts(examples)
    vocabulary = {}
    for feature, count in counts.items():
        if count >= min_count: vocabulary[feature] = len(vocabulary)
    matrix, targets = _build_matrix(examples, vocabulary)
    if verbose:
        print(f'training on {matrix.shape[0]} boundary candidates, '
            f'{len(vocabulary)} features')
    model = LogisticRegression(l1_ratio=1, solver='liblinear', C=c)
    model.fit(matrix, targets)
    weights = {}
    coefficients = model.coef_[0]
    for feature, index in vocabulary.items():
        if coefficients[index] != 0:
            weights[feature] = float(coefficients[index])
    if verbose:
        print(f'kept {len(weights)} nonzero weights')
    return {'intercept': float(model.intercept_[0]), 'weights': weights}
