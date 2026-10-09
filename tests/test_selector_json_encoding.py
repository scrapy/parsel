from __future__ import annotations

import json
from typing import Any

import pytest

from parsel import Selector


@pytest.mark.parametrize("encoding", ["latin-1", "utf-8-sig", "utf-16", "utf-32"])
@pytest.mark.parametrize("input_type", [None, "json"])
@pytest.mark.parametrize("as_bytearray", [False, True])
@pytest.mark.parametrize("data", [{"name": "caf\u00e9"}, [{"name": "caf\u00e9"}]])
def test_json_body_encoding(
    encoding: str, input_type: str | None, as_bytearray: bool, data: Any
) -> None:
    body = json.dumps(data, ensure_ascii=False).encode(encoding)
    selector = Selector(
        body=bytearray(body) if as_bytearray else body,
        encoding=encoding,
        type=input_type,
    )

    assert selector.type == "json"
    assert selector.get() == data
    query = "name" if isinstance(data, dict) else "[0].name"
    assert selector.jmespath(query).get() == "caf\u00e9"


@pytest.mark.parametrize("encoding", ["utf-16", "utf-32"])
def test_json_body_default_encoding_autodetection(encoding: str) -> None:
    data = {"name": "caf\u00e9"}
    selector = Selector(body=json.dumps(data, ensure_ascii=False).encode(encoding))

    assert selector.type == "json"
    assert selector.get() == data


@pytest.mark.parametrize("encoding", ["latin-1", "utf-8-sig", "utf-16", "utf-32"])
def test_invalid_json_body_encoding(encoding: str) -> None:
    body = "<p>caf\u00e9</p>".encode(encoding)

    assert Selector(body=body, encoding=encoding, type="json").get() is None
    selector = Selector(body=body, encoding=encoding)
    assert selector.type == "html"
    assert selector.css("p::text").get() == "caf\u00e9"
