# coding: utf-8

from parsel import Selector
from parsel.xpathfuncs import set_xpathfunc
import unittest


class XPathFuncsTestCase(unittest.TestCase):
    def test_has_class_simple(self):
        body = u"""
        <p class="foo bar-baz">First</p>
        <p class="foo">Second</p>
        <p class="bar">Third</p>
        <p>Fourth</p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo")]/text()')],
            [u'First', u'Second'])
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("bar")]/text()')],
            [u'Third'])
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo","bar")]/text()')],
            [])
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo","bar-baz")]/text()')],
            [u'First'])

    def test_has_class_error_no_args(self):
        body = u"""
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegexp(
            ValueError, 'has-class must have at least 1 argument',
            sel.xpath, 'has-class()')

    def test_has_class_error_invalid_arg_type(self):
        body = u"""
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegexp(
            ValueError, 'has-class arguments must be strings',
            sel.xpath, 'has-class(.)')

    def test_has_class_error_invalid_unicode(self):
        body = u"""
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegexp(
            ValueError, 'All strings must be XML compatible',
            sel.xpath, u'has-class("héllö")'.encode('utf-8'))

    def test_has_class_unicode(self):
        body = u"""
        <p CLASS="fóó">First</p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath(u'//p[has-class("fóó")]/text()')],
            [u'First'])

    def test_has_class_uppercase(self):
        body = u"""
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo")]/text()')],
            [u'First'])

    def test_set_xpathfunc(self):

        def myfunc(ctx):
            myfunc.call_count += 1

        myfunc.call_count = 0

        body = u"""
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegexp(
            ValueError, 'Unregistered function in myfunc',
            sel.xpath, 'myfunc()')

        set_xpathfunc('myfunc', myfunc)
        sel.xpath('myfunc()')
        self.assertEqual(myfunc.call_count, 1)

        set_xpathfunc('myfunc', None)
        self.assertRaisesRegexp(
            ValueError, 'Unregistered function in myfunc',
            sel.xpath, 'myfunc()')

    def test_rel_id_basic(self):
        body = u"""
        <foo><p id="foop">Foo</p></foo>
        <bar><p id="barp">Bar</p></p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('rel-id("foop")/text()')],
            [u'Foo'],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('rel-id("foop", .)/text()')],
            [u'Foo'],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('rel-id("foop", //foo)/text()')],
            [u'Foo'],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('rel-id("foop", //p)/text()')],
            [u'Foo'],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('rel-id("foop", //bar)/text()')],
            [],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('//foo').xpath('rel-id("foop")/text()')],
            [u'Foo'],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('//bar').xpath('rel-id("foop")/text()')],
            [],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('rel-id("barp", //bar)/text()')],
            [u'Bar'],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('rel-id("foop", //zzz)/text()')],
            [],
        )

    def test_rel_id_in_conditional(self):
        body = u"""
        <p><p id="foop">Foo</p></foo>
        <p><p id="barp">Bar</p></p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[rel-id("foop")]//text()')],
            [u'Foo'],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[rel-id("barp")]//text()')],
            [u'Bar'],
        )

    def test_rel_id_error_invalid_id(self):
        body = u"""
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegexp(
            ValueError, 'rel-id: first argument must be a string',
            sel.xpath, u'rel-id(123)')

    def test_rel_id_error_invalid_nodeset(self):
        body = u"""
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegexp(
            ValueError, 'rel-id: second argument must be a nodeset',
            sel.xpath, u'rel-id("123", true())')
