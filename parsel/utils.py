import re
import six
from w3lib.html import replace_entities


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


def flatten(x, flatten_type=_is_listlike):
    """flatten(sequence) -> list
    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    ``flatten_type`` is a method that return true for the
    type of objects that have to be flattened
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
    >>> flatten([1, [2], [{"foo": "bar"}]], lambda y: isinstance(y, list))
    [1, 2, {'foo': 'bar'}]
    """
    return list(iflatten(x, flatten_type))


def iflatten(x, flatten_type=_is_listlike):
    """iflatten(sequence) -> iterator
    Similar to ``.flatten()``, but returns iterator instead
    ``flatten_type`` is a method that return true for the
    type of objects that have to be flattened
    """
    for el in x:
        if flatten_type(el):
            for el_ in flatten(el, flatten_type):
                yield el_
        else:
            yield el


def extract_regex(regex, text):
    """Extract a list of unicode strings from the given text/encoding using the following policies:
    * if the regex contains a named group called "extract" that will be returned
    * if the regex contains multiple numbered groups, all those will be returned (flattened)
    * if the regex doesn't contain any group the entire regex matching is returned
    """
    if isinstance(regex, six.string_types):
        regex = re.compile(regex, re.UNICODE)

    try:
        strings = [regex.search(text).group('extract')]   # named group
    except:
        strings = regex.findall(text)    # full regex or numbered groups
    return [replace_entities(s, keep=['lt', 'amp']) for s in flatten(strings)]
