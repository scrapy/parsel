# -*- coding: utf-8 -*-
# @Time    : 2019/12/16 5:28 PM
# @Author  : EchoShoot
# @Email   : BiarFordlander@gmail.com
# @URL     : https://github.com/EchoShoot
# @File    : test_selector_jmespath.py
# @Explain :
import unittest

from parsel import Selector


class jmespathTestCase(unittest.TestCase):
    sscls = Selector

    def test_jmespath_with_json_contains_html(self):
        """ Sometimes the information is returned in a json wrapper """
        datas = u"""{
                    "content": [
                        {
                            "name": "A",
                            "value": "a"
                        },
                        {
                            "name": {
                                "age": 18
                            },
                            "value": "b"
                        },
                        {
                            "name": "C",
                            "value": "c"
                        },
                        {
                            "name": "<a>D</a>",
                            "value": "<div>d</div>"
                        }
                    ],
                    "html": [
                        "<div><a>AAA<br>Test</a>aaa</div><div><a>BBB</a>bbb<b>BbB</b><div/>"
                    ]
                }
                """
        sel = Selector(text=datas)
        self.assertEqual(sel.jmespath(u'html').get(),
                         u'<div><a>AAA<br>Test</a>aaa</div>'
                         u'<div><a>BBB</a>bbb<b>BbB</b><div/>')
        self.assertEqual(sel.jmespath(u'html').xpath(u'//div/a/text()').getall(),
                         [u'AAA', u'Test', u'BBB'])
        self.assertEqual(sel.jmespath(u'html').xpath(u'//div/b').getall(),
                         [u'<b>BbB</b>'])
        self.assertEqual(sel.jmespath(u'content').jmespath(u'name.age').get(),
                         18)

    def test_jmespath_with_html_contains_json(self):
        html_text = u"""
        <div>
            <h1>Information</h1>
            <content>
            {
              "user": [
                        {
                                  "name": "A",
                                  "age": 18
                        },
                        {
                                  "name": "B",
                                  "age": 32
                        },
                        {
                                  "name": "C",
                                  "age": 22
                        },
                        {
                                  "name": "D",
                                  "age": 25
                        }
              ],
              "total": 4,
              "status": "ok"
            }
            </content>
        </div>
        """
        sel = Selector(text=html_text)
        self.assertEqual(
            sel.xpath(u'//div/content/text()').jmespath(u'user[*].name').getall(),
            [u'A', u'B', u'C', u'D'])
        self.assertEqual(
            sel.xpath(u'//div/content').jmespath(u'user[*].name').getall(),
            [u'A', u'B', u'C', u'D'])
        self.assertEqual(
            sel.xpath(u'//div/content').jmespath(u'total').get(), 4)
