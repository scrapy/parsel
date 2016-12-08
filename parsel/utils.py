import re
import six
from w3lib.html import replace_entities


def flatten(x):
    """flatten(sequence) -> list
    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).
    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]
    >>> flatten(["foo", "bar"])
    ['foo', 'bar']
    >>> flatten(["foo", ["baz", 42], "bar"])
    ['foo', 'baz', 42, 'bar']
    """
    return list(iflatten(x))


def iflatten(x):
    """iflatten(sequence) -> iterator
    Similar to ``.flatten()``, but returns iterator instead"""
    for el in x:
        if _is_listlike(el):
            for el_ in flatten(el):
                yield el_
        else:
            yield el


def _is_listlike(x):
    """
    >>> _is_listlike("foo")
    False
    >>> _is_listlike(5)
    False
    >>> _is_listlike(b"foo")
    False
    >>> _is_listlike([b"foo"])
    True
    >>> _is_listlike((b"foo",))
    True
    >>> _is_listlike({})
    True
    >>> _is_listlike(set())
    True
    >>> _is_listlike((x for x in range(3)))
    True
    >>> _is_listlike(six.moves.xrange(5))
    True
    """
    return hasattr(x, "__iter__") and not isinstance(x, (six.text_type, bytes))

def extract_regex_first(regex, text):
    """Extract the first match of unicode strings from the given text/encoding using the following policies:
    * if the regex contains a named group called "extract" that will be returned
    * if the regex contains multiple numbered groups, all those will be returned (flattened)
    * if the regex doesn't contain any group the entire regex matching is returned
    """
    if isinstance(regex, six.string_types):
        regex = re.compile(regex, re.UNICODE)

    m = regex.search(text) # looks for the first location

    if not m:
        return []
        
    if 'extract' in regex.groupindex:
        return _replace_entities(m.group('extract'))
    
    # full regex or numbered groups
    return [_replace_entities(group) for group in m.groups()]

def _replace_entities(text):
    return replace_entities(text, keep=['lt', 'amp'])

def extract_regex(regex, text):
    """Extract a list of unicode strings from the given text/encoding using the following policies:
    * if the regex contains a named group called "extract" that will be returned
    * if the regex contains multiple numbered groups, all those will be returned (flattened)
    * if the regex doesn't contain any group the entire regex matching is returned
    """
    if isinstance(regex, six.string_types):
        regex = re.compile(regex, re.UNICODE)

    if 'extract' in regex.groupindex: # named group
        m = regex.search(text)
        if not m:
            return []
        return [_replace_entities(m.group('extract'))]
    
    # full regex or numbered groups
    strings = flatten(regex.findall(text))
    return [_replace_entities(s) for s in strings]
    