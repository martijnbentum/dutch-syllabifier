'''Load CELEX training examples and normalize them to this package.

An example is (phones, labels, key): phones use this package's ipa
inventory, labels[i] is 1 when a syllable boundary follows phones[i]
and key groups inflectional family members (lemma id), so splits can
be made lemma disjoint.
'''

import hashlib

from celex.training_data import training_examples

from .. import phone_inventory, phonotactics

# celex ipa symbols this package's inventory deliberately collapses
# (see NOTES/phone_symbol_normalization_2026-07-08.md); plain aliases
# like ascii 'g' are handled by phone_inventory.canonical_label
CELEX_TO_IPA = {'ʉ': 'ʏ', 'ɒː': 'ɔː', 'iːː': 'iː', 'yːː': 'yː'}


def normalize_phones(phones):
    '''Map celex ipa symbols to this package's canonical labels.
    phones                  list of celex ipa symbols

    Returns the normalized list, or None when a symbol has no single
    phone equivalent (e.g. the loanword affricate dʒ). Emitting
    canonical labels here keeps the trained artifacts repo-canonical
    by construction.
    '''
    normalized = []
    for phone in phones:
        phone = phone_inventory.canonical_label(
            CELEX_TO_IPA.get(phone, phone))
        if phone not in phone_inventory.KNOWN_PHONES: return None
        normalized.append(phone)
    return normalized


def syllable_groups(phones, labels):
    '''Group phones into syllables according to the boundary labels.'''
    groups, current = [], []
    for index, phone in enumerate(phones):
        current.append(phone)
        if index < len(labels) and labels[index]:
            groups.append(current)
            current = []
    groups.append(current)
    return groups


def _one_nucleus_per_syllable(phones, labels):
    '''True when every syllable has exactly one nucleus.'''
    for group in syllable_groups(phones, labels):
        nuclei = [p for p in group if phonotactics.is_nucleus(p)]
        if len(nuclei) != 1: return False
    return True


def load_examples(language='dutch', verbose=True):
    '''Load normalized (phones, labels, key) examples from CELEX.
    language                celex language to load (default dutch)
    verbose                 print how many entries were skipped

    Skips multiword entries, words with an unmappable phone and words
    where a syllable does not have exactly one nucleus.
    '''
    examples = []
    skipped_phone, skipped_nucleus = 0, 0
    for phones, labels, word in training_examples(language):
        normalized = normalize_phones(phones)
        if normalized is None:
            skipped_phone += 1
            continue
        if not _one_nucleus_per_syllable(normalized, labels):
            skipped_nucleus += 1
            continue
        examples.append((normalized, labels, _lemma_key(word)))
    if verbose:
        m = f'loaded {len(examples)} examples'
        m += f', skipped {skipped_phone} with unmappable phones'
        m += f' and {skipped_nucleus} without one nucleus per syllable'
        print(m)
    return examples


def _lemma_key(word):
    '''Group key for a word: the lemma id, else the word id.'''
    if word.id_number_lemma and word.id_number_lemma > 0:
        return f'l{word.id_number_lemma}'
    return f'w{word.id_number}'


def split_examples(examples, dev_share=1, test_share=1, out_of=10):
    '''Deterministic lemma disjoint train/dev/test split.
    examples                list of (phones, labels, key)
    dev_share, test_share   buckets (of out_of) for dev and test
    out_of                  total number of hash buckets

    All examples sharing a key land in the same part, so inflectional
    families never straddle a split. Returns (train, dev, test).
    '''
    train, dev, test = [], [], []
    for example in examples:
        key = example[2]
        digest = hashlib.md5(key.encode('utf-8')).hexdigest()
        bucket = int(digest, 16) % out_of
        if bucket < test_share: test.append(example)
        elif bucket < test_share + dev_share: dev.append(example)
        else: train.append(example)
    return train, dev, test
