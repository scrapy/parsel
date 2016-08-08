# -*- coding: utf-8 -*-
import pytest
from parsel import Selector
import codecs

@pytest.fixture
def large_text_sample():
    return codecs.open("tests/sample_data/saffron.html", encoding='utf-8').read()

def test_benchmark_re(benchmark, large_text_sample):
    sel = Selector(text=large_text_sample)
    dl_re = "(2.5 dl (.*))<br />"
    benchmark(sel.re, dl_re)


def test_benchmark_re_first(benchmark, large_text_sample):
    sel = Selector(text=large_text_sample)
    dl_re = "(2.5 dl (.*))<br />"
    benchmark(sel.re_first, dl_re)
