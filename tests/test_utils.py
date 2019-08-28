from parsel.utils import shorten

from pytest import mark, raises
import six


@mark.parametrize(
    'width,expected',
    (
        (-1, ValueError),
        (0, u''),
        (1, u'.'),
        (2, u'..'),
        (3, u'...'),
        (4, u'f...'),
        (5, u'fo...'),
        (6, u'foobar'),
        (7, u'foobar'),
    )
)
def test_shorten(width, expected):
    if isinstance(expected, six.string_types):
        assert shorten(u'foobar', width) == expected
    else:
        with raises(expected):
            shorten(u'foobar', width)
