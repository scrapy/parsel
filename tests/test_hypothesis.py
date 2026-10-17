from __future__ import annotations

import json
from typing import Any, TypeAlias

import pytest
from hypothesis import assume, example, given
from hypothesis import strategies as st

from parsel import Selector
from parsel.utils import flatten, shorten

json_values: st.SearchStrategy[object] = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=20,
)
json_documents: st.SearchStrategy[object] = st.dictionaries(
    st.text(), json_values
) | st.lists(json_values)

class_names: st.SearchStrategy[str] = st.text(
    st.characters(codec="ascii", categories=["L", "N"]), min_size=1, max_size=4
)

# A tree is either a text leaf or the list of children of an element.
_Tree: TypeAlias = "str | list[_Tree]"
trees: st.SearchStrategy[_Tree] = st.recursive(
    st.text(st.characters(codec="ascii", categories=["L"]), max_size=3),
    lambda children: st.lists(children, max_size=3),
    max_leaves=12,
)


def _is_json_document(text: str) -> bool:
    try:
        return isinstance(json.loads(text), (dict, list))
    except ValueError:
        return False


@pytest.mark.xfail(
    reason=(
        "text= strips all Unicode whitespace from the ends, UTF-8 body= only"
        " ASCII whitespace; text= strips the ends before removing NULs,"
        " UTF-8 body= after"
    ),
    strict=True,
)
@given(st.text(min_size=1))
@example("\u3000")
@example("0\r\x00")
def test_text_vs_body_utf8(text: str) -> None:
    sel_text = Selector(text=text)
    sel_body = Selector(body=text.encode("utf-8"))
    assert sel_text.type == sel_body.type
    assert sel_text.get() == sel_body.get()


@pytest.mark.parametrize("encoding", ["latin-1", "cp1252", "utf-16", "utf-16-le"])
@given(data=st.data())
def test_text_vs_body_other_encodings(encoding: str, data: st.DataObject) -> None:
    text = data.draw(st.text(st.characters(codec=encoding), min_size=1))
    # JSON is only detected in UTF-8 bodies, test_json_body_any_encoding()
    # covers JSON with other encodings.
    assume(not _is_json_document(text))
    sel_text = Selector(text=text)
    sel_body = Selector(body=text.encode(encoding), encoding=encoding)
    assert sel_text.type == sel_body.type
    assert sel_text.get() == sel_body.get()


@pytest.mark.parametrize(
    "encoding",
    [
        "utf-8",
        *(
            pytest.param(
                encoding,
                marks=pytest.mark.xfail(
                    reason="JSON is only parsed from UTF-8 bodies, other encodings give a None root",
                    strict=True,
                ),
            )
            for encoding in ("utf-8-sig", "utf-16", "latin-1")
        ),
    ],
)
@given(obj=json_documents)
@example(obj={})
def test_json_body_any_encoding(encoding: str, obj: object) -> None:
    sel = Selector(
        body=json.dumps(obj).encode(encoding), encoding=encoding, type="json"
    )
    assert sel.root == obj


@given(json_documents)
def test_json_detection_roundtrip(obj: object) -> None:
    text = json.dumps(obj)
    for sel in (Selector(text=text), Selector(body=text.encode())):
        assert sel.type == "json"
        # Comparing jmespath("@") results instead would not work, as list
        # results are flattened.
        assert sel.root == obj


@given(json_values)
def test_json_explicit_type_roundtrip(obj: object) -> None:
    text = json.dumps(obj)
    for sel in (
        Selector(text=text, type="json"),
        Selector(body=text.encode(), type="json"),
    ):
        assert sel.type == "json"
        assert sel.root == obj


@pytest.mark.parametrize(
    "from_body",
    [
        pytest.param(
            False,
            marks=pytest.mark.xfail(
                reason="JSON detection from text= does not skip a BOM",
                strict=True,
            ),
        ),
        True,
    ],
)
@given(json_documents)
@example({})
def test_json_detection_bom(from_body: bool, obj: object) -> None:
    text = "\ufeff" + json.dumps(obj)
    sel = Selector(body=text.encode()) if from_body else Selector(text=text)
    assert sel.type == "json"
    assert sel.root == obj


@pytest.mark.xfail(
    reason="::attr() does not lower-case the attribute name in HTML, unlike [attr]",
    strict=True,
)
@given(
    st.text(st.characters(codec="ascii", categories=["L"]), min_size=1, max_size=5),
    # NULs are removed from the input, and the parser turns CR into LF.
    st.text(st.characters(codec="ascii", exclude_characters='"&<\x00\r'), max_size=10),
)
@example("A", "")
def test_css_attr_pseudo_element(name: str, value: str) -> None:
    sel = Selector(text=f'<p {name}="{value}">x</p>')
    assert sel.css(f"p[{name}]")
    assert sel.css(f"p::attr({name})").get() == value


@given(
    st.lists(class_names, max_size=5),
    st.text(st.sampled_from(" \t\n\r\x0c"), min_size=1, max_size=3),
    class_names,
)
def test_has_class(classes: list[str], separator: str, query: str) -> None:
    sel = Selector(text=f'<p class="{separator.join(classes)}">x</p>')
    assert bool(sel.xpath("//p[has-class($q)]", q=query)) == (query in classes)


def _render_tree(tree: _Tree) -> tuple[str, str, list[tuple[int, int]]]:
    """Return the markup of *tree*, its text, and for every element, in
    document order, the span of its text within that text.

    The element K is rendered as ``<e id="nK">``.
    """
    markup: list[str] = []
    text: list[str] = []
    spans: list[tuple[int, int]] = []
    length = 0

    def render(node: _Tree) -> None:
        nonlocal length
        if isinstance(node, str):
            markup.append(node)
            text.append(node)
            length += len(node)
            return
        index = len(spans)
        start = length
        spans.append((start, start))
        markup.append(f'<e id="n{index}">')
        for child in node:
            render(child)
        markup.append("</e>")
        spans[index] = (start, length)

    render(tree)
    return "".join(markup), "".join(text), spans


@pytest.mark.parametrize("type_", ["html", "xml"])
@given(children=st.lists(trees, max_size=4), data=st.data())
def test_drop_keeps_surrounding_text(
    type_: str, children: list[_Tree], data: st.DataObject
) -> None:
    markup, text, spans = _render_tree(children)
    sel = Selector(text=f"<root>{markup}</root>", type=type_)
    assert "".join(sel.root.itertext()) == text
    index = data.draw(st.integers(min_value=0, max_value=len(spans) - 1))
    sel.xpath("//e[@id=$id]", id=f"n{index}").drop()
    start, end = spans[index]
    assert "".join(sel.root.itertext()) == text[:start] + text[end:]


@given(st.text(), st.integers(min_value=0, max_value=50))
def test_shorten_length(text: str, width: int) -> None:
    assert len(shorten(text, width)) == min(len(text), width)


@given(
    st.lists(
        st.recursive(
            st.integers(),
            lambda children: st.lists(children) | st.tuples(children, children),
        )
    )
)
def test_flatten_idempotent(x: list[Any]) -> None:
    assert flatten(flatten(x)) == flatten(x)


@given(st.text())
def test_text_type_roundtrip(text: str) -> None:
    assert Selector(text=text, type="text").get() == text


# body=b"" is rejected.
@given(st.text(min_size=1))
def test_text_type_roundtrip_body(text: str) -> None:
    assert Selector(body=text.encode(), type="text").get() == text
