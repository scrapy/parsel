from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from parsel.utils import extract_regex, shorten

if TYPE_CHECKING:
    from re import Pattern


@pytest.mark.parametrize(
    ("width", "expected"),
    [
        (-1, ValueError),
        (0, ""),
        (1, "."),
        (2, ".."),
        (3, "..."),
        (4, "f..."),
        (5, "fo..."),
        (6, "foobar"),
        (7, "foobar"),
    ],
)
def test_shorten(width: int, expected: str | type[Exception]) -> None:
    if isinstance(expected, str):
        assert shorten("foobar", width) == expected
    else:
        with pytest.raises(expected):
            shorten("foobar", width)


@pytest.mark.parametrize(
    ("regex", "text", "replace_entities", "expected"),
    [
        (
            r"(?P<month>\w+)\s*(?P<day>\d+)\s*\,?\s*(?P<year>\d+)",
            "October  25, 2019",
            True,
            ["October", "25", "2019"],
        ),
        (
            r"(?P<month>\w+)\s*(?P<day>\d+)\s*\,?\s*(?P<year>\d+)",
            "October  25 2019",
            True,
            ["October", "25", "2019"],
        ),
        (
            r"(?P<extract>\w+)\s*(?P<day>\d+)\s*\,?\s*(?P<year>\d+)",
            "October  25 2019",
            True,
            ["October"],
        ),
        (
            r"\w+\s*\d+\s*\,?\s*\d+",
            "October  25 2019",
            True,
            ["October  25 2019"],
        ),
        (
            r"^.*$",
            "&quot;sometext&quot; &amp; &quot;moretext&quot;",
            True,
            ['"sometext" &amp; "moretext"'],
        ),
        (
            r"^.*$",
            "&quot;sometext&quot; &amp; &quot;moretext&quot;",
            False,
            ["&quot;sometext&quot; &amp; &quot;moretext&quot;"],
        ),
    ],
)
def test_extract_regex(
    regex: str | Pattern[str],
    text: str,
    replace_entities: bool,
    expected: list[str],
) -> None:
    assert extract_regex(regex, text, replace_entities) == expected
