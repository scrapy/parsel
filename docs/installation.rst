============
Installation
============

To install Parsel, we recommend you to use `pip <https://pip.pypa.io/>`_::

    $ pip install parsel

You `probably shouldn't
<https://stackoverflow.com/questions/3220404/why-use-pip-over-easy-install>`_,
but you can also install it with easy_install::

    $ easy_install parsel

.. _jsonpath-install:

JSONPath support
================

:meth:`~parsel.selector.Selector.jsonpath` requires `jsonpath-rfc9535`_ or
`python-jsonpath`_, each of which has a matching extra::

    $ pip install parsel[jsonpath-rfc9535]
    $ pip install parsel[python-jsonpath]

jsonpath-rfc9535 runs queries 2 to 4 times faster, and supports Unicode
character classes, such as ``\p{Lu}``, in the ``match()`` and ``search()``
JSONPath functions.

However, it only provides wheels for CPython, and not for every platform. PyPy,
free-threaded CPython and Windows on ARM, among others, build it from source,
which requires a Rust toolchain. python-jsonpath is written in pure Python.

Parsel uses jsonpath-rfc9535 when both are installed.

.. _jsonpath-rfc9535: https://jg-rp.github.io/python-jsonpath-rfc9535/
.. _python-jsonpath: https://jg-rp.github.io/python-jsonpath/
