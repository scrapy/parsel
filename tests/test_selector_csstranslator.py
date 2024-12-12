"""
Selector tests for cssselect backend
"""

import unittest
from typing import Any, Callable, List, Protocol, Tuple, Type, Union

import cssselect
import pytest
from cssselect.parser import SelectorSyntaxError
from cssselect.xpath import ExpressionError
from packaging.version import Version

from parsel import Selector
from parsel.csstranslator import GenericTranslator, HTMLTranslator, TranslatorProtocol

HTMLBODY = """
<html>
<body>
<div>
 <a id="name-anchor" name="foo"></a>
 <a id="tag-anchor" rel="tag" href="http://localhost/foo">link</a>
 <a id="nofollow-anchor" rel="nofollow" href="https://example.org"> link</a>
 <p id="paragraph">
   lorem ipsum text
   <b id="p-b">hi</b> <em id="p-em">there</em>
   <b id="p-b2">guy</b>
   <input type="checkbox" id="checkbox-unchecked" />
   <input type="checkbox" id="checkbox-disabled" disabled="" />
   <input type="text" id="text-checked" checked="checked" />
   <input type="hidden" />
   <input type="hidden" disabled="disabled" />
   <input type="checkbox" id="checkbox-checked" checked="checked" />
   <input type="checkbox" id="checkbox-disabled-checked"
          disabled="disabled" checked="checked" />
   <fieldset id="fieldset" disabled="disabled">
     <input type="checkbox" id="checkbox-fieldset-disabled" />
     <input type="hidden" />
   </fieldset>
 </p>
 <map name="dummymap">
   <area shape="circle" coords="200,250,25" href="foo.html" id="area-href" />
   <area shape="default" id="area-nohref" />
 </map>
</div>
<div class="cool-footer" id="foobar-div" foobar="ab bc cde">
    <span id="foobar-span">foo ter</span>
</div>
</body></html>
"""


class TranslatorTestProtocol(Protocol):
    tr_cls: Type[TranslatorProtocol]
    tr: TranslatorProtocol

    def c2x(self, css: str, prefix: str = ...) -> str:
        pass

    def assertEqual(self, first: Any, second: Any, msg: Any = ...) -> None:
        pass

    def assertRaises(
        self,
        expected_exception: Union[Type[BaseException], Tuple[Type[BaseException], ...]],
        callable: Callable[..., object],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        pass


class TranslatorTestMixin:
    def setUp(self: TranslatorTestProtocol) -> None:
        self.tr = self.tr_cls()
        self.c2x = self.tr.css_to_xpath

    def test_attr_function(self: TranslatorTestProtocol) -> None:
        cases = [
            ("::attr(name)", "descendant-or-self::*/@name"),
            ("a::attr(href)", "descendant-or-self::a/@href"),
            (
                "a ::attr(img)",
                "descendant-or-self::a/descendant-or-self::*/@img",
            ),
            ("a > ::attr(class)", "descendant-or-self::a/*/@class"),
        ]
        for css, xpath in cases:
            self.assertEqual(self.c2x(css), xpath, css)

    def test_attr_function_exception(self: TranslatorTestProtocol) -> None:
        cases = [
            ("::attr(12)", ExpressionError),
            ("::attr(34test)", ExpressionError),
            ("::attr(@href)", SelectorSyntaxError),
        ]
        for css, exc in cases:
            self.assertRaises(exc, self.c2x, css)

    def test_text_pseudo_element(self: TranslatorTestProtocol) -> None:
        cases = [
            ("::text", "descendant-or-self::text()"),
            ("p::text", "descendant-or-self::p/text()"),
            ("p ::text", "descendant-or-self::p/descendant-or-self::text()"),
            ("#id::text", "descendant-or-self::*[@id = 'id']/text()"),
            ("p#id::text", "descendant-or-self::p[@id = 'id']/text()"),
            (
                "p#id ::text",
                "descendant-or-self::p[@id = 'id']/descendant-or-self::text()",
            ),
            ("p#id > ::text", "descendant-or-self::p[@id = 'id']/*/text()"),
            (
                "p#id ~ ::text",
                "descendant-or-self::p[@id = 'id']/following-sibling::*/text()",
            ),
            ("a[href]::text", "descendant-or-self::a[@href]/text()"),
            (
                "a[href] ::text",
                "descendant-or-self::a[@href]/descendant-or-self::text()",
            ),
            (
                "p::text, a::text",
                "descendant-or-self::p/text() | descendant-or-self::a/text()",
            ),
        ]
        for css, xpath in cases:
            self.assertEqual(self.c2x(css), xpath, css)

    def test_pseudo_function_exception(self: TranslatorTestProtocol) -> None:
        cases = [
            ("::attribute(12)", ExpressionError),
            ("::text()", ExpressionError),
            ("::attr(@href)", SelectorSyntaxError),
        ]
        for css, exc in cases:
            self.assertRaises(exc, self.c2x, css)

    def test_unknown_pseudo_element(self: TranslatorTestProtocol) -> None:
        cases = [
            ("::text-node", ExpressionError),
        ]
        for css, exc in cases:
            self.assertRaises(exc, self.c2x, css)

    def test_unknown_pseudo_class(self: TranslatorTestProtocol) -> None:
        cases = [
            (":text", ExpressionError),
            (":attribute(name)", ExpressionError),
        ]
        for css, exc in cases:
            self.assertRaises(exc, self.c2x, css)


class HTMLTranslatorTest(TranslatorTestMixin, unittest.TestCase):
    tr_cls = HTMLTranslator


class GenericTranslatorTest(TranslatorTestMixin, unittest.TestCase):
    tr_cls = GenericTranslator


class UtilCss2XPathTest(unittest.TestCase):
    def test_css2xpath(self) -> None:
        from parsel import css2xpath

        expected_xpath = (
            "descendant-or-self::*[@class and contains("
            "concat(' ', normalize-space(@class), ' '), ' some-class ')]"
        )
        self.assertEqual(css2xpath(".some-class"), expected_xpath)


class CSSSelectorTest(unittest.TestCase):

    sscls = Selector

    def setUp(self) -> None:
        self.sel = self.sscls(text=HTMLBODY)

    def x(self, *a: Any, **kw: Any) -> List[str]:
        return [v.strip() for v in self.sel.css(*a, **kw).extract() if v.strip()]

    def test_selector_simple(self) -> None:
        for x in self.sel.css("input"):
            self.assertTrue(isinstance(x, self.sel.__class__), x)
        self.assertEqual(
            self.sel.css("input").extract(),
            [x.extract() for x in self.sel.css("input")],
        )

    def test_text_pseudo_element(self) -> None:
        self.assertEqual(self.x("#p-b2"), ['<b id="p-b2">guy</b>'])
        self.assertEqual(self.x("#p-b2::text"), ["guy"])
        self.assertEqual(self.x("#p-b2 ::text"), ["guy"])
        self.assertEqual(self.x("#paragraph::text"), ["lorem ipsum text"])
        self.assertEqual(
            self.x("#paragraph ::text"),
            ["lorem ipsum text", "hi", "there", "guy"],
        )
        self.assertEqual(self.x("p::text"), ["lorem ipsum text"])
        self.assertEqual(self.x("p ::text"), ["lorem ipsum text", "hi", "there", "guy"])

    def test_attribute_function(self) -> None:
        self.assertEqual(self.x("#p-b2::attr(id)"), ["p-b2"])
        self.assertEqual(self.x(".cool-footer::attr(class)"), ["cool-footer"])
        self.assertEqual(
            self.x(".cool-footer ::attr(id)"), ["foobar-div", "foobar-span"]
        )
        self.assertEqual(
            self.x('map[name="dummymap"] ::attr(shape)'), ["circle", "default"]
        )

    def test_nested_selector(self) -> None:
        self.assertEqual(self.sel.css("p").css("b::text").extract(), ["hi", "guy"])
        self.assertEqual(
            self.sel.css("div").css("area:last-child").extract(),
            ['<area shape="default" id="area-nohref">'],
        )

    @pytest.mark.xfail(
        Version(cssselect.__version__) < Version("1.2.0"),
        reason="Support added in cssselect 1.2.0",
    )
    def test_pseudoclass_has(self) -> None:
        self.assertEqual(self.x("p:has(b)::text"), ["lorem ipsum text"])


class CSSSelectorTestBytes(CSSSelectorTest):
    def setUp(self) -> None:
        self.sel = self.sscls(body=bytes(HTMLBODY, encoding="utf-8"))
