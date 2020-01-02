# -*- coding: utf-8 -*-
# @Time    : 2019/12/16 5:28 PM
# @Author  : EchoShoot
# @Email   : BiarFordlander@gmail.com
# @URL     : https://github.com/EchoShoot
# @File    : test_selector_jpath.py
# @Explain :
import unittest
import json

from parsel import Selector


class JpathTestCase(unittest.TestCase):
    sscls = Selector

    def test_jpath_with_json_contains_html(self):
        """ Sometimes the information is returned in a json wrapper """
        datas = {
            'content': [
                {'name': 'A', 'value': 'a'},
                {'name': {'age': 18}, 'value': 'b'},
                {'name': 'C', 'value': 'c'},
                {'name': '<a>D</a>', 'value': '<div>d</div>'},
            ],
            'html': ['<div><a>AAA<br>鬼打墙</a>aaa</div><div><a>BBB</a>bbb<b>BbB</b><div/>'],
        }
        sel = Selector(text=json.dumps(datas))
        self.assertEqual(sel.jpath('html').get(), '<div><a>AAA<br>鬼打墙</a>aaa</div><div><a>BBB</a>bbb<b>BbB</b><div/>')
        self.assertEqual(sel.jpath('html').xpath('//div/a/text()').getall(), ['AAA', '鬼打墙', 'BBB'])
        self.assertEqual(sel.jpath('html').xpath('//div/b').getall(), ['<b>BbB</b>'])
        self.assertEqual(sel.jpath('content').jpath('name.age').get(), 18)

    def test_jpath_with_html_contains_json(self):
        html_text = """
        <div>
            <h1>Information</h1>
            <jsondata>
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
            </jsondata>
        </div>
        """
        sel = Selector(text=html_text)
        self.assertEqual(sel.xpath('//div/jsondata/text()').jpath('user[*].name').getall(), ['A', 'B', 'C', 'D'])
        self.assertEqual(sel.xpath('//div/jsondata').jpath('user[*].name').getall(), ['A', 'B', 'C', 'D'])
        self.assertEqual(sel.xpath('//div/jsondata').jpath('total').get(), 4)

