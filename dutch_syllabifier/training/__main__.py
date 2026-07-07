'''Train and evaluate both learned syllabifiers on CELEX Dutch.

Writes the model artifacts to dutch_syllabifier/data/ and prints the
maximal onset baseline next to both models on a lemma disjoint test
set. Run with: .venv/bin/python -m dutch_syllabifier.training
'''

import json
from pathlib import Path

from ..learned import (COUNTS_FILE, CLASSIFIER_FILE, CountSyllabifier,
    ClassifierSyllabifier)
from .classifier import train_classifier
from .counts import count_onsets_codas
from .dataset import load_examples, split_examples
from .evaluate import evaluate, report, rule_boundaries

DATA_DIR = Path(__file__).parent.parent / 'data'


def save_artifact(filename, artifact):
    '''Write a model artifact as JSON to the package data directory.'''
    path = DATA_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(artifact, f, ensure_ascii=False)
    print(f'wrote {path}')


def main(language='dutch'):
    '''Train the count model and the classifier, then evaluate.'''
    examples = load_examples(language)
    train, dev, test = split_examples(examples)
    print(f'split: {len(train)} train, {len(dev)} dev, {len(test)} test')

    counts = count_onsets_codas(train)
    save_artifact(COUNTS_FILE, counts)
    model = train_classifier(train)
    save_artifact(CLASSIFIER_FILE, model)

    count_model = CountSyllabifier(counts)
    classifier = ClassifierSyllabifier(model)
    report('baseline', evaluate(rule_boundaries, test))
    report('counts', evaluate(count_model.boundary_indices, test))
    report('classifier', evaluate(classifier.boundary_indices, test))


if __name__ == '__main__':
    main()
