'''Evaluate syllabifiers against CELEX boundary labels.'''

from ..syllabifier import syllabify


def gold_boundaries(labels):
    '''Boundary indices (syllable starts) from per position labels.'''
    return [i + 1 for i, label in enumerate(labels) if label]


def rule_boundaries(phones):
    '''Boundary indices from the maximal onset baseline syllabify().'''
    boundaries, position = [], 0
    for syllable in syllabify(phones)[:-1]:
        position += len(syllable.phones)
        boundaries.append(position)
    return boundaries


def evaluate(predict, examples):
    '''Score a boundary predictor against gold labels.
    predict                 function phones -> list of boundary indices
    examples                list of (phones, labels, key)

    Returns a dict with word_accuracy, boundary precision/recall/f1,
    the number of words and how many raised ValueError (counted as
    fully wrong).
    '''
    correct, failed = 0, 0
    tp, fp, fn = 0, 0, 0
    for phones, labels, _ in examples:
        gold = gold_boundaries(labels)
        try:
            predicted = predict(phones)
        except ValueError:
            failed += 1
            predicted = []
        if predicted == gold: correct += 1
        gold_set, predicted_set = set(gold), set(predicted)
        tp += len(gold_set & predicted_set)
        fp += len(predicted_set - gold_set)
        fn += len(gold_set - predicted_set)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 0.0
    if precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    return {'word_accuracy': correct / len(examples), 'precision':
        precision, 'recall': recall, 'f1': f1, 'n': len(examples),
        'failed': failed}


def report(name, scores):
    '''One line summary of an evaluate() result.'''
    m = f'{name:12} word accuracy {scores["word_accuracy"]:.4f} | '
    m += f'boundary f1 {scores["f1"]:.4f} '
    m += f'(p {scores["precision"]:.4f}, r {scores["recall"]:.4f}) | '
    m += f'{scores["n"]} words, {scores["failed"]} failed'
    print(m)
