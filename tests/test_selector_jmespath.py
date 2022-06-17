# -*- coding: utf-8 -*-

import unittest

from parsel import Selector


class JMESPathTestCase(unittest.TestCase):
    def test_json_has_html(self):
        """Sometimes the information is returned in a json wrapper"""
        data = """
        {
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
            "html": "<div><a>AAA<br>Test</a>aaa</div><div><a>BBB</a>bbb<b>BbB</b></div>"
        }
        """
        sel = Selector(text=data)
        self.assertEqual(
            sel.jmespath("html").get(),
            "<div><a>AAA<br>Test</a>aaa</div>" "<div><a>BBB</a>bbb<b>BbB</b></div>",
        )
        self.assertEqual(
            sel.jmespath("html").xpath("//div/a/text()").getall(),
            ["AAA", "Test", "BBB"],
        )
        self.assertEqual(sel.jmespath("html").css("div > b").getall(), ["<b>BbB</b>"])
        self.assertEqual(sel.jmespath("content").jmespath("name.age").get(), 18)

    def test_html_has_json(self):
        html_text = """
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
            sel.xpath("//div/content/text()").jmespath("user[*].name").getall(),
            ["A", "B", "C", "D"],
        )
        self.assertEqual(
            sel.xpath("//div/content").jmespath("user[*].name").getall(),
            ["A", "B", "C", "D"],
        )
        self.assertEqual(sel.xpath("//div/content").jmespath("total").get(), 4)

    def test_jmespath_functions(self):
        data = """
        [
            {
              "name": "A",
              "age": {
                    "format_break": "No",
                    "value": "32"
                }
            },
            {
              "name": "B",
              "age": "32a"
            },
            {
              "name": "C",
              "age": ["22", "32", "55"]
            },
            {
              "name": "D",
              "age": "25"
            },
            {
              "name": "E",
              "age": 55
            }
        ]
        """
        sel = Selector(text=data)
        self.assertEqual(sel.jmespath("[*].age.value").get(), "32")
        self.assertEqual(
            sel.jmespath("[*].age").getall(),
            [
                {"format_break": "No", "value": "32"},
                "32a",
                ["22", "32", "55"],
                "25",
                55,
            ],
        )
        self.assertEqual(sel.jmespath("[*].age.to_number(@)").getall(), [25, 55])
        self.assertEqual(sel.jmespath("[*].age | [1]").get(), "32a")
        self.assertEqual(sel.jmespath("[*].age.to_number(@) | [1]").get(), 55)
        self.assertEqual(sel.jmespath("[*].age[].to_number(@)").get(), 22)

        self.assertEqual(
            sel.jmespath("[*].age.outer || [*].age.format_break").getall(), ["No"]
        )
