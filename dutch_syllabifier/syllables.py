from .phones import phones_to_label


class Syllable:
    '''A single syllable, holding an ordered list of phones.

    A user may supply their own syllable object instead of this one. The only
    requirement is that it exposes a ``.phones`` attribute with a list of
    phones, where each phone is an IPA string or an object with a ``.label``
    attribute.
    '''

    def __init__(self, phones):
        '''Create a syllable.
        phones                  list of IPA strings or objects with ``.label``
        '''
        self.phones = phones
        self.legality = None        # set by check_syllabification; None if unjudged

    @property
    def label(self):
        '''Return the phones as a space-separated IPA string.'''
        return ' '.join(phones_to_label(self.phones))

    def __repr__(self):
        return f'Syllable({phones_to_label(self.phones)!r})'

    def __eq__(self, other):
        if not hasattr(other, 'phones'):
            return NotImplemented
        return phones_to_label(self.phones) == phones_to_label(other.phones)

    # phones is a mutable list and legality is assigned after construction,
    # so Syllable is deliberately unhashable; Phone is immutable and hashable
    __hash__ = None
