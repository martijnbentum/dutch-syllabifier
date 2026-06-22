class Phone:
    '''A single IPA phone.

    A user may supply their own phone object instead of this one. The only
    requirement is that it exposes a ``.label`` attribute holding the IPA
    symbol.
    '''

    def __init__(self, label):
        '''Create a phone.
        label                   IPA symbol, e.g. 'm' or 'ɛi'
        '''
        self.label = label

    def __repr__(self):
        return f'Phone({self.label!r})'

    def __eq__(self, other):
        return label_of(self) == label_of(other)

    def __hash__(self):
        return hash(self.label)


def label_of(phone):
    '''Return the IPA label of a phone.
    phone                   IPA string or an object with a ``.label`` attribute
    '''
    if isinstance(phone, str):
        return phone
    if hasattr(phone, 'label'):
        return phone.label
    raise TypeError(
        f'phone {phone!r} is not a string and has no .label attribute')


def labels_of(phones):
    '''Return the list of IPA labels for a list of phones.
    phones                  list of IPA strings or objects with ``.label``
    '''
    return [label_of(p) for p in phones]
