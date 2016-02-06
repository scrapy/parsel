# -*- coding: utf-8 -*-
import re
import weakref
import six
import unittest
import json
import warnings
from parsel import Selector


class SelectorTestCase(unittest.TestCase):

    sscls = Selector

    def test_simple_selection(self):
        """Simple selector tests"""
        body = u"<p><input name='a'value='1'/><input name='b'value='2'/></p>"
        sel = self.sscls(text=body)

        xl = sel.xpath('//input')
        self.assertEqual(2, len(xl))
        for x in xl:
            assert isinstance(x, self.sscls)

        self.assertEqual(sel.xpath('//input').extract(),
                         [x.extract() for x in sel.xpath('//input')])

        self.assertEqual([x.extract() for x in sel.xpath("//input[@name='a']/@name")],
                         [u'a'])
        self.assertEqual([x.extract() for x in sel.xpath("number(concat(//input[@name='a']/@value, //input[@name='b']/@value))")],
                         [u'12.0'])

        self.assertEqual(sel.xpath("concat('xpath', 'rules')").extract(),
                         [u'xpathrules'])
        self.assertEqual([x.extract() for x in sel.xpath("concat(//input[@name='a']/@value, //input[@name='b']/@value)")],
                         [u'12'])

    def test_representation_slice(self):
        body = u"<p><input name='{}' value='\xa9'/></p>".format(50 * 'b')
        sel = self.sscls(text=body)

        representation = "<Selector type='html' path='//input/@name' data='{}'>".format(40 * 'b')
        if six.PY2:
            representation = "<Selector type='html' path='//input/@name' data=u'{}'>".format(40 * 'b')

        self.assertEqual(
            [repr(it) for it in sel.xpath('//input/@name')],
            [representation]
        )

    def test_representation_unicode_query(self):
        body = u"<p><input name='{}' value='\xa9'/></p>".format(50 * 'b')

        representation = '<Selector type=\'html\' path=\'//input[@value="©"]/@value\' data=\'©\'>'
        if six.PY2:
            representation = "<Selector type='html' path=u'//input[@value=\"\\xa9\"]/@value' data=u'\\xa9'>"

        sel = self.sscls(text=body)
        self.assertEqual(
            [repr(it) for it in sel.xpath(u'//input[@value="\xa9"]/@value')],
            [representation]
        )

    def test_check_text_argument_type(self):
        self.assertRaisesRegexp(TypeError, 'text argument should be of type',
                                self.sscls, b'<html/>')

    def test_extract_first(self):
        """Test if extract_first() returns first element"""
        body = u'<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(sel.xpath('//ul/li/text()').extract_first(),
                         sel.xpath('//ul/li/text()').extract()[0])

        self.assertEqual(sel.xpath('//ul/li[@id="1"]/text()').extract_first(),
                         sel.xpath('//ul/li[@id="1"]/text()').extract()[0])

        self.assertEqual(sel.xpath('//ul/li[2]/text()').extract_first(),
                         sel.xpath('//ul/li/text()').extract()[1])

        self.assertEqual(sel.xpath('/ul/li[@id="doesnt-exist"]/text()').extract_first(), None)

    def test_extract_first_default(self):
        """Test if extract_first() returns default value when no results found"""
        body = u'<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(sel.xpath('//div/text()').extract_first(default='missing'), 'missing')

    def test_re_first(self):
        """Test if re_first() returns first matched element"""
        body = u'<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(text=body)

        self.assertEqual(sel.xpath('//ul/li/text()').re_first('\d'),
                         sel.xpath('//ul/li/text()').re('\d')[0])

        self.assertEqual(sel.xpath('//ul/li[@id="1"]/text()').re_first('\d'),
                         sel.xpath('//ul/li[@id="1"]/text()').re('\d')[0])

        self.assertEqual(sel.xpath('//ul/li[2]/text()').re_first('\d'),
                         sel.xpath('//ul/li/text()').re('\d')[1])

        self.assertEqual(sel.xpath('/ul/li/text()').re_first('\w+'), None)
        self.assertEqual(sel.xpath('/ul/li[@id="doesnt-exist"]/text()').re_first('\d'), None)

    def test_select_unicode_query(self):
        body = u"<p><input name='\xa9' value='1'/></p>"
        sel = self.sscls(text=body)
        self.assertEqual(sel.xpath(u'//input[@name="\xa9"]/@value').extract(), [u'1'])

    def test_list_elements_type(self):
        """Test Selector returning the same type in selection methods"""
        text = u'<p>test<p>'
        assert isinstance(self.sscls(text=text).xpath("//p")[0], self.sscls)
        assert isinstance(self.sscls(text=text).css("p")[0], self.sscls)

    def test_boolean_result(self):
        body = u"<p><input name='a'value='1'/><input name='b'value='2'/></p>"
        xs = self.sscls(text=body)
        self.assertEquals(xs.xpath("//input[@name='a']/@name='a'").extract(), [u'1'])
        self.assertEquals(xs.xpath("//input[@name='a']/@name='n'").extract(), [u'0'])

    def test_differences_parsing_xml_vs_html(self):
        """Test that XML and HTML Selector's behave differently"""
        # some text which is parsed differently by XML and HTML flavors
        text = u'<div><img src="a.jpg"><p>Hello</div>'
        hs = self.sscls(text=text, type='html')
        self.assertEqual(hs.xpath("//div").extract(),
                         [u'<div><img src="a.jpg"><p>Hello</p></div>'])

        xs = self.sscls(text=text, type='xml')
        self.assertEqual(xs.xpath("//div").extract(),
                         [u'<div><img src="a.jpg"><p>Hello</p></img></div>'])

    def test_error_for_unknown_selector_type(self):
        self.assertRaises(ValueError, self.sscls, text=u'', type='_na_')

    def test_text_or_root_is_required(self):
        self.assertRaisesRegexp(ValueError,
                                'Selector needs either text or root argument',
                                self.sscls)

    def test_bool(self):
        text = u'<a href="" >false</a><a href="nonempty">true</a>'
        hs = self.sscls(text=text, type='html')
        falsish = hs.xpath('//a/@href')[0]
        self.assertEqual(falsish.extract(), u'')
        self.assertFalse(falsish)
        trueish = hs.xpath('//a/@href')[1]
        self.assertEqual(trueish.extract(), u'nonempty')
        self.assertTrue(trueish)

    def test_slicing(self):
        text = u'<div><p>1</p><p>2</p><p>3</p></div>'
        hs = self.sscls(text=text, type='html')
        self.assertIsInstance(hs.css('p')[2], self.sscls)
        self.assertIsInstance(hs.css('p')[2:3], self.sscls.selectorlist_cls)
        self.assertIsInstance(hs.css('p')[:2], self.sscls.selectorlist_cls)
        self.assertEqual(hs.css('p')[2:3].extract(), [u'<p>3</p>'])
        self.assertEqual(hs.css('p')[1:3].extract(), [u'<p>2</p>', u'<p>3</p>'])

    def test_nested_selectors(self):
        """Nested selector tests"""
        body = u"""<body>
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
        self.assertEqual(divtwo.xpath("//li").extract(),
                         ["<li>one</li>", "<li>two</li>", "<li>four</li>", "<li>five</li>", "<li>six</li>"])
        self.assertEqual(divtwo.xpath("./ul/li").extract(),
                         ["<li>four</li>", "<li>five</li>", "<li>six</li>"])
        self.assertEqual(divtwo.xpath(".//li").extract(),
                         ["<li>four</li>", "<li>five</li>", "<li>six</li>"])
        self.assertEqual(divtwo.xpath("./li").extract(), [])

    def test_mixed_nested_selectors(self):
        body = u'''<body>
                    <div id=1>not<span>me</span></div>
                    <div class="dos"><p>text</p><a href='#'>foo</a></div>
               </body>'''
        sel = self.sscls(text=body)
        self.assertEqual(sel.xpath('//div[@id="1"]').css('span::text').extract(), [u'me'])
        self.assertEqual(sel.css('#1').xpath('./span/text()').extract(), [u'me'])

    def test_dont_strip(self):
        sel = self.sscls(text=u'<div>fff: <a href="#">zzz</a></div>')
        self.assertEqual(sel.xpath("//text()").extract(), [u'fff: ', u'zzz'])

    def test_namespaces_simple(self):
        body = u"""
        <test xmlns:somens="http://scrapy.org">
           <somens:a id="foo">take this</a>
           <a id="bar">found</a>
        </test>
        """

        x = self.sscls(text=body, type='xml')

        x.register_namespace("somens", "http://scrapy.org")
        self.assertEqual(x.xpath("//somens:a/text()").extract(),
                         [u'take this'])

    def test_namespaces_multiple(self):
        body = u"""<?xml version="1.0" encoding="UTF-8"?>
<BrowseNode xmlns="http://webservices.amazon.com/AWSECommerceService/2005-10-05"
            xmlns:b="http://somens.com"
            xmlns:p="http://www.scrapy.org/product" >
    <b:Operation>hello</b:Operation>
    <TestTag b:att="value"><Other>value</Other></TestTag>
    <p:SecondTestTag><material>iron</material><price>90</price><p:name>Dried Rose</p:name></p:SecondTestTag>
</BrowseNode>
        """
        x = self.sscls(text=body, type='xml')
        x.register_namespace("xmlns", "http://webservices.amazon.com/AWSECommerceService/2005-10-05")
        x.register_namespace("p", "http://www.scrapy.org/product")
        x.register_namespace("b", "http://somens.com")
        self.assertEqual(len(x.xpath("//xmlns:TestTag")), 1)
        self.assertEqual(x.xpath("//b:Operation/text()").extract()[0], 'hello')
        self.assertEqual(x.xpath("//xmlns:TestTag/@b:att").extract()[0], 'value')
        self.assertEqual(x.xpath("//p:SecondTestTag/xmlns:price/text()").extract()[0], '90')
        self.assertEqual(x.xpath("//p:SecondTestTag").xpath("./xmlns:price/text()")[0].extract(), '90')
        self.assertEqual(x.xpath("//p:SecondTestTag/xmlns:material/text()").extract()[0], 'iron')

    def test_re(self):
        body = u"""<div>Name: Mary
                    <ul>
                      <li>Name: John</li>
                      <li>Age: 10</li>
                      <li>Name: Paul</li>
                      <li>Age: 20</li>
                    </ul>
                    Age: 20
                  </div>"""
        x = self.sscls(text=body)

        name_re = re.compile("Name: (\w+)")
        self.assertEqual(x.xpath("//ul/li").re(name_re),
                         ["John", "Paul"])
        self.assertEqual(x.xpath("//ul/li").re("Age: (\d+)"),
                         ["10", "20"])

    def test_re_intl(self):
        body = u'<div>Evento: cumplea\xf1os</div>'
        x = self.sscls(text=body)
        self.assertEqual(x.xpath("//div").re("Evento: (\w+)"), [u'cumplea\xf1os'])

    def test_selector_over_text(self):
        hs = self.sscls(text=u'<root>lala</root>')
        self.assertEqual(hs.extract(), u'<html><body><root>lala</root></body></html>')
        xs = self.sscls(text=u'<root>lala</root>', type='xml')
        self.assertEqual(xs.extract(), u'<root>lala</root>')
        self.assertEqual(xs.xpath('.').extract(), [u'<root>lala</root>'])

    def test_invalid_xpath(self):
        "Test invalid xpath raises ValueError with the invalid xpath"
        x = self.sscls(text=u"<html></html>")
        xpath = "//test[@foo='bar]"
        self.assertRaisesRegexp(ValueError, re.escape(xpath), x.xpath, xpath)

    def test_invalid_xpath_unicode(self):
        "Test *Unicode* invalid xpath raises ValueError with the invalid xpath"
        x = self.sscls(text=u"<html></html>")
        xpath = u"//test[@foo='\u0431ar]"
        encoded = xpath if six.PY3 else xpath.encode('unicode_escape')
        self.assertRaisesRegexp(ValueError, re.escape(encoded), x.xpath, xpath)

    def test_http_header_encoding_precedence(self):
        # u'\xa3'     = pound symbol in unicode
        # u'\xc2\xa3' = pound symbol in utf-8
        # u'\xa3'     = pound symbol in latin-1 (iso-8859-1)

        text = u'''<html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"></head>
        <body><span id="blank">\xa3</span></body></html>'''
        x = self.sscls(text=text)
        self.assertEquals(x.xpath("//span[@id='blank']/text()").extract(),
                          [u'\xa3'])

    def test_empty_bodies_shouldnt_raise_errors(self):
        self.sscls(text=u'').xpath('//text()').extract()

    def test_null_bytes_shouldnt_raise_errors(self):
        text = u'<root>pre\x00post</root>'
        self.sscls(text).xpath('//text()').extract()

    def test_replacement_char_from_badly_encoded_body(self):
        # \xe9 alone isn't valid utf8 sequence
        text = u'<html><p>an Jos\ufffd de</p><html>'
        self.assertEquals([u'an Jos\ufffd de'],
                          self.sscls(text).xpath('//text()').extract())

    def test_select_on_unevaluable_nodes(self):
        r = self.sscls(text=u'<span class="big">some text</span>')
        # Text node
        x1 = r.xpath('//text()')
        self.assertEquals(x1.extract(), [u'some text'])
        self.assertEquals(x1.xpath('.//b').extract(), [])
        # Tag attribute
        x1 = r.xpath('//span/@class')
        self.assertEquals(x1.extract(), [u'big'])
        self.assertEquals(x1.xpath('.//text()').extract(), [])

    def test_select_on_text_nodes(self):
        r = self.sscls(text=u'<div><b>Options:</b>opt1</div><div><b>Other</b>opt2</div>')
        x1 = r.xpath("//div/descendant::text()[preceding-sibling::b[contains(text(), 'Options')]]")
        self.assertEquals(x1.extract(), [u'opt1'])

        x1 = r.xpath("//div/descendant::text()/preceding-sibling::b[contains(text(), 'Options')]")
        self.assertEquals(x1.extract(), [u'<b>Options:</b>'])

    @unittest.skip("Text nodes lost parent node reference in lxml")
    def test_nested_select_on_text_nodes(self):
        # FIXME: does not work with lxml backend [upstream]
        r = self.sscls(text=u'<div><b>Options:</b>opt1</div><div><b>Other</b>opt2</div>')
        x1 = r.xpath("//div/descendant::text()")
        x2 = x1.xpath("./preceding-sibling::b[contains(text(), 'Options')]")
        self.assertEquals(x2.extract(), [u'<b>Options:</b>'])

    def test_weakref_slots(self):
        """Check that classes are using slots and are weak-referenceable"""
        x = self.sscls(text=u'')
        weakref.ref(x)
        assert not hasattr(x, '__dict__'), "%s does not use __slots__" % \
            x.__class__.__name__

    def test_remove_namespaces(self):
        xml = u"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-US" xmlns:media="http://search.yahoo.com/mrss/">
  <link type="text/html">
  <link type="application/atom+xml">
</feed>
"""
        sel = self.sscls(text=xml, type='xml')
        self.assertEqual(len(sel.xpath("//link")), 0)
        sel.remove_namespaces()
        self.assertEqual(len(sel.xpath("//link")), 2)

    def test_remove_attributes_namespaces(self):
        xml = u"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:atom="http://www.w3.org/2005/Atom" xml:lang="en-US" xmlns:media="http://search.yahoo.com/mrss/">
  <link atom:type="text/html">
  <link atom:type="application/atom+xml">
</feed>
"""
        sel = self.sscls(text=xml, type='xml')
        self.assertEqual(len(sel.xpath("//link/@type")), 0)
        sel.remove_namespaces()
        self.assertEqual(len(sel.xpath("//link/@type")), 2)

    def test_smart_strings(self):
        """Lxml smart strings return values"""

        class SmartStringsSelector(Selector):
            _lxml_smart_strings = True

        body = u"""<body>
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
        li_text = x.xpath('//li/text()')
        self.assertFalse(any(map(lambda e: hasattr(e.root, 'getparent'), li_text)))
        div_class = x.xpath('//div/@class')
        self.assertFalse(any(map(lambda e: hasattr(e.root, 'getparent'), div_class)))

        x = SmartStringsSelector(text=body)
        li_text = x.xpath('//li/text()')
        self.assertTrue(all(map(lambda e: hasattr(e.root, 'getparent'), li_text)))
        div_class = x.xpath('//div/@class')
        self.assertTrue(all(map(lambda e: hasattr(e.root, 'getparent'), div_class)))

    def test_xml_entity_expansion(self):
        malicious_xml = u'<?xml version="1.0" encoding="ISO-8859-1"?>'\
            '<!DOCTYPE foo [ <!ELEMENT foo ANY > <!ENTITY xxe SYSTEM '\
            '"file:///etc/passwd" >]><foo>&xxe;</foo>'

        sel = self.sscls(text=malicious_xml, type='xml')

        self.assertEqual(sel.extract(), '<foo>&xxe;</foo>')

    def test_configure_base_url(self):
        sel = self.sscls(text=u'nothing', base_url='http://example.com')
        self.assertEquals(u'http://example.com', sel.root.base)

    def test_extending_selector(self):
        class MySelectorList(Selector.selectorlist_cls):
            pass

        class MySelector(Selector):
            selectorlist_cls = MySelectorList

        sel = MySelector(text=u'<html><div>foo</div></html>')
        self.assertIsInstance(sel.xpath('//div'), MySelectorList)
        self.assertIsInstance(sel.xpath('//div')[0], MySelector)
        self.assertIsInstance(sel.css('div'), MySelectorList)
        self.assertIsInstance(sel.css('div')[0], MySelector)

    def test_simple_selection_json(self):
        jsbody = u"""
        {
            "products": [
                {
                    "product": {
                        "img_url": [
                            "http://example.com/img1.png",
                            "http://example.com/img1.jpeg"
                        ],
                        "id": 1
                    }
                },
                {
                    "product": {
                        "img_url": [
                            "http://example.com/img2.png",
                            "http://example.com/img2.jpeg"
                        ],
                        "id": 2
                    }
                }
            ]
        }
        """
        jmsel = self.sscls(text=jsbody, type='json')
        jl = jmsel.jmespath('products[].product.id')
        self.assertEqual(2, len(jl))
        for x in jl:
            assert isinstance(x, self.sscls)
        self.assertEqual(jl.extract(),
                         [x.extract() for x in jl])
        self.assertEqual([x.extract() for x in jl],
                         [u'1', u'2'])

        self.assertEqual(len([x.extract() for x in jmsel.jmespath('*[*].*.img_url')]),
                         4)
        self.assertEqual([x.extract() for x in jmsel.jmespath('*[*].*.img_url')],
                         [u'http://example.com/img1.png',
                          u'http://example.com/img1.jpeg',
                          u'http://example.com/img2.png',
                          u'http://example.com/img2.jpeg'])

        self.assertEqual([x.extract() for x in jmsel.jmespath('products[0].product.img_url.join(`, `, @)')],
                         [u'http://example.com/img1.png, http://example.com/img1.jpeg'])

    def test_representation_slice_json(self):
        jsbody = u"""
            {{
                "products": [
                    {{
                        "product": {{
                            "name": "{}",
                            "id": 1
                        }}
                    }}]
            }}
            """.format(50*'b')
        jmsel = self.sscls(text=jsbody, type='json')

        representation = "<Selector type='json' path='*[0].*.name' data='{}'>".format(40 * 'b')
        if six.PY2:
            representation = "<Selector type='json' path='*[0].*.name' data=u'{}'>".format(40 * 'b')

        self.assertEqual(
            [repr(it) for it in jmsel.jmespath('*[0].*.name')],
            [representation]
        )

    def test_representation_unicode_query_json(self):
        jsbody = u"""
        {
            "products": [
                {
                    "product": {
                        "name": "\xa9",
                        "id": 1
                    }
                }]
        }
        """
        representation = '<Selector type=\'json\' path=' \
                         '\"products[?product.name==\'©\'].product.name\" data=\'©\'>'
        if six.PY2:
            representation = '<Selector type=\'json\' path=' \
                             'u"products[?product.name==\'\\xa9\'].product.name" data=u\'\\xa9\'>'

        jmsel = self.sscls(text=jsbody, type='json')
        self.assertEqual(
            [repr(it) for it in jmsel.jmespath(u'products[?product.name==\'\xa9\'].product.name')],
            [representation]
        )

    def test_check_text_argument_type_json(self):
        self.assertRaisesRegexp(TypeError, 'text argument should be of type',
                                self.sscls, b'{}', 'json')

    def test_extract_first_json(self):
        jsbody = u"""
        {
            "products": [
                {
                    "product": {
                        "img_url": [
                            "http://example.com/img1.png",
                            "http://example.com/img1.jpeg"
                        ],
                        "id": 1
                    }
                },
                {
                    "product": {
                        "img_url": [
                            "http://example.com/img2.png",
                            "http://example.com/img2.jpeg"
                        ],
                        "id": 2
                    }
                }
            ]
        }
        """
        jmsel = self.sscls(text=jsbody, type='json')
        self.assertEqual(jmsel.jmespath('products[].product.img_url').extract_first(),
                         jmsel.jmespath('products[].product.img_url').extract()[0])

        self.assertEqual(jmsel.jmespath("products[?product.id == `1`].product.img_url").extract_first(),
                         jmsel.jmespath("products[?product.id == `1`].product.img_url").extract()[0])

        self.assertEqual(jmsel.jmespath('products[1].product.img_url').extract_first(),
                         jmsel.jmespath('products[*].product.img_url').extract()[2])

        self.assertEqual(jmsel.jmespath("products[?product.id == 'does-not exist'].product.img_url").extract_first(),
                         None)

    def test_extract_first_default_json(self):
        jsbody = u"""
        {
            "products": [
                {
                    "product": {
                        "name": "\xa9",
                        "id": 1
                    }
                }]
        }
        """
        jmsel = self.sscls(text=jsbody, type='json')
        self.assertEqual(jmsel.jmespath('doesnot_exist.doesnot_exist').extract_first(default='missing'), 'missing')

    def test_re_first_json(self):
        jsbody = u"""
        {
            "products": [
                {
                    "product": {
                        "name": "ABC",
                        "id": 1
                    }
                },
                {
                    "product": {
                        "name": "XYZ",
                        "id": 2
                    }
                }
            ]
        }
        """
        jmsel = self.sscls(text=jsbody, type='json')

        self.assertEqual(jmsel.jmespath('*[].*.id').re_first('\d'),
                         jmsel.jmespath('*[].*.id').re('\d')[0])

        self.assertEqual(jmsel.jmespath('*[1].*.id').re_first('\d'),
                         jmsel.jmespath('*[].*.id').re('\d')[1])

        self.assertEqual(jmsel.jmespath('*[? product.id == `2`].*.name').re_first('\w+'),
                         jmsel.jmespath('*[].*.name').re('\w+')[1])
        self.assertEqual(jmsel.jmespath('*[].*.doesnot_exist').re_first('\d'), None)

    def test_select_unicode_query_json(self):
        jsbody = u"""
        {
            "products": [
                {
                    "product": {
                        "name": "\xa9",
                        "id": "1"
                    }
                }]
        }
        """
        jmsel = self.sscls(text=jsbody, type='json')
        self.assertEqual(jmsel.jmespath(u"products[?product.name == '\xa9'].product.id").extract(), [u'1'])

    def test_list_elements_type_json(self):
        jsbody = u'{"A": ["a"]}'
        assert isinstance(self.sscls(text=jsbody, type='json').jmespath("*")[0], self.sscls)

    def test_boolean_result_json(self):
        js = u"""
        {
            "order": {
                "shipped": "true",
                "delivered": "false"
            }
        }
        """
        jmsel = self.sscls(text=js, type='json')
        self.assertEqual(jmsel.jmespath('order.shipped').extract(), [u'true'])
        self.assertEqual(jmsel.jmespath('order.delivered').extract(), [u'false'])
        self.assertEquals(jmsel.jmespath('contains(`foobar`, `foo`)').extract(), [u'true'])

    def test_bool_json(self):
        jsbody = u"""
            {
                "products": [
                    {
                        "product": {
                            "name": "",
                            "id": 1
                        }
                    },
                    {
                        "product": {
                            "name": "nonempty",
                            "id": 2
                        }
                    }
                ]
            }
            """
        jmsel = self.sscls(text=jsbody, type='json')
        falsish = jmsel.jmespath('products[*].product.name')[0]
        self.assertEqual(falsish.extract(), u'')
        self.assertFalse(falsish)
        trueish = jmsel.jmespath('products[*].product.name')[1]
        self.assertEqual(trueish.extract(), u'nonempty')
        self.assertTrue(trueish)

    def test_text_or_json_obj_is_required_json(self):
        self.assertRaisesRegexp(ValueError,
                                'Selector needs either text or root argument',
                                self.sscls, **{'type': 'json'})

    def test_slicing_json(self):
        jsbody = u'[1, 2, 3, 4]'
        jmsel = self.sscls(text=jsbody, type='json')
        self.assertIsInstance(jmsel.jmespath('[]')[2], self.sscls)
        self.assertIsInstance(jmsel.jmespath('[]')[2:3], self.sscls.selectorlist_cls)
        self.assertIsInstance(jmsel.jmespath('[]')[:2], self.sscls.selectorlist_cls)
        self.assertEqual(jmsel.jmespath('[]')[2:3].extract(), [u'3'])
        self.assertEqual(jmsel.jmespath('[]')[1:3].extract(), [u'2', u'3'])

    def test_jmespath_returns_none_for_json_null(self):
        js = u'{"id": null}'
        jmsel = self.sscls(text=js, type='json')
        self.assertEqual(jmsel.jmespath('id').extract(), [])
        self.assertEqual(jmsel.jmespath('id').extract_first(), None)

    def test_nested_selectors_json(self):
        jsbody = u"""
        {
            "orders": [
                {
                    "order": {
                        "id": 1,
                        "items": [
                            {
                                "id": 62,
                                "quantity": 1,
                                "productId": 70
                            }
                        ]
                    }
                },
                {
                    "order": {
                        "id": 2,
                        "items": [
                            {
                                "id": 63,
                                "quantity": 1,
                                "productId": 73
                            },
                            {
                                "id": 64,
                                "quantity": 2,
                                "productId": 28
                            }
                        ]
                    }
                }
            ]
        }
        """
        jmsel = self.sscls(text=jsbody, type='json')
        ordertwo = jmsel.jmespath('orders[1]')
        self.assertEqual([json.dumps(json.loads(x), sort_keys=True)
                          for x in ordertwo.jmespath('order.items').extract()],
                         [u'{"id": 63, "productId": 73, "quantity": 1}',
                          u'{"id": 64, "productId": 28, "quantity": 2}'])

        self.assertEqual(ordertwo.jmespath('order.items[].id').extract(),
                         [u'63', u'64'])
        self.assertEqual(ordertwo.jmespath('*.quantity').extract(), [])

    def test_mixed_nested_selectors_html_to_json(self):
        js = u'{"id": "1", "name": "ABCD", "html": "<p>html content</p>"}'
        body = u'''<body>
                    <div id=1>not<span>me</span></div>
                    <div class="dos"><p>text</p><a href='#'>foo</a></div>
                    <div class="data" data-attr='{}'><p>json</p></div>
               </body>'''.format(js)
        sel = self.sscls(text=body)
        self.assertEqual(sel.xpath('//div[@id="1"]').css('span::text').extract(), [u'me'])
        self.assertEqual(sel.css('#1').xpath('./span/text()').extract(), [u'me'])
        self.assertEqual(sel.xpath('//div/@data-attr').jmespath('id').extract(), [u'1'])
        self.assertEqual(sel.css("div[data-attr]::attr(data-attr)").jmespath('id').extract(), [u'1'])
        self.assertEqual(sel.xpath('//div/@data-attr').jmespath('html').xpath('//p/text()').extract(),
                         [u'html content'])
        self.assertEqual(sel.xpath('//div/@data-attr').jmespath('html').css('p').extract(),
                         [u'<p>html content</p>'])

    def test_mixed_nested_selectors_json_to_html(self):
        body = u'''<body>
                    <div id=1>not<span>me</span></div>
                    <div class="dos"><p>text</p><a href='#'>foo</a></div>
               </body>'''
        mixed_body = u"""
        {{
            "id": 32,
            "name": "ABCD",
            "description": "{}"
        }}
        """.format(body.replace('"', '\\"').replace('\n', ''))
        sel = self.sscls(text=mixed_body, type='json')
        self.assertEqual(sel.jmespath('description').xpath('//div[@id="1"]').css('span::text').extract(), [u'me'])
        self.assertEqual(sel.jmespath('description').css('#1').xpath('./span/text()').extract(), [u'me'])

    def test_dont_strip_json(self):
        jmsel = self.sscls(text=u'[{"name": "fff: "}, {"name": "zzz"}]', type='json')
        self.assertEqual(jmsel.jmespath('[].name').extract(), [u'fff: ', u'zzz'])

    def test_re_json(self):
        jsbody = u"""
        {
            "order": {
                "detail1": "Title: ABC",
                "detail2": "Price: $30"
            }
        }
        """
        j = self.sscls(text=jsbody, type='json')
        self.assertEqual(j.jmespath('order.detail1').re('Title: (\w+)'),
                         ["ABC"])
        self.assertEqual(j.jmespath('order.detail2').re("Price: \$(\d+)"),
                         ["30"])

    def test_re_intl_json(self):
        jsbody = u'{"text": "Evento: cumplea\xf1os"}'
        j = self.sscls(text=jsbody, type='json')
        self.assertEqual(j.jmespath('text').re("Evento: (\w+)"), [u'cumplea\xf1os'])

    def test_selector_over_text_json(self):
        js = self.sscls(text=u'{"name": "abcd"}', type='json')
        self.assertEqual(js.extract(), u'{"name": "abcd"}')

    def test_invalid_jmespath(self):
        j = self.sscls(text=u'{["id": "1"}]')
        jmespath = '[?id == "1]'
        self.assertRaisesRegexp(ValueError, re.escape(jmespath), j.jmespath, jmespath)

    def test_invalid_jmespath_unicode(self):
        j = self.sscls(text=u'[{"id": "1"}]', type='json')
        jmespath = u"[?id == '\u0431ar]"
        encoded = jmespath if six.PY3 else jmespath.encode('unicode_escape')
        self.assertRaisesRegexp(ValueError, re.escape(encoded), j.jmespath, jmespath)

    def test_empty_bodies_shouldnt_raise_errors_json(self):
        self.sscls(text=u'', type='json').jmespath('*').extract()

    def test_invalid_json_should_not_raise_errors(self):
        text = u"{'id': '1'}"
        j = self.sscls(text=text, type='json')
        j.jmespath('id').extract()

    def test_type_for_invalid_json(self):
        text = u"{'id': '1'}"
        j = self.sscls(text=text, type='json')
        self.assertEqual(j.type, 'html')

    def test_warn_incompatible_methods_json(self):
        text = u'{"id": "1"}'
        jmsel = self.sscls(text=text, type='json')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            jmsel.remove_namespaces()
            jmsel.register_namespace("g", "http://base.google.com/ns/1.0")

        self.assertEqual(len(w), 2)
        self.assertEqual(
            str(w[0].message),
            'Cannot call this method when '
            'Selector is instantiated with type: `json`')

    def test_donot_warn_incompatible_methods(self):
        xml = u"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:atom="http://www.w3.org/2005/Atom" xml:lang="en-US" xmlns:media="http://search.yahoo.com/mrss/">
  <link atom:type="text/html">
  <link atom:type="application/atom+xml">
</feed>
"""
        sel = self.sscls(text=xml, type='xml')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            sel.remove_namespaces()
            sel.register_namespace("g", "http://base.google.com/ns/1.0")
        self.assertEqual(len(w), 0)


class ExsltTestCase(unittest.TestCase):

    sscls = Selector

    def test_regexp(self):
        """EXSLT regular expression tests"""
        body = u"""
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
            sel.xpath(
                '//input[re:test(@name, "[A-Z]+", "i")]').extract(),
            [x.extract() for x in sel.xpath('//input[re:test(@name, "[A-Z]+", "i")]')])
        self.assertEqual(
            [x.extract()
             for x in sel.xpath(
                 '//a[re:test(@href, "\.html$")]/text()')],
            [u'first link', u'second link'])
        self.assertEqual(
            [x.extract()
             for x in sel.xpath(
                 '//a[re:test(@href, "first")]/text()')],
            [u'first link'])
        self.assertEqual(
            [x.extract()
             for x in sel.xpath(
                 '//a[re:test(@href, "second")]/text()')],
            [u'second link'])


        # re:match() is rather special: it returns a node-set of <match> nodes
        #[u'<match>http://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.xml</match>',
        #u'<match>http</match>',
        #u'<match>www.bayes.co.uk</match>',
        #u'<match></match>',
        #u'<match>/xml/index.xml?/xml/utils/rechecker.xml</match>']
        self.assertEqual(
            sel.xpath('re:match(//a[re:test(@href, "\.xml$")]/@href,'
                      '"(\w+):\/\/([^/:]+)(:\d*)?([^# ]*)")/text()').extract(),
            [u'http://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.xml',
             u'http',
             u'www.bayes.co.uk',
             u'',
             u'/xml/index.xml?/xml/utils/rechecker.xml'])



        # re:replace()
        self.assertEqual(
            sel.xpath('re:replace(//a[re:test(@href, "\.xml$")]/@href,'
                      '"(\w+)://(.+)(\.xml)", "","https://\\2.html")').extract(),
            [u'https://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.html'])

    def test_set(self):
        """EXSLT set manipulation tests"""
        # microdata example from http://schema.org/Event
        body = u"""
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
            sel.xpath('''//div[@itemtype="http://schema.org/Event"]
                            //@itemprop''').extract(),
            [u'url',
             u'name',
             u'startDate',
             u'location',
             u'url',
             u'address',
             u'addressLocality',
             u'addressRegion',
             u'offers',
             u'lowPrice',
             u'offerCount']
        )

        self.assertEqual(sel.xpath('''
                set:difference(//div[@itemtype="http://schema.org/Event"]
                                    //@itemprop,
                               //div[@itemtype="http://schema.org/Event"]
                                    //*[@itemscope]/*/@itemprop)''').extract(),
                         [u'url', u'name', u'startDate', u'location', u'offers'])
