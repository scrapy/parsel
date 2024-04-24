import unittest
from typing import Any

from parsel import Selector
from parsel.xpathfuncs import set_xpathfunc


class XPathFuncsTestCase(unittest.TestCase):
    def test_has_class_simple(self) -> None:
        body = """
        <p class="foo bar-baz">First</p>
        <p class="foo">Second</p>
        <p class="bar">Third</p>
        <p>Fourth</p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo")]/text()')],
            ["First", "Second"],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("bar")]/text()')],
            ["Third"],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo","bar")]/text()')],
            [],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo","bar-baz")]/text()')],
            ["First"],
        )

    def test_has_class_error_no_args(self) -> None:
        body = """
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegex(
            ValueError,
            "has-class must have at least 1 argument",
            sel.xpath,
            "has-class()",
        )

    def test_has_class_error_invalid_arg_type(self) -> None:
        body = """
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegex(
            ValueError,
            "has-class arguments must be strings",
            sel.xpath,
            "has-class(.)",
        )

    def test_has_class_error_invalid_unicode(self) -> None:
        body = """
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegex(
            ValueError,
            "All strings must be XML compatible",
            sel.xpath,
            'has-class("héllö")'.encode(),
        )

    def test_has_class_unicode(self) -> None:
        body = """
        <p CLASS="fóó">First</p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("fóó")]/text()')],
            ["First"],
        )

    def test_has_class_uppercase(self) -> None:
        body = """
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo")]/text()')],
            ["First"],
        )

    def test_has_class_newline(self) -> None:
        body = """
        <p CLASS="foo
        bar">First</p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo")]/text()')],
            ["First"],
        )

    def test_has_class_tab(self) -> None:
        body = """
        <p CLASS="foo\tbar">First</p>
        """
        sel = Selector(text=body)
        self.assertEqual(
            [x.extract() for x in sel.xpath('//p[has-class("foo")]/text()')],
            ["First"],
        )

    def test_set_xpathfunc(self) -> None:
        def myfunc(ctx: Any) -> None:
            myfunc.call_count += 1  # type: ignore[attr-defined]

        myfunc.call_count = 0  # type: ignore[attr-defined]

        body = """
        <p CLASS="foo">First</p>
        """
        sel = Selector(text=body)
        self.assertRaisesRegex(
            ValueError,
            "Unregistered function in myfunc",
            sel.xpath,
            "myfunc()",
        )

        set_xpathfunc("myfunc", myfunc)
        sel.xpath("myfunc()")
        self.assertEqual(myfunc.call_count, 1)  # type: ignore[attr-defined]

        set_xpathfunc("myfunc", None)
        self.assertRaisesRegex(
            ValueError,
            "Unregistered function in myfunc",
            sel.xpath,
            "myfunc()",
        )
