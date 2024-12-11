import pickle
import re
import typing
import unittest
import warnings
import weakref
from typing import Any, Mapping, Optional, cast

from lxml import etree
from lxml.html import HtmlElement
from packaging.version import Version

from parsel import Selector, SelectorList
from parsel.selector import (
    _NOT_SET,
    LXML_SUPPORTS_HUGE_TREE,
    CannotRemoveElementWithoutParent,
    CannotRemoveElementWithoutRoot,
)


class SelectorTestCase(unittest.TestCase):

    sscls = Selector

    def assertIsSelector(self, value: Any) -> None:
        self.assertEqual(type(value), type(self.sscls(text="")))

    def assertIsSelectorList(self, value: Any) -> None:
        self.assertEqual(type(value), type(self.sscls.selectorlist_cls()))

    def test_pickle_selector(self) -> None:
        sel = self.sscls(text="<html><body><p>some text</p></body></html>")
        self.assertRaises(TypeError, lambda s: pickle.dumps(s, protocol=2), sel)

    def test_pickle_selector_list(self) -> None:
        sel = self.sscls(
            text="<html><body><ul><li>1</li><li>2</li><li>3</li></ul></body></html>"
        )
        sel_list = sel.css("li")
        empty_sel_list = sel.css("p")
        self.assertIsSelectorList(sel_list)
        self.assertIsSelectorList(empty_sel_list)
        self.assertRaises(TypeError, lambda s: pickle.dumps(s, protocol=2), sel_list)
        self.assertRaises(
            TypeError, lambda s: pickle.dumps(s, protocol=2), empty_sel_list
        )

    def test_simple_selection(self) -> None:
        """Simple selector tests"""
        body = "<p><input name='a'value='1'/><input name='b'value='2'/></p>"
        sel = self.sscls(text=body)

        xl = sel.xpath("//input")
        self.assertEqual(2, len(xl))
        for x in xl:
            self.assertIsSelector(x)

        self.assertEqual(
            sel.xpath("//input").extract(),
            [x.extract() for x in sel.xpath("//input")],
        )

        self.assertEqual(
            [x.extract() for x in sel.xpath("//input[@name='a']/@name")],
            ["a"],
        )
        self.assertEqual(
            [
                x.extract()
                for x in sel.xpath(
                    "number(concat(//input[@name='a']/@value, //input[@name='b']/@value))"
                )
            ],
            ["12.0"],
        )

        self.assertEqual(
            sel.xpath("concat('xpath', 'rules')").extract(), ["xpathrules"]
        )
        self.assertEqual(
            [
                x.extract()
                for x in sel.xpath(
                    "concat(//input[@name='a']/@value, //input[@name='b']/@value)"
                )
            ],
            ["12"],
        )

    def test_simple_selection_with_variables(self) -> None:
        """Using XPath variables"""
        body = "<p><input name='a' value='1'/><input name='b' value='2'/></p>"
        sel = self.sscls(text=body)

        self.assertEqual(
            [x.extract() for x in sel.xpath("//input[@value=$number]/@name", number=1)],
            ["a"],
        )
        self.assertEqual(
            [
                x.extract()
                for x in sel.xpath("//input[@name=$letter]/@value", letter="b")
            ],
            ["2"],
        )

        self.assertEqual(
            sel.xpath(
                "count(//input[@value=$number or @name=$letter])",
                number=2,
                letter="a",
            ).extract(),
            ["2.0"],
        )

        # you can also pass booleans
        self.assertEqual(
            sel.xpath("boolean(count(//input)=$cnt)=$test", cnt=2, test=True).extract(),
            ["1"],
        )
        self.assertEqual(
            sel.xpath("boolean(count(//input)=$cnt)=$test", cnt=4, test=True).extract(),
            ["0"],
        )
        self.assertEqual(
            sel.xpath(
                "boolean(count(//input)=$cnt)=$test", cnt=4, test=False
            ).extract(),
            ["1"],
        )

        # for named nodes, you need to use "name()=node_name"
        self.assertEqual(
            sel.xpath(
                "boolean(count(//*[name()=$tag])=$cnt)=$test",
                tag="input",
                cnt=2,
                test=True,
            ).extract(),
            ["1"],
        )

    def test_simple_selection_with_variables_escape_friendly(self) -> None:
        """Using XPath variables with quotes that would need escaping with string formatting"""
        body = """<p>I'm mixing single and <input name='a' value='I say "Yeah!"'/>
        "double quotes" and I don't care :)</p>"""
        sel = self.sscls(text=body)

        t = 'I say "Yeah!"'
        # naive string formatting with give something like:
        # ValueError: XPath error: Invalid predicate in //input[@value="I say "Yeah!""]/@name
        self.assertRaises(ValueError, sel.xpath, f'//input[@value="{t}"]/@name')

        # with XPath variables, escaping is done for you
        self.assertEqual(
            [x.extract() for x in sel.xpath("//input[@value=$text]/@name", text=t)],
            ["a"],
        )
        lt = """I'm mixing single and "double quotes" and I don't care :)"""
        # the following gives you something like
        # ValueError: XPath error: Invalid predicate in //p[normalize-space()='I'm mixing single and "double quotes" and I don't care :)']//@name
        self.assertRaises(
            ValueError, sel.xpath, f"//p[normalize-space()='{lt}']//@name"
        )

        self.assertEqual(
            [
                x.extract()
                for x in sel.xpath("//p[normalize-space()=$lng]//@name", lng=lt)
            ],
            ["a"],
        )

    def test_accessing_attributes(self) -> None:
        body = """
<html lang="en" version="1.0">
    <body>
        <ul id="some-list" class="list-cls" class="list-cls">
            <li class="item-cls" id="list-item-1">
            <li class="item-cls active" id="list-item-2">
            <li class="item-cls" id="list-item-3">
        </ul>
    </body>
</html>
        """
        sel = self.sscls(text=body)
        self.assertEqual({"lang": "en", "version": "1.0"}, sel.attrib)
        self.assertEqual(
            {"id": "some-list", "class": "list-cls"}, sel.css("ul")[0].attrib
        )

        # for a SelectorList, bring the attributes of first-element only
        self.assertEqual({"id": "some-list", "class": "list-cls"}, sel.css("ul").attrib)
        self.assertEqual(
            {"class": "item-cls", "id": "list-item-1"}, sel.css("li").attrib
        )
        self.assertEqual({}, sel.css("body").attrib)
        self.assertEqual({}, sel.css("non-existing-element").attrib)

        self.assertEqual(
            [
                {"class": "item-cls", "id": "list-item-1"},
                {"class": "item-cls active", "id": "list-item-2"},
                {"class": "item-cls", "id": "list-item-3"},
            ],
            [e.attrib for e in sel.css("li")],
        )

    def test_representation_slice(self) -> None:
        body = f"<p><input name='{50 * 'b'}' value='\xa9'/></p>"
        sel = self.sscls(text=body)

        representation = f"<Selector query='//input/@name' data='{37 * 'b'}...'>"

        self.assertEqual(
            [repr(it) for it in sel.xpath("//input/@name")], [representation]
        )

    def test_representation_unicode_query(self) -> None:
        body = f"<p><input name='{50 * 'b'}' value='\xa9'/></p>"

        representation = "<Selector query='//input[@value=\"©\"]/@value' data='©'>"

        sel = self.sscls(text=body)
        self.assertEqual(
            [repr(it) for it in sel.xpath('//input[@value="\xa9"]/@value')],
            [representation],
        )

    def test_check_text_argument_type(self) -> None:
        self.assertRaisesRegex(
            TypeError,
            "text argument should be of type",
            self.sscls,
            b"<html/>",
        )

    def test_extract_first(self) -> None:
        """Test if extract_first() returns first element"""
        body = '<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(
            sel.xpath("//ul/li/text()").extract_first(),
            sel.xpath("//ul/li/text()").extract()[0],
        )

        self.assertEqual(
            sel.xpath('//ul/li[@id="1"]/text()').extract_first(),
            sel.xpath('//ul/li[@id="1"]/text()').extract()[0],
        )

        self.assertEqual(
            sel.xpath("//ul/li[2]/text()").extract_first(),
            sel.xpath("//ul/li/text()").extract()[1],
        )

        self.assertEqual(
            sel.xpath('/ul/li[@id="doesnt-exist"]/text()').extract_first(),
            None,
        )

    def test_extract_first_default(self) -> None:
        """Test if extract_first() returns default value when no results found"""
        body = '<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(
            sel.xpath("//div/text()").extract_first(default="missing"),
            "missing",
        )

    def test_selector_get_alias(self) -> None:
        """Test if get() returns extracted value on a Selector"""
        body = '<ul><li id="1">1</li><li id="2">2</li><li id="3">3</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(
            sel.xpath("//ul/li[position()>1]")[0].get(), '<li id="2">2</li>'
        )
        self.assertEqual(sel.xpath("//ul/li[position()>1]/text()")[0].get(), "2")

    def test_selector_getall_alias(self) -> None:
        """Test if get() returns extracted value on a Selector"""
        body = '<ul><li id="1">1</li><li id="2">2</li><li id="3">3</li></ul>'
        sel = self.sscls(text=body)

        self.assertListEqual(
            sel.xpath("//ul/li[position()>1]")[0].getall(),
            ['<li id="2">2</li>'],
        )
        self.assertListEqual(
            sel.xpath("//ul/li[position()>1]/text()")[0].getall(), ["2"]
        )

    def test_selectorlist_get_alias(self) -> None:
        """Test if get() returns first element for a selection call"""
        body = '<ul><li id="1">1</li><li id="2">2</li><li id="3">3</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(sel.xpath("//ul/li").get(), '<li id="1">1</li>')
        self.assertEqual(sel.xpath("//ul/li/text()").get(), "1")

    def test_re_first(self) -> None:
        """Test if re_first() returns first matched element"""
        body = '<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(
            sel.xpath("//ul/li/text()").re_first(r"\d"),
            sel.xpath("//ul/li/text()").re(r"\d")[0],
        )

        self.assertEqual(
            sel.xpath('//ul/li[@id="1"]/text()').re_first(r"\d"),
            sel.xpath('//ul/li[@id="1"]/text()').re(r"\d")[0],
        )

        self.assertEqual(
            sel.xpath("//ul/li[2]/text()").re_first(r"\d"),
            sel.xpath("//ul/li/text()").re(r"\d")[1],
        )

        self.assertEqual(sel.xpath("/ul/li/text()").re_first(r"\w+"), None)
        self.assertEqual(
            sel.xpath('/ul/li[@id="doesnt-exist"]/text()').re_first(r"\d"),
            None,
        )

        self.assertEqual(sel.re_first(r'id="(\d+)'), "1")
        self.assertEqual(sel.re_first(r"foo"), None)
        self.assertEqual(sel.re_first(r"foo", default="bar"), "bar")

    def test_extract_first_re_default(self) -> None:
        """Test if re_first() returns default value when no results found"""
        body = '<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(
            sel.xpath("//div/text()").re_first(r"\w+", default="missing"),
            "missing",
        )
        self.assertEqual(
            sel.xpath("/ul/li/text()").re_first(r"\w+", default="missing"),
            "missing",
        )

    def test_select_unicode_query(self) -> None:
        body = "<p><input name='\xa9' value='1'/></p>"
        sel = self.sscls(text=body)
        self.assertEqual(sel.xpath('//input[@name="\xa9"]/@value').extract(), ["1"])

    def test_list_elements_type(self) -> None:
        """Test Selector returning the same type in selection methods"""
        text = "<p>test<p>"
        self.assertEqual(
            type(self.sscls(text=text).xpath("//p")[0]),
            type(self.sscls(text=text)),
        )
        self.assertEqual(
            type(self.sscls(text=text).css("p")[0]),
            type(self.sscls(text=text)),
        )

    def test_boolean_result(self) -> None:
        body = "<p><input name='a'value='1'/><input name='b'value='2'/></p>"
        xs = self.sscls(text=body)
        self.assertEqual(xs.xpath("//input[@name='a']/@name='a'").extract(), ["1"])
        self.assertEqual(xs.xpath("//input[@name='a']/@name='n'").extract(), ["0"])

    def test_differences_parsing_xml_vs_html(self) -> None:
        """Test that XML and HTML Selector's behave differently"""
        # some text which is parsed differently by XML and HTML flavors
        text = '<div><img src="a.jpg"><p>Hello</div>'
        hs = self.sscls(text=text, type="html")
        self.assertEqual(
            hs.xpath("//div").extract(),
            ['<div><img src="a.jpg"><p>Hello</p></div>'],
        )

        xs = self.sscls(text=text, type="xml")
        self.assertEqual(
            xs.xpath("//div").extract(),
            ['<div><img src="a.jpg"><p>Hello</p></img></div>'],
        )

    def test_error_for_unknown_selector_type(self) -> None:
        self.assertRaises(ValueError, self.sscls, text="", type="_na_")

    def test_text_or_root_is_required(self) -> None:
        self.assertRaisesRegex(
            ValueError,
            "Selector needs text, body, or root arguments",
            self.sscls,
        )

    def test_bool(self) -> None:
        text = '<a href="" >false</a><a href="nonempty">true</a>'
        hs = self.sscls(text=text, type="html")
        falsish = hs.xpath("//a/@href")[0]
        self.assertEqual(falsish.extract(), "")
        self.assertFalse(falsish)
        trueish = hs.xpath("//a/@href")[1]
        self.assertEqual(trueish.extract(), "nonempty")
        self.assertTrue(trueish)

    def test_slicing(self) -> None:
        text = "<div><p>1</p><p>2</p><p>3</p></div>"
        hs = self.sscls(text=text, type="html")
        self.assertIsSelector(hs.css("p")[2])
        self.assertIsSelectorList(hs.css("p")[2:3])
        self.assertIsSelectorList(hs.css("p")[:2])
        self.assertEqual(hs.css("p")[2:3].extract(), ["<p>3</p>"])
        self.assertEqual(hs.css("p")[1:3].extract(), ["<p>2</p>", "<p>3</p>"])

    def test_nested_selectors(self) -> None:
        """Nested selector tests"""
        body = """<body>
                    <div class='one'>
                      <ul>
                        <li>one</li><li>two</li>
                      </ul>
                    </div>
                    <div class='two'>
                      <ul>
                        <li>four</li><li>five</li><li>six</li>
                      </ul>
                    </div>
                  </body>"""

        x = self.sscls(text=body)
        divtwo = x.xpath('//div[@class="two"]')
        self.assertEqual(
            divtwo.xpath("//li").extract(),
            [
                "<li>one</li>",
                "<li>two</li>",
                "<li>four</li>",
                "<li>five</li>",
                "<li>six</li>",
            ],
        )
        self.assertEqual(
            divtwo.xpath("./ul/li").extract(),
            ["<li>four</li>", "<li>five</li>", "<li>six</li>"],
        )
        self.assertEqual(
            divtwo.xpath(".//li").extract(),
            ["<li>four</li>", "<li>five</li>", "<li>six</li>"],
        )
        self.assertEqual(divtwo.xpath("./li").extract(), [])

    def test_selectorlist_getall_alias(self) -> None:
        """Nested selector tests using getall()"""
        body = """<body>
                    <div class='one'>
                      <ul>
                        <li>one</li><li>two</li>
                      </ul>
                    </div>
                    <div class='two'>
                      <ul>
                        <li>four</li><li>five</li><li>six</li>
                      </ul>
                    </div>
                  </body>"""

        x = self.sscls(text=body)
        divtwo = x.xpath('//div[@class="two"]')
        self.assertEqual(
            divtwo.xpath("//li").getall(),
            [
                "<li>one</li>",
                "<li>two</li>",
                "<li>four</li>",
                "<li>five</li>",
                "<li>six</li>",
            ],
        )
        self.assertEqual(
            divtwo.xpath("./ul/li").getall(),
            ["<li>four</li>", "<li>five</li>", "<li>six</li>"],
        )
        self.assertEqual(
            divtwo.xpath(".//li").getall(),
            ["<li>four</li>", "<li>five</li>", "<li>six</li>"],
        )
        self.assertEqual(divtwo.xpath("./li").getall(), [])

    def test_mixed_nested_selectors(self) -> None:
        body = """<body>
                    <div id=1>not<span>me</span></div>
                    <div class="dos"><p>text</p><a href='#'>foo</a></div>
               </body>"""
        sel = self.sscls(text=body)
        self.assertEqual(
            sel.xpath('//div[@id="1"]').css("span::text").extract(), ["me"]
        )
        self.assertEqual(sel.css("#1").xpath("./span/text()").extract(), ["me"])

    def test_dont_strip(self) -> None:
        sel = self.sscls(text='<div>fff: <a href="#">zzz</a></div>')
        self.assertEqual(sel.xpath("//text()").extract(), ["fff: ", "zzz"])

    def test_namespaces_simple(self) -> None:
        body = """
        <test xmlns:somens="http://scrapy.org">
           <somens:a id="foo">take this</a>
           <a id="bar">found</a>
        </test>
        """

        x = self.sscls(text=body, type="xml")

        x.register_namespace("somens", "http://scrapy.org")
        self.assertEqual(x.xpath("//somens:a/text()").extract(), ["take this"])

    def test_namespaces_adhoc(self) -> None:
        body = """
        <test xmlns:somens="http://scrapy.org">
           <somens:a id="foo">take this</a>
           <a id="bar">found</a>
        </test>
        """

        x = self.sscls(text=body, type="xml")

        self.assertEqual(
            x.xpath(
                "//somens:a/text()",
                namespaces={"somens": "http://scrapy.org"},
            ).extract(),
            ["take this"],
        )

    def test_namespaces_adhoc_variables(self) -> None:
        body = """
        <test xmlns:somens="http://scrapy.org">
           <somens:a id="foo">take this</a>
           <a id="bar">found</a>
        </test>
        """

        x = self.sscls(text=body, type="xml")

        self.assertEqual(
            x.xpath(
                "//somens:a/following-sibling::a[@id=$identifier]/text()",
                namespaces={"somens": "http://scrapy.org"},
                identifier="bar",
            ).extract(),
            ["found"],
        )

    def test_namespaces_multiple(self) -> None:
        body = """<?xml version="1.0" encoding="UTF-8"?>
<BrowseNode xmlns="http://webservices.amazon.com/AWSECommerceService/2005-10-05"
            xmlns:b="http://somens.com"
            xmlns:p="http://www.scrapy.org/product" >
    <b:Operation>hello</b:Operation>
    <TestTag b:att="value"><Other>value</Other></TestTag>
    <p:SecondTestTag><material>iron</material><price>90</price><p:name>Dried Rose</p:name></p:SecondTestTag>
</BrowseNode>
        """
        x = self.sscls(text=body, type="xml")
        x.register_namespace(
            "xmlns",
            "http://webservices.amazon.com/AWSECommerceService/2005-10-05",
        )
        x.register_namespace("p", "http://www.scrapy.org/product")
        x.register_namespace("b", "http://somens.com")
        self.assertEqual(len(x.xpath("//xmlns:TestTag")), 1)
        self.assertEqual(x.xpath("//b:Operation/text()").extract()[0], "hello")
        self.assertEqual(x.xpath("//xmlns:TestTag/@b:att").extract()[0], "value")
        self.assertEqual(
            x.xpath("//p:SecondTestTag/xmlns:price/text()").extract()[0], "90"
        )
        self.assertEqual(
            x.xpath("//p:SecondTestTag").xpath("./xmlns:price/text()")[0].extract(),
            "90",
        )
        self.assertEqual(
            x.xpath("//p:SecondTestTag/xmlns:material/text()").extract()[0],
            "iron",
        )

    def test_namespaces_multiple_adhoc(self) -> None:
        body = """<?xml version="1.0" encoding="UTF-8"?>
<BrowseNode xmlns="http://webservices.amazon.com/AWSECommerceService/2005-10-05"
            xmlns:b="http://somens.com"
            xmlns:p="http://www.scrapy.org/product" >
    <b:Operation>hello</b:Operation>
    <TestTag b:att="value"><Other>value</Other></TestTag>
    <p:SecondTestTag><material>iron</material><price>90</price><p:name>Dried Rose</p:name></p:SecondTestTag>
</BrowseNode>
        """
        x = self.sscls(text=body, type="xml")
        x.register_namespace(
            "xmlns",
            "http://webservices.amazon.com/AWSECommerceService/2005-10-05",
        )
        self.assertEqual(len(x.xpath("//xmlns:TestTag")), 1)

        # "b" namespace is not declared yet
        self.assertRaises(ValueError, x.xpath, "//xmlns:TestTag/@b:att")

        # "b" namespace being passed ad-hoc
        self.assertEqual(
            x.xpath(
                "//b:Operation/text()", namespaces={"b": "http://somens.com"}
            ).extract()[0],
            "hello",
        )

        # "b" namespace declaration is not cached
        self.assertRaises(ValueError, x.xpath, "//xmlns:TestTag/@b:att")

        # "xmlns" is still defined
        self.assertEqual(
            x.xpath(
                "//xmlns:TestTag/@b:att",
                namespaces={"b": "http://somens.com"},
            ).extract()[0],
            "value",
        )

        # chained selectors still have knowledge of register_namespace() operations
        self.assertEqual(
            x.xpath(
                "//p:SecondTestTag",
                namespaces={"p": "http://www.scrapy.org/product"},
            )
            .xpath("./xmlns:price/text()")[0]
            .extract(),
            "90",
        )

        # but chained selector don't know about parent ad-hoc declarations
        self.assertRaises(
            ValueError,
            x.xpath(
                "//p:SecondTestTag",
                namespaces={"p": "http://www.scrapy.org/product"},
            ).xpath,
            "p:name/text()",
        )

        # ad-hoc declarations need repeats when chaining
        self.assertEqual(
            x.xpath(
                "//p:SecondTestTag",
                namespaces={"p": "http://www.scrapy.org/product"},
            )
            .xpath(
                "p:name/text()",
                namespaces={"p": "http://www.scrapy.org/product"},
            )
            .extract_first(),
            "Dried Rose",
        )

        # declaring several ad-hoc namespaces
        self.assertEqual(
            x.xpath(
                "string(//b:Operation/following-sibling::xmlns:TestTag"
                "/following-sibling::*//p:name)",
                namespaces={
                    "b": "http://somens.com",
                    "p": "http://www.scrapy.org/product",
                },
            ).extract_first(),
            "Dried Rose",
        )

        # "p" prefix is not cached from previous calls
        self.assertRaises(ValueError, x.xpath, "//p:SecondTestTag/xmlns:price/text()")

        x.register_namespace("p", "http://www.scrapy.org/product")
        self.assertEqual(
            x.xpath("//p:SecondTestTag/xmlns:material/text()").extract()[0],
            "iron",
        )

    def test_make_links_absolute(self) -> None:
        text = '<a href="file.html">link to file</a>'
        sel = Selector(text=text, base_url="http://example.com")
        typing.cast(HtmlElement, sel.root).make_links_absolute()
        self.assertEqual(
            "http://example.com/file.html",
            sel.xpath("//a/@href").extract_first(),
        )

    def test_re(self) -> None:
        body = """<div>Name: Mary
                    <ul>
                      <li>Name: John</li>
                      <li>Age: 10</li>
                      <li>Name: Paul</li>
                      <li>Age: 20</li>
                    </ul>
                    Age: 20
                  </div>"""
        x = self.sscls(text=body)

        name_re = re.compile(r"Name: (\w+)")
        self.assertEqual(x.xpath("//ul/li").re(name_re), ["John", "Paul"])
        self.assertEqual(x.xpath("//ul/li").re(r"Age: (\d+)"), ["10", "20"])

        # Test named group, hit and miss
        x = self.sscls(text="foobar")
        self.assertEqual(x.re("(?P<extract>foo)"), ["foo"])
        self.assertEqual(x.re("(?P<extract>baz)"), [])

        # A purposely constructed test for an edge case
        x = self.sscls(text="baz")
        self.assertEqual(x.re("(?P<extract>foo)|(?P<bar>baz)"), [])

    def test_re_replace_entities(self) -> None:
        body = """<script>{"foo":"bar &amp; &quot;baz&quot;"}</script>"""
        x = self.sscls(text=body)

        name_re = re.compile('{"foo":(.*)}')

        # by default, only &amp; and &lt; are preserved ;
        # other entities are converted
        expected = '"bar &amp; "baz""'
        self.assertEqual(x.xpath("//script/text()").re(name_re), [expected])
        self.assertEqual(x.xpath("//script").re(name_re), [expected])
        self.assertEqual(x.xpath("//script/text()")[0].re(name_re), [expected])
        self.assertEqual(x.xpath("//script")[0].re(name_re), [expected])

        # check that re_first() works the same way for single value output
        self.assertEqual(x.xpath("//script").re_first(name_re), expected)
        self.assertEqual(x.xpath("//script")[0].re_first(name_re), expected)

        # switching off replace_entities will preserve &quot; also
        expected = '"bar &amp; &quot;baz&quot;"'
        self.assertEqual(
            x.xpath("//script/text()").re(name_re, replace_entities=False),
            [expected],
        )
        self.assertEqual(
            x.xpath("//script")[0].re(name_re, replace_entities=False),
            [expected],
        )

        self.assertEqual(
            x.xpath("//script/text()").re_first(name_re, replace_entities=False),
            expected,
        )
        self.assertEqual(
            x.xpath("//script")[0].re_first(name_re, replace_entities=False),
            expected,
        )

    def test_re_intl(self) -> None:
        body = "<div>Evento: cumplea\xf1os</div>"
        x = self.sscls(text=body)
        self.assertEqual(x.xpath("//div").re(r"Evento: (\w+)"), ["cumplea\xf1os"])

    def test_selector_over_text(self) -> None:
        hs = self.sscls(text="<root>lala</root>")
        self.assertEqual(hs.extract(), "<html><body><root>lala</root></body></html>")
        xs = self.sscls(text="<root>lala</root>", type="xml")
        self.assertEqual(xs.extract(), "<root>lala</root>")
        self.assertEqual(xs.xpath(".").extract(), ["<root>lala</root>"])

    def test_invalid_xpath(self) -> None:
        "Test invalid xpath raises ValueError with the invalid xpath"
        x = self.sscls(text="<html></html>")
        xpath = "//test[@foo='bar]"
        self.assertRaisesRegex(ValueError, re.escape(xpath), x.xpath, xpath)

    def test_invalid_xpath_unicode(self) -> None:
        "Test *Unicode* invalid xpath raises ValueError with the invalid xpath"
        x = self.sscls(text="<html></html>")
        xpath = "//test[@foo='\\u0431ar]"
        self.assertRaisesRegex(ValueError, re.escape(xpath), x.xpath, xpath)

    def test_http_header_encoding_precedence(self) -> None:
        # '\xa3'     = pound symbol in unicode
        # '\xc2\xa3' = pound symbol in utf-8
        # '\xa3'     = pound symbol in latin-1 (iso-8859-1)

        text = """<html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"></head>
        <body><span id="blank">\xa3</span></body></html>"""
        x = self.sscls(text=text)
        self.assertEqual(x.xpath("//span[@id='blank']/text()").extract(), ["\xa3"])

    def test_empty_bodies_shouldnt_raise_errors(self) -> None:
        self.sscls(text="").xpath("//text()").extract()

    def test_bodies_with_comments_only(self) -> None:
        sel = self.sscls(text="<!-- hello world -->", base_url="http://example.com")
        self.assertEqual("http://example.com", sel.root.base)

    def test_null_bytes_shouldnt_raise_errors(self) -> None:
        text = "<root>pre\x00post</root>"
        self.sscls(text).xpath("//text()").extract()

    def test_replacement_char_from_badly_encoded_body(self) -> None:
        # \xe9 alone isn't valid utf8 sequence
        text = "<html><p>an Jos\\ufffd de</p><html>"
        self.assertEqual(
            ["an Jos\\ufffd de"], self.sscls(text).xpath("//text()").extract()
        )

    def test_select_on_unevaluable_nodes(self) -> None:
        r = self.sscls(text='<span class="big">some text</span>')
        # Text node
        x1 = r.xpath("//text()")
        self.assertEqual(x1.extract(), ["some text"])
        self.assertEqual(x1.xpath(".//b").extract(), [])
        # Tag attribute
        x1 = r.xpath("//span/@class")
        self.assertEqual(x1.extract(), ["big"])
        self.assertEqual(x1.xpath(".//text()").extract(), [])

    def test_select_on_text_nodes(self) -> None:
        r = self.sscls(text="<div><b>Options:</b>opt1</div><div><b>Other</b>opt2</div>")
        x1 = r.xpath(
            "//div/descendant::text()[preceding-sibling::b[contains(text(), 'Options')]]"
        )
        self.assertEqual(x1.extract(), ["opt1"])

        x1 = r.xpath(
            "//div/descendant::text()/preceding-sibling::b[contains(text(), 'Options')]"
        )
        self.assertEqual(x1.extract(), ["<b>Options:</b>"])

    @unittest.skip("Text nodes lost parent node reference in lxml")
    def test_nested_select_on_text_nodes(self) -> None:
        # FIXME: does not work with lxml backend [upstream]
        r = self.sscls(text="<div><b>Options:</b>opt1</div><div><b>Other</b>opt2</div>")
        x1 = r.xpath("//div/descendant::text()")
        x2 = x1.xpath("./preceding-sibling::b[contains(text(), 'Options')]")
        self.assertEqual(x2.extract(), ["<b>Options:</b>"])

    def test_weakref_slots(self) -> None:
        """Check that classes are using slots and are weak-referenceable"""
        x = self.sscls(text="")
        weakref.ref(x)
        assert not hasattr(
            x, "__dict__"
        ), f"{x.__class__.__name__} does not use __slots__"

    def test_remove_namespaces(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-US" xmlns:media="http://search.yahoo.com/mrss/">
  <link type="text/html"/>
  <entry>
    <link type="text/html"/>
  </entry>
  <link type="application/atom+xml"/>
</feed>
"""
        sel = self.sscls(text=xml, type="xml")
        self.assertEqual(len(sel.xpath("//link")), 0)
        self.assertEqual(len(sel.xpath("./namespace::*")), 3)
        sel.remove_namespaces()
        self.assertEqual(len(sel.xpath("//link")), 3)
        self.assertEqual(len(sel.xpath("./namespace::*")), 1)

    def test_remove_namespaces_embedded(self) -> None:
        xml = """
        <feed xmlns="http://www.w3.org/2005/Atom">
          <link type="text/html"/>
          <entry>
            <link type="text/html"/>
          </entry>
          <svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 100 100">
            <linearGradient id="gradient">
              <stop class="begin" offset="0%" style="stop-color:yellow;"/>
              <stop class="end" offset="80%" style="stop-color:green;"/>
            </linearGradient>
            <circle cx="50" cy="50" r="30" style="fill:url(#gradient)" />
          </svg>
        </feed>
        """
        sel = self.sscls(text=xml, type="xml")
        self.assertEqual(len(sel.xpath("//link")), 0)
        self.assertEqual(len(sel.xpath("//stop")), 0)
        self.assertEqual(len(sel.xpath("./namespace::*")), 2)
        self.assertEqual(
            len(
                sel.xpath(
                    "//f:link",
                    namespaces={"f": "http://www.w3.org/2005/Atom"},
                )
            ),
            2,
        )
        self.assertEqual(
            len(sel.xpath("//s:stop", namespaces={"s": "http://www.w3.org/2000/svg"})),
            2,
        )
        sel.remove_namespaces()
        self.assertEqual(len(sel.xpath("//link")), 2)
        self.assertEqual(len(sel.xpath("//stop")), 2)
        self.assertEqual(len(sel.xpath("./namespace::*")), 1)

    def test_remove_attributes_namespaces(self) -> None:
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:atom="http://www.w3.org/2005/Atom" xml:lang="en-US" xmlns:media="http://search.yahoo.com/mrss/">
  <link atom:type="text/html"/>
  <entry>
    <link atom:type="text/html"/>
  </entry>
  <link atom:type="application/atom+xml"/>
</feed>
"""
        sel = self.sscls(text=xml, type="xml")
        self.assertEqual(len(sel.xpath("//link/@type")), 0)
        sel.remove_namespaces()
        self.assertEqual(len(sel.xpath("//link/@type")), 3)

    def test_smart_strings(self) -> None:
        """Lxml smart strings return values"""

        class SmartStringsSelector(Selector):
            _lxml_smart_strings = True

        body = """<body>
                    <div class='one'>
                      <ul>
                        <li>one</li><li>two</li>
                      </ul>
                    </div>
                    <div class='two'>
                      <ul>
                        <li>four</li><li>five</li><li>six</li>
                      </ul>
                    </div>
                  </body>"""

        # .getparent() is available for text nodes and attributes
        # only when smart_strings are on
        x = self.sscls(text=body)
        li_text = x.xpath("//li/text()")
        self.assertFalse(any([hasattr(e.root, "getparent") for e in li_text]))
        div_class = x.xpath("//div/@class")
        self.assertFalse(any([hasattr(e.root, "getparent") for e in div_class]))

        smart_x = SmartStringsSelector(text=body)
        smart_li_text = smart_x.xpath("//li/text()")
        self.assertTrue(all([hasattr(e.root, "getparent") for e in smart_li_text]))
        smart_div_class = smart_x.xpath("//div/@class")
        self.assertTrue(all([hasattr(e.root, "getparent") for e in smart_div_class]))

    def test_xml_entity_expansion(self) -> None:
        malicious_xml = (
            '<?xml version="1.0" encoding="ISO-8859-1"?>'
            "<!DOCTYPE foo [ <!ELEMENT foo ANY > <!ENTITY xxe SYSTEM "
            '"file:///etc/passwd" >]><foo>&xxe;</foo>'
        )

        sel = self.sscls(text=malicious_xml, type="xml")

        self.assertEqual(sel.extract(), "<foo>&xxe;</foo>")

    def test_configure_base_url(self) -> None:
        sel = self.sscls(text="nothing", base_url="http://example.com")
        self.assertEqual("http://example.com", sel.root.base)

    def test_extending_selector(self) -> None:
        class MySelectorList(SelectorList["MySelector"]):
            pass

        class MySelector(Selector):
            selectorlist_cls = MySelectorList

            def extra_method(self) -> str:
                return "extra" + cast(str, self.get())

        sel = MySelector(text="<html><div>foo</div></html>")
        self.assertIsInstance(sel.xpath("//div"), MySelectorList)
        self.assertIsInstance(sel.xpath("//div")[0], MySelector)
        self.assertIsInstance(sel.css("div"), MySelectorList)
        self.assertIsInstance(sel.css("div")[0], MySelector)
        content: str = sel.css("div")[0].extra_method()
        self.assertEqual("extra<div>foo</div>", content)

    def test_replacement_null_char_from_body(self) -> None:
        text = "<html>\x00<body><p>Grainy</p></body></html>"
        self.assertEqual(
            "<html><body><p>Grainy</p></body></html>",
            self.sscls(text).extract(),
        )

    def test_remove_selector_list(self) -> None:
        sel = self.sscls(
            text="<html><body><ul><li>1</li><li>2</li><li>3</li></ul></body></html>"
        )
        sel_list = sel.css("li")
        sel_list.drop()
        self.assertIsSelectorList(sel.css("li"))
        self.assertEqual(sel.css("li"), [])

    def test_remove_selector(self) -> None:
        sel = self.sscls(
            text="<html><body><ul><li>1</li><li>2</li><li>3</li></ul></body></html>"
        )
        sel_list = sel.css("li")
        sel_list[0].drop()
        self.assertIsSelectorList(sel.css("li"))
        self.assertEqual(sel.css("li::text").getall(), ["2", "3"])

    def test_remove_pseudo_element_selector_list(self) -> None:
        sel = self.sscls(
            text="<html><body><ul><li>1</li><li>2</li><li>3</li></ul></body></html>"
        )
        sel_list = sel.css("li::text")
        self.assertEqual(sel_list.getall(), ["1", "2", "3"])
        with self.assertRaises(CannotRemoveElementWithoutRoot):
            sel_list.drop()

        self.assertIsSelectorList(sel.css("li"))
        self.assertEqual(sel.css("li::text").getall(), ["1", "2", "3"])

    def test_remove_pseudo_element_selector(self) -> None:
        sel = self.sscls(
            text="<html><body><ul><li>1</li><li>2</li><li>3</li></ul></body></html>"
        )
        sel_list = sel.css("li::text")
        self.assertEqual(sel_list.getall(), ["1", "2", "3"])
        with self.assertRaises(CannotRemoveElementWithoutRoot):
            sel_list[0].drop()

        self.assertIsSelectorList(sel.css("li"))
        self.assertEqual(sel.css("li::text").getall(), ["1", "2", "3"])

    def test_remove_root_element_selector(self) -> None:
        sel = self.sscls(
            text="<html><body><ul><li>1</li><li>2</li><li>3</li></ul></body></html>"
        )
        sel_list = sel.css("li::text")
        self.assertEqual(sel_list.getall(), ["1", "2", "3"])
        with self.assertRaises(CannotRemoveElementWithoutParent):
            sel.drop()

        with self.assertRaises(CannotRemoveElementWithoutParent):
            sel.css("html").drop()

        self.assertIsSelectorList(sel.css("li"))
        self.assertEqual(sel.css("li::text").getall(), ["1", "2", "3"])

        sel.css("body").drop()
        self.assertEqual(sel.get(), "<html></html>")

    def test_deep_nesting(self) -> None:
        lxml_version = Version(etree.__version__)
        lxml_huge_tree_version = Version("4.2")

        content = """
        <html>
        <body>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span><span>
        <span><span><span><span><span><span><span><span><span><span><span><span>
        hello world
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span></span></span></span></span></span></span>
        </span></span></span></span></span></span></span></span></span></span>
        <table>
         <tr><td>some test</td></tr>
        </table>
        </body>
        </html>
        """

        # If lxml doesn't support huge trees expect wrong results and a warning
        if lxml_version < lxml_huge_tree_version:
            with warnings.catch_warnings(record=True) as w:
                sel = Selector(text=content)
                self.assertIn("huge_tree", str(w[0].message))
                self.assertLessEqual(len(sel.css("span")), 256)
                self.assertEqual(len(sel.css("td")), 0)
            return

        # Same goes for explicitly disabling huge trees
        with warnings.catch_warnings(record=True) as w:
            sel = Selector(text=content, huge_tree=False)
            self.assertIn("huge_tree", str(w[0].message))
            self.assertLessEqual(len(sel.css("span")), 256)
            self.assertEqual(len(sel.css("td")), 0)

        # If huge trees are enabled, elements with a depth > 255 should be found
        sel = Selector(text=content)
        nest_level = 282
        self.assertEqual(len(sel.css("span")), nest_level)
        self.assertEqual(len(sel.css("td")), 1)

    def test_invalid_type(self) -> None:
        with self.assertRaises(ValueError):
            self.sscls("", type="xhtml")

    def test_default_type(self) -> None:
        text = "foo"
        selector = self.sscls(text)
        self.assertEqual(selector.type, "html")

    def test_json_type(self) -> None:
        obj = 1
        selector = self.sscls(str(obj), type="json")
        self.assertEqual(selector.root, obj)
        self.assertEqual(selector.type, "json")

    def test_html_root(self) -> None:
        root = etree.fromstring("<html/>")
        selector = self.sscls(root=root)
        self.assertEqual(selector.root, root)
        self.assertEqual(selector.type, "html")

    def test_json_root(self) -> None:
        obj = 1
        selector = self.sscls(root=obj)
        self.assertEqual(selector.root, obj)
        self.assertEqual(selector.type, "json")

    def test_json_xpath(self) -> None:
        obj = 1
        selector = self.sscls(root=obj)
        with self.assertRaises(ValueError):
            selector.xpath("//*")

    def test_json_css(self) -> None:
        obj = 1
        selector = self.sscls(root=obj)
        with self.assertRaises(ValueError):
            selector.css("*")

    def test_invalid_json(self) -> None:
        text = "<html/>"
        selector = self.sscls(text, type="json")
        self.assertEqual(selector.root, None)
        self.assertEqual(selector.type, "json")

    def test_text_and_root_warning(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            Selector(text="a", root="b")
            self.assertIn("both text and root", str(w[0].message))

    def test_etree_root_invalid_type(self) -> None:
        selector = Selector("<html></html>")
        self.assertRaisesRegex(
            ValueError,
            "object as root",
            Selector,
            root=selector.root,
            type="text",
        )
        self.assertRaisesRegex(
            ValueError,
            "object as root",
            Selector,
            root=selector.root,
            type="json",
        )

    def test_json_selector_representation(self) -> None:
        selector = Selector(text="true")
        assert repr(selector) == "<Selector query=None data='True'>"
        assert str(selector) == "True"
        selector = Selector(text="1")
        assert repr(selector) == "<Selector query=None data='1'>"
        assert str(selector) == "1"


class ExsltTestCase(unittest.TestCase):

    sscls = Selector

    def test_regexp(self) -> None:
        """EXSLT regular expression tests"""
        body = """
        <p><input name='a' value='1'/><input name='b' value='2'/></p>
        <div class="links">
        <a href="/first.html">first link</a>
        <a href="/second.html">second link</a>
        <a href="http://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.xml">EXSLT match example</a>
        </div>
        """
        sel = self.sscls(text=body)

        # re:test()
        self.assertEqual(
            sel.xpath('//input[re:test(@name, "[A-Z]+", "i")]').extract(),
            [x.extract() for x in sel.xpath('//input[re:test(@name, "[A-Z]+", "i")]')],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath(r'//a[re:test(@href, "\.html$")]/text()')],
            ["first link", "second link"],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('//a[re:test(@href, "first")]/text()')],
            ["first link"],
        )
        self.assertEqual(
            [x.extract() for x in sel.xpath('//a[re:test(@href, "second")]/text()')],
            ["second link"],
        )

        # re:match() is rather special: it returns a node-set of <match> nodes
        # ['<match>http://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.xml</match>',
        # '<match>http</match>',
        # '<match>www.bayes.co.uk</match>',
        # '<match></match>',
        # '<match>/xml/index.xml?/xml/utils/rechecker.xml</match>']
        self.assertEqual(
            sel.xpath(
                r're:match(//a[re:test(@href, "\.xml$")]/@href,'
                r'"(\w+):\/\/([^/:]+)(:\d*)?([^# ]*)")/text()'
            ).extract(),
            [
                "http://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.xml",
                "http",
                "www.bayes.co.uk",
                "",
                "/xml/index.xml?/xml/utils/rechecker.xml",
            ],
        )

        # re:replace()
        self.assertEqual(
            sel.xpath(
                r're:replace(//a[re:test(@href, "\.xml$")]/@href,'
                r'"(\w+)://(.+)(\.xml)", "","https://\2.html")'
            ).extract(),
            ["https://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.html"],
        )

    def test_set(self) -> None:
        """EXSLT set manipulation tests"""
        # microdata example from http://schema.org/Event
        body = """
        <div itemscope itemtype="http://schema.org/Event">
          <a itemprop="url" href="nba-miami-philidelphia-game3.html">
          NBA Eastern Conference First Round Playoff Tickets:
          <span itemprop="name"> Miami Heat at Philadelphia 76ers - Game 3 (Home Game 1) </span>
          </a>

          <meta itemprop="startDate" content="2016-04-21T20:00">
            Thu, 04/21/16
            8:00 p.m.

          <div itemprop="location" itemscope itemtype="http://schema.org/Place">
            <a itemprop="url" href="wells-fargo-center.html">
            Wells Fargo Center
            </a>
            <div itemprop="address" itemscope itemtype="http://schema.org/PostalAddress">
              <span itemprop="addressLocality">Philadelphia</span>,
              <span itemprop="addressRegion">PA</span>
            </div>
          </div>

          <div itemprop="offers" itemscope itemtype="http://schema.org/AggregateOffer">
            Priced from: <span itemprop="lowPrice">$35</span>
            <span itemprop="offerCount">1938</span> tickets left
          </div>
        </div>
        """
        sel = self.sscls(text=body)

        self.assertEqual(
            sel.xpath(
                """//div[@itemtype="http://schema.org/Event"]
                            //@itemprop"""
            ).extract(),
            [
                "url",
                "name",
                "startDate",
                "location",
                "url",
                "address",
                "addressLocality",
                "addressRegion",
                "offers",
                "lowPrice",
                "offerCount",
            ],
        )

        self.assertEqual(
            sel.xpath(
                """
                set:difference(//div[@itemtype="http://schema.org/Event"]
                                    //@itemprop,
                               //div[@itemtype="http://schema.org/Event"]
                                    //*[@itemscope]/*/@itemprop)"""
            ).extract(),
            ["url", "name", "startDate", "location", "offers"],
        )

    def test_dont_remove_text_after_deleted_element(self) -> None:
        sel = self.sscls(
            text="""<html><body>Text before.<span>Text in.</span> Text after.</body></html>
            """
        )
        sel.css("span").drop()
        self.assertEqual(
            sel.get(), "<html><body>Text before. Text after.</body></html>"
        )

    def test_drop_with_xml_type(self) -> None:
        sel = self.sscls(text="<a><b></b><c/></a>", type="xml")
        el = sel.xpath("//b")[0]
        assert el.root.getparent() is not None
        el.drop()
        assert sel.get() == "<a><c/></a>"


class SelectorBytesInput(Selector):
    def __init__(
        self,
        text: Optional[str] = None,
        type: Optional[str] = None,
        body: bytes = b"",
        encoding: str = "utf-8",
        namespaces: Optional[Mapping[str, str]] = None,
        root: Optional[Any] = _NOT_SET,
        base_url: Optional[str] = None,
        _expr: Optional[str] = None,
        huge_tree: bool = LXML_SUPPORTS_HUGE_TREE,
    ) -> None:
        if text:
            body = bytes(text, encoding=encoding)
            text = None
        super().__init__(
            text=text,
            type=type,
            body=body,
            encoding=encoding,
            namespaces=namespaces,
            root=root,
            base_url=base_url,
            _expr=_expr,
            huge_tree=huge_tree,
        )


class SelectorTestCaseBytes(SelectorTestCase):
    sscls = SelectorBytesInput

    def test_representation_slice(self) -> None:
        pass

    def test_representation_unicode_query(self) -> None:
        pass

    def test_weakref_slots(self) -> None:
        pass

    def test_check_text_argument_type(self) -> None:
        self.assertRaisesRegex(
            TypeError,
            "body argument should be of type",
            self.sscls,
            body="<html/>",
        )


class ExsltTestCaseBytes(ExsltTestCase):
    sscls = SelectorBytesInput
