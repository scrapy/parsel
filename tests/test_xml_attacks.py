"""Tests for known XML attacks"""

from pathlib import Path

import pytest
from psutil import Process

from parsel import Selector

MiB_1 = 1024**2


def _load(attack: str) -> str:
    folder_path = Path(__file__).parent
    file_path = folder_path / "xml_attacks" / f"{attack}.xml"
    return file_path.read_bytes().decode("utf-8")


# List of known attacks:
# https://github.com/tiran/defusedxml#python-xml-libraries
@pytest.mark.parametrize(
    ("type_", "lolz"),
    [
        # The XML parser does not resolve entities, so the reference is dropped.
        ("xml", None),
        # The HTML parser keeps the unresolved reference as text.
        ("html", "&lol9;"),
    ],
)
def test_billion_laughs(type_: str, lolz: str | None) -> None:
    process = Process()
    memory_usage_before = process.memory_info().rss
    selector = Selector(text=_load("billion_laughs"), type=type_)
    actual_lolz = selector.css("lolz::text").get()
    memory_usage_after = process.memory_info().rss
    memory_change = memory_usage_after - memory_usage_before
    assert_message = f"Memory change: {memory_change}B"
    assert memory_change <= MiB_1, assert_message
    assert actual_lolz == lolz
