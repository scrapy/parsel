# -*- coding:utf-8 -*-


from unittest import TestCase
from warnings import catch_warnings

from parsel.selector import create_root_node, SafeXMLParser
from lxml.html import HTMLParser


class TestDeprecations(TestCase):

    def test_create_root_node(self):
        with catch_warnings(record=True) as warnings:
            create_root_node(u'…', HTMLParser)
            self.assertEqual(len(warnings), 1)

    def test_SafeXMLParser(self):
        with catch_warnings(record=True) as warnings:
            parser = SafeXMLParser()
            self.assertEqual(len(warnings), 1)
