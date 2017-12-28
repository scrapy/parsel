===============================
Parsel
===============================

.. image:: https://img.shields.io/travis/scrapy/parsel/master.svg
   :target: https://travis-ci.org/scrapy/parsel
   :alt: Build Status

.. image:: https://img.shields.io/pypi/v/parsel.svg
   :target: https://pypi.python.org/pypi/parsel
   :alt: PyPI Version

.. image:: https://img.shields.io/codecov/c/github/scrapy/parsel/master.svg
   :target: http://codecov.io/github/scrapy/parsel?branch=master
   :alt: Coverage report


Parsel is a library to extract data from HTML and XML using XPath and CSS selectors

* Free software: BSD license
* Documentation: https://parsel.readthedocs.org.

Features
--------

* Extract text using CSS or XPath selectors
* Regular expression helper methods

Example::

    >>> from parsel import Selector
    >>> sel = Selector(text=u"""<html>
            <body>
                <h1>Hello, Parsel!</h1>
                <ul>
                    <li><a href="http://example.com">Link 1</a></li>
                    <li><a href="http://scrapy.org">Link 2</a></li>
                </ul
            </body>
            </html>""")
    >>>
    >>> sel.css('h1::text').extract_first()
    u'Hello, Parsel!'
    >>>
    >>> sel.css('h1::text').re('\w+')
    [u'Hello', u'Parsel']
    >>>
    >>> for e in sel.css('ul > li'):
            print(e.xpath('.//a/@href').extract_first())
    http://example.com
    http://scrapy.org
