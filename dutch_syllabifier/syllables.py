from .phones import labels_of


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

    @property
    def label(self):
        '''Return the phones as a space-separated IPA string.'''
        return ' '.join(labels_of(self.phones))

    def __repr__(self):
        return f'Syllable({labels_of(self.phones)!r})'

    def __eq__(self, other):
        if not hasattr(other, 'phones'):
            return NotImplemented
        return labels_of(self.phones) == labels_of(other.phones)
