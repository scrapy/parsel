import os
from doctest import ELLIPSIS, NORMALIZE_WHITESPACE

from sybil import Sybil
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser, FIX_BYTE_UNICODE_REPR
from sybil.parsers.skip import skip

from parsel import Selector


DOCTEST_OPTIONS = ELLIPSIS | FIX_BYTE_UNICODE_REPR | NORMALIZE_WHITESPACE


def load_selector(filename, **kwargs):
    input_path = os.path.join(os.path.dirname(__file__), '_static', filename)
    with open(input_path) as input_file:
        return Selector(text=input_file.read(), **kwargs)


def setup(namespace):
    namespace['load_selector'] = load_selector


pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=DOCTEST_OPTIONS),
        CodeBlockParser(future_imports=['print_function']),
        skip,
    ],
    pattern='*.rst',
    setup=setup,
).pytest()
