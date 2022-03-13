import os
from doctest import ELLIPSIS, NORMALIZE_WHITESPACE

from sybil import Sybil

try:
    from sybil.parsers.codeblock import PythonCodeBlockParser
except ImportError:
    from sybil.parsers.codeblock import CodeBlockParser as PythonCodeBlockParser
from sybil.parsers.doctest import DocTestParser
from sybil.parsers.skip import skip

from parsel import Selector


def load_selector(filename, **kwargs):
    input_path = os.path.join(os.path.dirname(__file__), "_static", filename)
    with open(input_path, encoding="utf-8") as input_file:
        return Selector(text=input_file.read(), **kwargs)


def setup(namespace):
    namespace["load_selector"] = load_selector


pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS | NORMALIZE_WHITESPACE),
        PythonCodeBlockParser(future_imports=["print_function"]),
        skip,
    ],
    pattern="*.rst",
    setup=setup,
).pytest()
