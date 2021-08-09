"""Tests for known XML attacks"""

from os import path
from unittest import TestCase

from psutil import Process

from parsel import Selector


MiB_1 = 1024 ** 2


def _load(attack):
    folder_path = path.dirname(__file__)
    file_path = path.join(folder_path, "xml_attacks", f"{attack}.xml")
    with open(file_path, "rb") as attack_file:
        return attack_file.read().decode("utf-8")


# List of known attacks:
# https://github.com/tiran/defusedxml#python-xml-libraries
class XMLAttackTestCase(TestCase):
    def test_billion_laughs(self):
        process = Process()
        memory_usage_before = process.memory_info().rss
        selector = Selector(text=_load("billion_laughs"))
        lolz = selector.css("lolz::text").get()
        memory_usage_after = process.memory_info().rss
        memory_change = memory_usage_after - memory_usage_before
        assert_message = f"Memory change: {memory_change}B"
        assert memory_change <= MiB_1, assert_message
        assert lolz == "&lol9;"
