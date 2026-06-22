import warnings

from . import data


class UnknownPhoneWarning(UserWarning):
    '''Warning for labels that are not in the known IPA phone inventory.'''


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
        warn_if_unknown_phone(label)

    def __repr__(self):
        return f'Phone({self.label!r})'

    def __eq__(self, other):
        return phone_to_label(self) == phone_to_label(other)

    def __hash__(self):
        return hash(self.label)


def phone_to_label(phone):
    '''Return the IPA label of a phone.
    phone                   IPA string or an object with a ``.label`` attribute
    '''
    if isinstance(phone, str):
        return phone
    if hasattr(phone, 'label'):
        return phone.label
    raise TypeError(
        f'phone {phone!r} is not a string and has no .label attribute')


def phones_to_label(phones):
    '''Return the list of IPA labels for a list of phones.
    phones                  list of IPA strings or objects with ``.label``
    '''
    return [phone_to_label(p) for p in phones]


def is_ipa_phone(label):
    '''Return True if the label is a known Dutch IPA phone.
    label                   IPA symbol string
    '''
    return label in data.KNOWN_PHONES


def warn_if_unknown_phone(label):
    '''Warn (do not raise) when a label is not a known IPA phone.
    label                   IPA symbol string
    '''
    if is_ipa_phone(label): return
    m = f'phone {label!r} is not in the known Dutch IPA phone inventory; '
    m += f'check the symbol (diphthongs are single phones such as '
    m += f"'ɛi', and /sx/ is two phones ['s', 'x'])"
    warnings.warn(m, UnknownPhoneWarning, stacklevel=2)
