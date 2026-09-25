from doctest import ELLIPSIS, NORMALIZE_WHITESPACE
from pathlib import Path

from sybil import Sybil

try:
    from sybil.parsers.codeblock import PythonCodeBlockParser
except ImportError:
    from sybil.parsers.codeblock import CodeBlockParser as PythonCodeBlockParser
from sybil.parsers.doctest import DocTestParser
from sybil.parsers.skip import skip

from parsel import Selector

# The Sphinx extensions under _ext require Sphinx/docutils, which are not part
# of the test environment. Skip them during pytest's --doctest-modules pass.
collect_ignore_glob = ["_ext/*"]


def load_selector(filename, **kwargs):
    input_path = Path(__file__).parent / "_static" / filename
    return Selector(text=input_path.read_text(encoding="utf-8"), **kwargs)


def setup(namespace):
    namespace["load_selector"] = load_selector


def pytest_collection_modifyitems(items):
    """Drop pytest's built-in doctest collection of the ``.rst`` files.

    When an ``.rst`` file is named explicitly on the command line (e.g.
    ``pytest docs/xpath-tutorial.rst``), pytest's own doctest plugin collects it
    as a text file *in addition* to Sybil (see ``_pytest.doctest._is_doctest``).
    That native pass does not run the ``.. code:: python`` setup blocks, so it
    fails on names such as ``doc``. Sybil is the source of truth for these
    files, so drop the duplicate native doctest items.
    """
    items[:] = [
        item
        for item in items
        if not (
            type(item).__module__.startswith("_pytest.doctest")
            and item.path.suffix in {".rst", ".txt"}
        )
    ]


pytest_collect_file = Sybil(
    parsers=[
        DocTestParser(optionflags=ELLIPSIS | NORMALIZE_WHITESPACE),
        PythonCodeBlockParser(future_imports=["print_function"]),
        skip,
    ],
    pattern="*.rst",
    setup=setup,
).pytest()
