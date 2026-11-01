from __future__ import annotations

import json

import pytest

from parsel import Selector


@pytest.mark.parametrize("value", ["", "123", "true", "null", '{"a": 1}', "plain text"])
@pytest.mark.parametrize("source", ["text", "body", "root"])
@pytest.mark.parametrize(("method", "query"), [("jmespath", "@"), ("jsonpath", "$")])
def test_queries_preserve_json_string_values(
    value: str, source: str, method: str, query: str
) -> None:
    if source == "text":
        selector = Selector(text=json.dumps(value), type="json")
    elif source == "body":
        selector = Selector(body=json.dumps(value).encode(), type="json")
    else:
        selector = Selector(root=value, type="json")
    assert selector.get() == value
    assert getattr(selector, method)(query).get() == value


@pytest.mark.parametrize("type_", ["text", "html", "xml"])
def test_embedded_json_keeps_being_decoded(type_: str) -> None:
    text = '{"a": 1}' if type_ == "text" else '<script>{"a": 1}</script>'
    selector = Selector(text=text, type=type_)
    if type_ == "html":
        selector = selector.xpath("//script")[0]
    assert selector.jmespath("a").get() == 1
    assert selector.jsonpath("$.a").get() == 1
