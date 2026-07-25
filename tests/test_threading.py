# Tests that use parsel from multiple threads concurrently, mostly for free-threaded Python tests
#
# The contract covered here: every thread may parse, query and mutate its own
# tree, and any number of threads may read a tree shared between them.
# Mutating a shared tree from several threads at once is not supported by
# lxml, so it is deliberately not tested. The same goes for mutating the state
# of a shared Selector, e.g. with register_namespace().

from __future__ import annotations

import json
import sys
import sysconfig
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

import pytest

from parsel import Selector
from parsel.csstranslator import GenericTranslator, HTMLTranslator
from parsel.xpathfuncs import set_xpathfunc

if TYPE_CHECKING:
    from collections.abc import Callable

pytestmark = pytest.mark.timeout(60, method="thread")

THREAD_COUNT = 8
ITEM_COUNT = 100
# How many times each thread repeats its workload. Query-only workloads are
# cheap enough to repeat more often, which widens the window for a race.
QUERY_ITERATIONS = 100
PARSE_ITERATIONS = 25
# How long a thread waits for the other threads to reach the starting barrier.
# Only exceeded if some thread never gets there, in which case failing is much
# better than hanging until the timeout of the whole test kills the process.
BARRIER_TIMEOUT = 30


def gil_enabled() -> bool:
    """Whether the GIL is enabled."""
    if sys.version_info >= (3, 13):
        return sys._is_gil_enabled()
    return True


# lxml 7.0.0a3 iterates the global XPath function registry without locking
# (_BaseContext.registerGlobalFunctions), so registering a function while any
# thread evaluates XPath breaks that evaluation, with either "dictionary
# changed size during iteration" or "Unregistered function". Not strict, as
# it is a race and may go unnoticed on a busy or single-core machine.
xfail_concurrent_set_xpathfunc = pytest.mark.xfail(
    not gil_enabled(),
    reason="set_xpathfunc() is not free-threading-safe with lxml 7.0.0a3",
)


def run_in_threads(func: Callable[[int], None]) -> None:
    """Run *func* in THREAD_COUNT threads at once, given the thread index.

    A barrier makes all threads start their work at the same time, to
    maximize the chance of hitting race conditions. Exceptions raised in
    threads, including assertion failures, are re-raised; if more than one
    thread fails, all of the failures are reported, as which threads lost a
    race is often the most useful part of the signal.
    """
    barrier = threading.Barrier(THREAD_COUNT, timeout=BARRIER_TIMEOUT)

    def run(index: int) -> None:
        barrier.wait()
        func(index)

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = [executor.submit(run, index) for index in range(THREAD_COUNT)]
        errors = [
            (index, exception)
            for index, future in enumerate(futures)
            if (exception := future.exception()) is not None
        ]

    if not errors:
        return
    if len(errors) == 1:
        raise errors[0][1]
    report = "\n\n".join(
        f"thread {index}:\n{''.join(traceback.format_exception(exception)).rstrip()}"
        for index, exception in errors
    )
    pytest.fail(
        f"{len(errors)} of {THREAD_COUNT} threads failed:\n\n{report}", pytrace=False
    )


TITLE = "Ítems ☃"

HTML_ITEMS = "".join(
    f'<li class="item i{index}" data-index="{index}">'
    f'<a href="/item/{index}">Item {index}</a></li>'
    for index in range(ITEM_COUNT)
)
HTML_TEXT = (
    f'<html><body><h1 class="title">{TITLE}</h1>'
    f'<ul id="items">{HTML_ITEMS}</ul></body></html>'
)


XML_ITEMS = "".join(
    f'<item id="{index}"><name>Item {index}</name></item>'
    for index in range(ITEM_COUNT)
)
XML_TEXT = (
    '<?xml version="1.0" encoding="utf-8"?>'
    f"<catalog><title>{TITLE}</title>{XML_ITEMS}</catalog>"
)


NS_XML_ITEMS = "".join(
    f'<item m:id="{index}"><name>Item {index}</name></item>'
    for index in range(ITEM_COUNT)
)
NS_XML_TEXT = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<catalog xmlns="http://example.com/catalog" xmlns:m="http://example.com/meta">'
    f"<title>{TITLE}</title>{NS_XML_ITEMS}</catalog>"
)
NS_XML_PREFIXES = {
    "c": "http://example.com/catalog",
    "m": "http://example.com/meta",
}


JSON_NAMES = [f"Item {index}" for index in range(ITEM_COUNT)]
JSON_TEXT = json.dumps({"items": [{"name": name} for name in JSON_NAMES]})


def test_gil_disabled() -> None:
    """Fail if the GIL is enabled while running a free-threaded build.

    Importing an extension module built without free-threading support
    re-enables the GIL at run time.
    """
    if not sysconfig.get_config_var("Py_GIL_DISABLED"):
        pytest.skip("not a free-threaded build")
    assert not gil_enabled()


def test_shared_selector_reads() -> None:
    """Query a single, shared Selector and its lxml tree from all threads."""
    selector = Selector(text=HTML_TEXT)
    expected_hrefs = [f"/item/{index}" for index in range(ITEM_COUNT)]
    expected_texts = [f"Item {index}" for index in range(ITEM_COUNT)]

    def read(index: int) -> None:
        for _ in range(QUERY_ITERATIONS):
            assert selector.css("h1.title::text").get() == TITLE
            assert selector.css("li.item a::attr(href)").getall() == expected_hrefs
            assert selector.xpath("//li/a/text()").getall() == expected_texts
            assert selector.css(f"li.i{index} a::text").re(r"Item (\d+)") == [
                str(index)
            ]
            assert selector.xpath("//ul").attrib["id"] == "items"
            assert (
                selector.css(f"li.i{index} > a").get()
                == f'<a href="/item/{index}">Item {index}</a>'
            )

    run_in_threads(read)


@pytest.mark.parametrize(
    "selector_kwargs",
    [
        {"text": HTML_TEXT},
        {"body": HTML_TEXT.encode(), "encoding": "utf-8"},
    ],
    ids=["text", "body"],
)
def test_parse_html_per_thread(selector_kwargs: dict[str, Any]) -> None:
    """Parse and query an independent HTML document in every thread."""

    def parse(index: int) -> None:
        for _ in range(PARSE_ITERATIONS):
            selector = Selector(**selector_kwargs)
            assert selector.type == "html"
            assert selector.css("h1.title::text").get() == TITLE
            assert selector.css(f"li.i{index} a::text").get() == f"Item {index}"
            assert len(selector.css("li.item")) == ITEM_COUNT

    run_in_threads(parse)


def test_parse_xml_per_thread() -> None:
    """Parse and query an independent XML document in every thread."""

    def parse(index: int) -> None:
        for _ in range(PARSE_ITERATIONS):
            selector = Selector(text=XML_TEXT, type="xml")
            assert selector.type == "xml"
            assert selector.xpath("//title/text()").get() == TITLE
            name = selector.xpath(f'//item[@id="{index}"]/name/text()').get()
            assert name == f"Item {index}"
            assert selector.css(f'item[id="{index}"] > name::text').get() == name
            assert len(selector.xpath("//item")) == ITEM_COUNT

    run_in_threads(parse)


def test_shared_namespaced_selector() -> None:
    """Query a shared XML Selector using namespace prefixes from all threads.

    Resolving a prefix to a namespace URI is a part of every query here, both
    for the prefixes passed to xpath() and for the ones of the document.
    """
    selector = Selector(text=NS_XML_TEXT, type="xml")

    def query(index: int) -> None:
        for _ in range(QUERY_ITERATIONS):
            name = selector.xpath(
                f'//c:item[@m:id="{index}"]/c:name/text()', namespaces=NS_XML_PREFIXES
            ).get()
            assert name == f"Item {index}"
            assert (
                selector.xpath("//c:title/text()", namespaces=NS_XML_PREFIXES).get()
                == TITLE
            )

    run_in_threads(query)


def test_shared_text_selector() -> None:
    """Query a single, shared Selector of the text type from all threads.

    Such a Selector parses its text again on every query, so one shared
    object drives concurrent parsing, unlike the tests above where every
    thread parses its own document.
    """
    selector = Selector(text=HTML_TEXT, type="text")
    assert selector.type == "text"

    def query(index: int) -> None:
        for _ in range(PARSE_ITERATIONS):
            assert selector.css(f"li.i{index} a::text").get() == f"Item {index}"
            assert selector.xpath("//h1/text()").get() == TITLE

    run_in_threads(query)


def test_has_class_shared_selector() -> None:
    """Call the global has-class XPath function on a shared Selector.

    Evaluation crosses the libxml2-to-Python callback boundary in every
    thread at the same time.
    """
    selector = Selector(text=HTML_TEXT)

    def query(index: int) -> None:
        for _ in range(QUERY_ITERATIONS):
            texts = selector.xpath(f'//li[has-class("i{index}")]/a/text()').getall()
            assert texts == [f"Item {index}"]

    run_in_threads(query)


def _html_cache_queries(value: int) -> list[tuple[str, str]]:
    return [
        (f"li.i{value} > a::text", f"Item {value}"),
        (f"ul#items li.i{value} a::attr(href)", f"/item/{value}"),
        (f"body li.i{value}::attr(data-index)", str(value)),
    ]


def _xml_cache_queries(value: int) -> list[tuple[str, str]]:
    return [
        (f'item[id="{value}"] > name::text', f"Item {value}"),
        (f'catalog item[id="{value}"] name::text', f"Item {value}"),
        (f'catalog > item[id="{value}"]::attr(id)', str(value)),
    ]


# css_to_xpath is decorated per class, so HTMLTranslator and GenericTranslator
# own two independent caches and both need exercising.
@pytest.mark.parametrize(
    ("translator_cls", "selector_kwargs", "queries_factory"),
    [
        (HTMLTranslator, {"text": HTML_TEXT}, _html_cache_queries),
        (
            GenericTranslator,
            {"text": XML_TEXT, "type": "xml"},
            _xml_cache_queries,
        ),
    ],
    ids=["html", "xml"],
)
def test_css_to_xpath_cache(
    translator_cls: type[GenericTranslator | HTMLTranslator],
    selector_kwargs: dict[str, Any],
    queries_factory: Callable[[int], list[tuple[str, str]]],
) -> None:
    """Exercise a CSS-to-XPath translation cache with distinct expressions.

    The expressions outnumber the cache entries, forcing concurrent cache
    insertions and evictions.
    """
    cache_info = translator_cls.css_to_xpath.cache_info
    maxsize = cache_info().maxsize
    assert maxsize is not None
    shape_count = len(queries_factory(0))
    # Enough values to overflow the cache. The values are item indexes, so
    # they cannot go past ITEM_COUNT.
    value_count = min(maxsize // shape_count + 1, ITEM_COUNT)
    assert shape_count * value_count > maxsize, (
        "not enough distinct expressions to overflow the cache, "
        "increase ITEM_COUNT or add expression shapes"
    )

    selector = Selector(**selector_kwargs)

    def query(index: int) -> None:
        for offset in range(value_count):
            # Each thread walks the same expression cycle from a different
            # starting point, so threads collide at varying points.
            value = (index * 37 + offset) % value_count
            for css, expected in queries_factory(value):
                assert selector.css(css).get() == expected

    run_in_threads(query)

    assert cache_info().currsize == maxsize


def _unique_xpathfunc_name() -> str:
    # Unique per call rather than per thread index, as pytest-run-parallel may
    # run the same test in several threads at once.
    return f"parsel-test-{uuid.uuid4().hex}"


def _xpathfunc_true(_context: Any) -> bool:
    return True


@xfail_concurrent_set_xpathfunc
def test_set_xpathfunc_per_thread() -> None:
    """Register, use and unregister a global XPath function in every thread.

    Every thread uses a unique function name, so concurrent mutation of the
    global lxml function namespace with distinct keys must be safe.
    """
    selector = Selector(text="<p>word</p>")

    def use_custom_function(_index: int) -> None:
        fname = _unique_xpathfunc_name()
        for _ in range(QUERY_ITERATIONS):
            set_xpathfunc(fname, _xpathfunc_true)
            try:
                assert selector.xpath(f"//p[{fname}()]/text()").get() == "word"
            finally:
                set_xpathfunc(fname, None)

    run_in_threads(use_custom_function)


@xfail_concurrent_set_xpathfunc
def test_set_xpathfunc_during_queries() -> None:
    """Mutate the global XPath function namespace while other threads read it.

    Half of the threads register and unregister function names of their own in
    the namespace where lxml looks up has-class(), while the other half keep
    calling has-class().
    """
    selector = Selector(text=HTML_TEXT)

    def churn() -> None:
        fname = _unique_xpathfunc_name()
        for _ in range(QUERY_ITERATIONS):
            set_xpathfunc(fname, _xpathfunc_true)
            try:
                assert selector.xpath(f"//h1[{fname}()]/text()").get() == TITLE
            finally:
                set_xpathfunc(fname, None)

    def query(index: int) -> None:
        for _ in range(QUERY_ITERATIONS):
            texts = selector.xpath(f'//li[has-class("i{index}")]/a/text()').getall()
            assert texts == [f"Item {index}"]

    def churn_or_query(index: int) -> None:
        if index % 2:
            churn()
        else:
            query(index)

    run_in_threads(churn_or_query)


def test_drop_per_thread() -> None:
    """Mutate a thread-local tree while other threads mutate their own."""

    def drop(index: int) -> None:
        for _ in range(PARSE_ITERATIONS):
            selector = Selector(text=HTML_TEXT)
            for item in selector.css(f"li.i{index}"):
                item.drop()
            assert len(selector.css("li.item")) == ITEM_COUNT - 1

    run_in_threads(drop)


def test_remove_namespaces_per_thread() -> None:
    """Remove the namespaces of a thread-local tree in every thread.

    remove_namespaces() renames every namespaced tag and attribute and then
    calls the lxml namespace cleanup.
    """

    def remove(index: int) -> None:
        for _ in range(PARSE_ITERATIONS):
            selector = Selector(text=NS_XML_TEXT, type="xml")
            assert selector.xpath("//item").getall() == []
            selector.remove_namespaces()
            assert len(selector.xpath("//item")) == ITEM_COUNT
            assert selector.xpath("//title/text()").get() == TITLE
            name = selector.xpath(f'//item[@id="{index}"]/name/text()').get()
            assert name == f"Item {index}"

    run_in_threads(remove)


def test_jmespath_shared_selector() -> None:
    """Query a single, shared JSON Selector from all threads.

    The document is parsed once, so all threads search the same object tree.
    """
    selector = Selector(text=JSON_TEXT)
    assert selector.type == "json"
    assert not isinstance(selector.root, str)

    def query(index: int) -> None:
        for _ in range(QUERY_ITERATIONS):
            assert selector.jmespath(f"items[{index}].name").get() == f"Item {index}"
            assert selector.jmespath("items[*].name").getall() == JSON_NAMES

    run_in_threads(query)


def test_jmespath_shared_json_string_selector() -> None:
    """Query a shared Selector that got JSON as a string root from all threads.

    Such a Selector parses that string again on every query, so one shared
    object drives concurrent JSON parsing, like test_shared_text_selector()
    does for markup.
    """
    selector = Selector(root=JSON_TEXT)
    assert selector.type == "json"
    assert isinstance(selector.root, str)

    def query(index: int) -> None:
        for _ in range(PARSE_ITERATIONS):
            assert selector.jmespath(f"items[{index}].name").get() == f"Item {index}"
            assert selector.jmespath("items[*].name").getall() == JSON_NAMES

    run_in_threads(query)


def test_jmespath_shared_html_selector() -> None:
    """Run JMESPath on a shared HTML Selector from all threads.

    The text of the node is parsed as JSON on every query, on top of the
    concurrent reads of the shared lxml tree that provides that text.
    """
    selector = Selector(text=f"<html><body><script>{JSON_TEXT}</script></body></html>")
    script = selector.css("script")[0]
    assert script.type == "html"

    def query(index: int) -> None:
        for _ in range(PARSE_ITERATIONS):
            assert script.jmespath(f"items[{index}].name").get() == f"Item {index}"
            assert script.jmespath("items[*].name").getall() == JSON_NAMES

    run_in_threads(query)
