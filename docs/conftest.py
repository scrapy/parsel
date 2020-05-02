import os
from doctest import ELLIPSIS, NORMALIZE_WHITESPACE
from sys import version_info

from sybil import Sybil
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser
from sybil.parsers.skip import skip

from parsel import Selector


def load_selector(filename, **kwargs):
    input_path = os.path.join(os.path.dirname(__file__), '_static', filename)
    with open(input_path) as input_file:
        return Selector(text=input_file.read(), **kwargs)


def setup(namespace):
    namespace['load_selector'] = load_selector


if version_info >= (3,):
    pytest_collect_file = Sybil(
        parsers=[
            DocTestParser(optionflags=ELLIPSIS | NORMALIZE_WHITESPACE),
            CodeBlockParser(future_imports=['print_function']),
            skip,
        ],
        pattern='*.rst',
        setup=setup,
    ).pytest()
