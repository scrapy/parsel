# -*- coding: utf-8 -*-
import pytest
from parsel import Selector
import six

@pytest.fixture
def saffron_html_sample():
    """
    A smaller sample html
    """
    return six.u(open("tests/sample_data/saffron.html").read())

@pytest.fixture
def parsel_html_sample():
    """
    A somewhat larger sample html from the parsel docs
    """
    return six.u(open("tests/sample_data/parsel_docs.htm").read())

def test_benchmark_saffron_re(benchmark, saffron_html_sample):
    sel = Selector(text=saffron_html_sample)
    regex = "([\d.]+ dl (.*))<br />"
    benchmark(sel.re, regex)

def test_benchmark_saffron_re_first(benchmark, saffron_html_sample):
    sel = Selector(text=saffron_html_sample)
    regex = "([\d.]+ dl (.*))<br />"
    benchmark(sel.re_first, regex)

def test_benchmark_saffron_re_named(benchmark, saffron_html_sample):
    sel = Selector(text=saffron_html_sample)
    regex = "(?P<extract>[\d.]+ dl (.*))<br />"
    benchmark(sel.re, regex)

def test_benchmark_saffron_re_first_named(benchmark, saffron_html_sample):
    sel = Selector(text=saffron_html_sample)
    regex = "(?P<extract>[\d.]+ dl (.*))<br />"
    benchmark(sel.re_first, regex)


def test_benchmark_saffron_list_re(benchmark, saffron_html_sample):
    sel = Selector(text=saffron_html_sample)
    sel = sel.xpath('//li')
    regex = "([\d.]+ dl (.*))<br />"
    benchmark(sel.re, regex)

def test_benchmark_saffron_list_re_first(benchmark, saffron_html_sample):
    sel = Selector(text=saffron_html_sample)
    sel = sel.xpath('//li')
    regex = "<a .*>"
    benchmark(sel.re_first, regex)

def test_benchmark_saffron_list_re_named(benchmark, saffron_html_sample):
    sel = Selector(text=saffron_html_sample)
    sel = sel.xpath('//li')
    regex = "(?P<extract>[\d.]+ dl (.*))<br />"
    benchmark(sel.re, regex)

def test_benchmark_saffron_list_re_first_named(benchmark, saffron_html_sample):
    sel = Selector(text=saffron_html_sample)
    sel = sel.xpath('//li')
    regex = "(?P<extract><a .*>)"
    benchmark(sel.re_first, regex)








def test_benchmark_parsel_re(benchmark, parsel_html_sample):
    sel = Selector(text=parsel_html_sample)
    regex = "<a .*>"
    benchmark(sel.re, regex)

def test_benchmark_parsel_re_first(benchmark, parsel_html_sample):
    sel = Selector(text=parsel_html_sample)
    regex = "<a .*>"
    benchmark(sel.re_first, regex)

def test_benchmark_parsel_list_re(benchmark, parsel_html_sample):
    sel = Selector(text=parsel_html_sample)
    sel = sel.xpath('//a')
    regex = "(\w+)"
    benchmark(sel.re, regex)

def test_benchmark_parsel_list_re_first(benchmark, parsel_html_sample):
    sel = Selector(text=parsel_html_sample)
    sel = sel.xpath('//a')
    regex = "(\w+)"
    benchmark(sel.re_first, regex)

def test_benchmark_parsel_re_named(benchmark, parsel_html_sample):
    sel = Selector(text=parsel_html_sample)
    regex = "(?P<extract><a .*>)"
    benchmark(sel.re, regex)

def test_benchmark_parsel_re_named_first(benchmark, parsel_html_sample):
    sel = Selector(text=parsel_html_sample)
    regex = "(?P<extract><a .*>)"
    benchmark(sel.re_first, regex)

def test_benchmark_parsel_list_re_named(benchmark, parsel_html_sample):
    sel = Selector(text=parsel_html_sample)
    sel = sel.xpath('//a')
    regex = "(?P<extract>\w+)"
    benchmark(sel.re, regex)

def test_benchmark_parsel_list_re_named_first(benchmark, parsel_html_sample):
    sel = Selector(text=parsel_html_sample)
    sel = sel.xpath('//a')
    regex = "(?P<extract>\w+)"
    benchmark(sel.re_first, regex)
