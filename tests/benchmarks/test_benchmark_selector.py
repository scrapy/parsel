from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from parsel import Selector

if TYPE_CHECKING:
    from pytest_codspeed import BenchmarkFixture  # type: ignore[import-not-found]

pytest.importorskip("pytest_codspeed", reason="Benchmarks require pytest-codspeed")

ITEM_COUNT = 3000


def _item_html(index: int) -> str:
    price = 9.99 + (index % 500)
    return (
        f'<li class="product" data-index="{index}">'
        f'<h2 class="title"><a href="/item/{index}">Product {index}</a></h2>'
        f'<span class="price">${price:.2f}</span>'
        f'<p class="desc">A description of product {index}.</p>'
        "</li>"
    )


def _build_catalog(item_count: int) -> str:
    """Return an HTML catalog page listing *item_count* products."""
    items = "".join(_item_html(index) for index in range(item_count))
    return (
        "<!DOCTYPE html><html><head><title>Catalog</title></head><body>"
        f'<ul class="catalog">{items}</ul>'
        "</body></html>"
    )


CATALOG_HTML = _build_catalog(ITEM_COUNT)


def test_parse(benchmark: BenchmarkFixture) -> None:
    benchmark(lambda: Selector(text=CATALOG_HTML))


def test_query_broad_css(benchmark: BenchmarkFixture) -> None:
    sel = Selector(text=CATALOG_HTML)

    def run() -> None:
        assert len(sel.css(".product")) == ITEM_COUNT

    benchmark(run)


def test_query_broad_xpath(benchmark: BenchmarkFixture) -> None:
    sel = Selector(text=CATALOG_HTML)

    def run() -> None:
        assert len(sel.xpath("//*[@class='product']")) == ITEM_COUNT

    benchmark(run)


def test_query_chained_elements_css(benchmark: BenchmarkFixture) -> None:
    """The ``for item in sel.css(...): item.css(...)`` spider pattern."""
    items = Selector(text=CATALOG_HTML).css(".product")

    def run() -> None:
        for item in items:
            item.css("h2.title a")
            item.css(".price")
            item.css(".desc")

    benchmark(run)


def test_query_chained_elements_xpath(benchmark: BenchmarkFixture) -> None:
    items = Selector(text=CATALOG_HTML).xpath("//*[@class='product']")

    def run() -> None:
        for item in items:
            item.xpath(".//h2[@class='title']/a")
            item.xpath(".//*[@class='price']")
            item.xpath(".//*[@class='desc']")

    benchmark(run)


def test_query_chained_values_css(benchmark: BenchmarkFixture) -> None:
    """Extracting title, link, price and description text/attrs per item."""
    items = Selector(text=CATALOG_HTML).css(".product")

    def run() -> None:
        for item in items:
            item.css("h2.title a::text").get()
            item.css("h2.title a::attr(href)").get()
            item.css(".price::text").get()
            item.css(".desc::text").get()

    benchmark(run)


def test_query_chained_values_xpath(benchmark: BenchmarkFixture) -> None:
    items = Selector(text=CATALOG_HTML).xpath("//*[@class='product']")

    def run() -> None:
        for item in items:
            item.xpath(".//h2[@class='title']/a/text()").get()
            item.xpath(".//h2[@class='title']/a/@href").get()
            item.xpath(".//*[@class='price']/text()").get()
            item.xpath(".//*[@class='desc']/text()").get()

    benchmark(run)


def test_re(benchmark: BenchmarkFixture) -> None:
    prices = Selector(text=CATALOG_HTML).css(".price::text")
    benchmark(lambda: prices.re(r"[\d.]+"))


def test_re_first(benchmark: BenchmarkFixture) -> None:
    prices = Selector(text=CATALOG_HTML).css(".price::text")
    benchmark(lambda: prices.re_first(r"[\d.]+"))
