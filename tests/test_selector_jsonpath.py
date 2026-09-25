from __future__ import annotations

import builtins
import importlib.util
from typing import TYPE_CHECKING, Any, cast

import pytest

from parsel import Selector
from parsel.selector import JSONPathError, _compile_jsonpath, _jsonpath_backend

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestJSONPath:
    def test_json_has_html(self) -> None:
        """Sometimes the information is returned in a json wrapper"""
        sel = Selector(text='{"html": "<div><a>a<br>b</a>c</div><div><b>f</b></div>"}')
        assert (
            sel.jsonpath("$.html").get()
            == "<div><a>a<br>b</a>c</div><div><b>f</b></div>"
        )
        assert sel.jsonpath("$.html").xpath("//div/a/text()").getall() == ["a", "b"]
        assert sel.jsonpath("$.html").css("div > b").getall() == ["<b>f</b>"]

    def test_html_has_json(self) -> None:
        html_text = """
        <div>
            <content>{"user": [{"name": "A"}, {"name": "B"}], "total": 2}</content>
        </div>
        """
        sel = Selector(text=html_text)
        assert sel.xpath("//div/content/text()").jsonpath(
            "$.user[*].name"
        ).getall() == [
            "A",
            "B",
        ]
        assert sel.xpath("//div/content").jsonpath("$.user[*].name").getall() == [
            "A",
            "B",
        ]
        assert cast("int", sel.xpath("//div/content").jsonpath("$.total").get()) == 2

    def test_jsonpath_with_re(self) -> None:
        sel = Selector(text='{"user": [{"name": "A", "age": 18}]}')

        assert sel.jsonpath("$.user[*].name").re(r"(\w+)") == ["A"]

        with pytest.raises(TypeError):
            sel.jsonpath("$.user[*].age").re(r"(\d+)")

        assert sel.jsonpath("$.unavailable").re(r"(\d+)") == []
        assert sel.jsonpath("$.unavailable").re_first(r"(\d+)") is None

    def test_no_match(self) -> None:
        sel = Selector(text='{"a": 1}')
        assert sel.jsonpath("$.b").getall() == []
        assert sel.jsonpath("$.b").get() is None

    def test_not_json(self) -> None:
        """A document with no JSON in it yields no results rather than an
        error."""
        sel = Selector(text="<html><body><p>Not JSON</p></body></html>")
        assert sel.jsonpath("$.a").getall() == []

    def test_null_value(self) -> None:
        """A JSON null is a match, unlike a missing key."""
        sel = Selector(text='{"a": null}')
        assert len(sel.jsonpath("$.a")) == 1
        assert sel.jsonpath("$.a")[0].root is None
        assert len(sel.jsonpath("$.b")) == 0

    def test_descendants(self) -> None:
        """Recursive descent has no JMESPath equivalent."""
        sel = Selector(text='{"a": {"price": 1, "b": {"price": 2, "c": {"price": 3}}}}')
        assert cast("Sequence[int]", sel.jsonpath("$..price").getall()) == [1, 2, 3]

    def test_filter(self) -> None:
        sel = Selector(
            text='{"products": [{"name": "A", "price": 10},'
            ' {"name": "B", "price": 30}]}'
        )
        assert sel.jsonpath("$.products[?@.price > 20].name").getall() == ["B"]

    def test_invalid_query(self) -> None:
        """Every backend reports query errors as the same exception."""
        sel = Selector(text="{}")
        with pytest.raises(JSONPathError):
            sel.jsonpath("$.[")

    def test_extensions_disabled(self) -> None:
        """Only RFC 9535 syntax is accepted, not the extensions that
        python-jsonpath enables by default."""
        sel = Selector(text='{"a": {"b": 1}}')
        for query in ("$.a.~", "$.a[~?@.b]", "$.a[?# == 'b']", "$.a.b | $.a"):
            with pytest.raises(JSONPathError):
                sel.jsonpath(query)

    def test_evaluation_error(self) -> None:
        """Errors raised while running a query are reported as
        :class:`JSONPathError` too."""
        depth = 150
        sel = Selector(text='{"a":' * depth + "1" + "}" * depth)
        with pytest.raises(JSONPathError):
            sel.jsonpath("$..a")

    def test_index_selector_on_object(self) -> None:
        """RFC 9535 index selectors do not match string keys."""
        sel = Selector(text='[{"0": 5}]')
        assert sel.jsonpath("$[?@[0] == 5]").getall() == []

    def test_selector_list(self) -> None:
        sel = Selector(text='[{"a": [1, 2]}, {"a": [3]}]')
        assert cast(
            "Sequence[int]", sel.jsonpath("$[*]").jsonpath("$.a[*]").getall()
        ) == [
            1,
            2,
            3,
        ]

    def test_extra_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_import = builtins.__import__

        def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name in {"jsonpath", "jsonpath_rfc9535"}:
                raise ImportError(name)
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        _compile_jsonpath.cache_clear()
        _jsonpath_backend.cache_clear()
        try:
            with pytest.raises(
                ImportError, match=r"pip install parsel\[jsonpath-rfc9535\]"
            ):
                Selector(text="{}").jsonpath("$.a")
        finally:
            _jsonpath_backend.cache_clear()

    def test_compilation_is_cached(self) -> None:
        _compile_jsonpath.cache_clear()
        Selector(text="{}").jsonpath("$.cached")
        Selector(text="{}").jsonpath("$.cached")
        assert _compile_jsonpath.cache_info().hits == 1

    def test_backend(self) -> None:
        """jsonpath-rfc9535 takes precedence over python-jsonpath."""
        expected = (
            "jsonpath_rfc9535"
            if importlib.util.find_spec("jsonpath_rfc9535")
            else "jsonpath"
        )
        _jsonpath_backend.cache_clear()
        _, _, backend_error = _jsonpath_backend()
        assert backend_error.__module__.split(".")[0] == expected
