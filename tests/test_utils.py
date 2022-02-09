from parsel.utils import shorten, extract_regex

from pytest import mark, raises


@mark.parametrize(
    "width,expected",
    (
        (-1, ValueError),
        (0, ""),
        (1, "."),
        (2, ".."),
        (3, "..."),
        (4, "f..."),
        (5, "fo..."),
        (6, "foobar"),
        (7, "foobar"),
    ),
)
def test_shorten(width, expected):
    if isinstance(expected, str):
        assert shorten("foobar", width) == expected
    else:
        with raises(expected):
            shorten("foobar", width)


@mark.parametrize(
    "regex, text, replace_entities, expected",
    (
        [
            r"(?P<month>\w+)\s*(?P<day>\d+)\s*\,?\s*(?P<year>\d+)",
            "October  25, 2019",
            True,
            ["October", "25", "2019"],
        ],
        [
            r"(?P<month>\w+)\s*(?P<day>\d+)\s*\,?\s*(?P<year>\d+)",
            "October  25 2019",
            True,
            ["October", "25", "2019"],
        ],
        [
            r"(?P<extract>\w+)\s*(?P<day>\d+)\s*\,?\s*(?P<year>\d+)",
            "October  25 2019",
            True,
            ["October"],
        ],
        [r"\w+\s*\d+\s*\,?\s*\d+", "October  25 2019", True, ["October  25 2019"]],
        [
            r"^.*$",
            "&quot;sometext&quot; &amp; &quot;moretext&quot;",
            True,
            ['"sometext" &amp; "moretext"'],
        ],
        [
            r"^.*$",
            "&quot;sometext&quot; &amp; &quot;moretext&quot;",
            False,
            ["&quot;sometext&quot; &amp; &quot;moretext&quot;"],
        ],
    ),
)
def test_extract_regex(regex, text, replace_entities, expected):
    assert extract_regex(regex, text, replace_entities) == expected
