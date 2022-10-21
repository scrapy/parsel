.. _topics-selectors:

=====
Usage
=====

Create a :class:`~parsel.selector.Selector` object for the HTML or XML text
that you want to parse::

    >>> from parsel import Selector
    >>> text = "<html><body><h1>Hello, Parsel!</h1></body></html>"
    >>> selector = Selector(text=text)

Then use `CSS`_ or `XPath`_ expressions to select elements::

    >>> selector.css('h1')
    [<Selector xpath='descendant-or-self::h1' data='<h1>Hello, Parsel!</h1>'>]
    >>> selector.xpath('//h1')  # the same, but now with XPath
    [<Selector xpath='//h1' data='<h1>Hello, Parsel!</h1>'>]

And extract data from those elements::

    >>> selector.css('h1::text').get()
    'Hello, Parsel!'
    >>> selector.xpath('//h1/text()').getall()
    ['Hello, Parsel!']

.. _CSS: https://www.w3.org/TR/selectors
.. _XPath: https://www.w3.org/TR/xpath

Learning CSS and XPath
======================

`CSS`_ is a language for applying styles to HTML documents. It defines
selectors to associate those styles with specific HTML elements. Resources to
learn CSS_ selectors include:

-   `CSS selectors in the MDN`_

-   `XPath/CSS Equivalents in Wikibooks`_

`XPath`_ is a language for selecting nodes in XML documents, which can also be
used with HTML. Resources to learn XPath_ include:

-   `XPath Tutorial in W3Schools`_

-   `XPath cheatsheet`_

You can use either CSS_ or XPath_. CSS_ is usually more readable, but some
things can only be done with XPath_.

.. _CSS selectors in the MDN: https://developer.mozilla.org/en-US/docs/Learn/CSS/Building_blocks/Selectors
.. _XPath cheatsheet: https://devhints.io/xpath
.. _XPath Tutorial in W3Schools: https://www.w3schools.com/xml/xpath_intro.asp
.. _XPath/CSS Equivalents in Wikibooks: https://en.wikibooks.org/wiki/XPath/CSS_Equivalents


Using selectors
===============

To explain how to use the selectors we'll use the :mod:`requests` library
to download an example page located in the Parsel's documentation:

    https://parsel.readthedocs.org/en/latest/_static/selectors-sample1.html

.. _topics-selectors-htmlcode:

For the sake of completeness, here's its full HTML code:

.. literalinclude:: _static/selectors-sample1.html
   :language: html

.. highlight:: python

So, let's download that page and create a selector for it:

.. skip: start

>>> import requests
>>> from parsel import Selector
>>> url = 'https://parsel.readthedocs.org/en/latest/_static/selectors-sample1.html'
>>> text = requests.get(url).text
>>> selector = Selector(text=text)

.. skip: end

.. invisible-code-block: python

   selector = load_selector('selectors-sample1.html')

Since we're dealing with HTML, the default type for Selector, we don't need
to specify the `type` argument.

So, by looking at the :ref:`HTML code <topics-selectors-htmlcode>` of that
page, let's construct an XPath for selecting the text inside the title tag::

    >>> selector.xpath('//title/text()')
    [<Selector xpath='//title/text()' data='Example website'>]

You can also ask the same thing using CSS instead::

    >>> selector.css('title::text')
    [<Selector xpath='descendant-or-self::title/text()' data='Example website'>]

To actually extract the textual data, you must call the selector ``.get()``
or ``.getall()`` methods, as follows::

    >>> selector.xpath('//title/text()').getall()
    ['Example website']
    >>> selector.xpath('//title/text()').get()
    'Example website'

``.get()`` always returns a single result; if there are several matches,
content of a first match is returned; if there are no matches, None
is returned. ``.getall()`` returns a list with all results.

Notice that CSS selectors can select text or attribute nodes using CSS3
pseudo-elements::

    >>> selector.css('title::text').get()
    'Example website'

As you can see, ``.xpath()`` and ``.css()`` methods return a
:class:`~parsel.selector.SelectorList` instance, which is a list of new
selectors. This API can be used for quickly selecting nested data::

    >>> selector.css('img').xpath('@src').getall()
    ['image1_thumb.jpg',
     'image2_thumb.jpg',
     'image3_thumb.jpg',
     'image4_thumb.jpg',
     'image5_thumb.jpg']

If you want to extract only the first matched element, you can call the
selector ``.get()`` (or its alias ``.extract_first()`` commonly used in
previous parsel versions)::

    >>> selector.xpath('//div[@id="images"]/a/text()').get()
    'Name: My image 1 '

It returns ``None`` if no element was found::

    >>> selector.xpath('//div[@id="not-exists"]/text()').get() is None
    True

Instead of using e.g. ``'@src'`` XPath it is possible to query for attributes
using ``.attrib`` property of a :class:`~parsel.selector.Selector`::

    >>> [img.attrib['src'] for img in selector.css('img')]
    ['image1_thumb.jpg',
     'image2_thumb.jpg',
     'image3_thumb.jpg',
     'image4_thumb.jpg',
     'image5_thumb.jpg']

As a shortcut, ``.attrib`` is also available on SelectorList directly;
it returns attributes for the first matching element::

    >>> selector.css('img').attrib['src']
    'image1_thumb.jpg'

This is most useful when only a single result is expected, e.g. when selecting
by id, or selecting unique elements on a web page::

    >>> selector.css('base').attrib['href']
    'http://example.com/'

Now we're going to get the base URL and some image links::

    >>> selector.xpath('//base/@href').get()
    'http://example.com/'

    >>> selector.css('base::attr(href)').get()
    'http://example.com/'

    >>> selector.css('base').attrib['href']
    'http://example.com/'

    >>> selector.xpath('//a[contains(@href, "image")]/@href').getall()
    ['image1.html',
     'image2.html',
     'image3.html',
     'image4.html',
     'image5.html']

    >>> selector.css('a[href*=image]::attr(href)').getall()
    ['image1.html',
     'image2.html',
     'image3.html',
     'image4.html',
     'image5.html']

    >>> selector.xpath('//a[contains(@href, "image")]/img/@src').getall()
    ['image1_thumb.jpg',
     'image2_thumb.jpg',
     'image3_thumb.jpg',
     'image4_thumb.jpg',
     'image5_thumb.jpg']

    >>> selector.css('a[href*=image] img::attr(src)').getall()
    ['image1_thumb.jpg',
     'image2_thumb.jpg',
     'image3_thumb.jpg',
     'image4_thumb.jpg',
     'image5_thumb.jpg']

.. _topics-selectors-css-extensions:

Extensions to CSS Selectors
---------------------------

Per W3C standards, `CSS selectors`_ do not support selecting text nodes
or attribute values.
But selecting these is so essential in a web scraping context
that Parsel implements a couple of **non-standard pseudo-elements**:

* to select text nodes, use ``::text``
* to select attribute values, use ``::attr(name)`` where *name* is the
  name of the attribute that you want the value of

.. warning::
    These pseudo-elements are Scrapy-/Parsel-specific.
    They will most probably not work with other libraries like `lxml`_ or `PyQuery`_.


Examples:

* ``title::text`` selects children text nodes of a descendant ``<title>`` element::

    >>> selector.css('title::text').get()
    'Example website'

* ``*::text`` selects all descendant text nodes of the current selector context::

    >>> selector.css('#images *::text').getall()
    ['\n   ',
     'Name: My image 1 ',
     '\n   ',
     'Name: My image 2 ',
     '\n   ',
     'Name: My image 3 ',
     '\n   ',
     'Name: My image 4 ',
     '\n   ',
     'Name: My image 5 ',
     '\n  ']

* ``a::attr(href)`` selects the *href* attribute value of descendant links::

    >>> selector.css('a::attr(href)').getall()
    ['image1.html',
     'image2.html',
     'image3.html',
     'image4.html',
     'image5.html']

.. note::
    You cannot chain these pseudo-elements. But in practice it would not
    make much sense: text nodes do not have attributes, and attribute values
    are string values already and do not have children nodes.

.. note::
    See also: :ref:`selecting-attributes`.


.. _CSS Selectors: https://www.w3.org/TR/css3-selectors/#selectors

.. _topics-selectors-nesting-selectors:

Nesting selectors
-----------------

The selection methods (``.xpath()`` or ``.css()``) return a list of selectors
of the same type, so you can call the selection methods for those selectors
too. Here's an example::

    >>> links = selector.xpath('//a[contains(@href, "image")]')
    >>> links.getall()
    ['<a href="image1.html">Name: My image 1 <br><img src="image1_thumb.jpg"></a>',
     '<a href="image2.html">Name: My image 2 <br><img src="image2_thumb.jpg"></a>',
     '<a href="image3.html">Name: My image 3 <br><img src="image3_thumb.jpg"></a>',
     '<a href="image4.html">Name: My image 4 <br><img src="image4_thumb.jpg"></a>',
     '<a href="image5.html">Name: My image 5 <br><img src="image5_thumb.jpg"></a>']

    >>> for index, link in enumerate(links):
    ...     args = (index, link.xpath('@href').get(), link.xpath('img/@src').get())
    ...     print('Link number %d points to url %r and image %r' % args)
    Link number 0 points to url 'image1.html' and image 'image1_thumb.jpg'
    Link number 1 points to url 'image2.html' and image 'image2_thumb.jpg'
    Link number 2 points to url 'image3.html' and image 'image3_thumb.jpg'
    Link number 3 points to url 'image4.html' and image 'image4_thumb.jpg'
    Link number 4 points to url 'image5.html' and image 'image5_thumb.jpg'

.. _selecting-attributes:

Selecting element attributes
----------------------------

There are several ways to get a value of an attribute. First, one can use
XPath syntax::

    >>> selector.xpath("//a/@href").getall()
    ['image1.html', 'image2.html', 'image3.html', 'image4.html', 'image5.html']

XPath syntax has a few advantages: it is a standard XPath feature, and
``@attributes`` can be used in other parts of an XPath expression - e.g.
it is possible to filter by attribute value.

parsel also provides an extension to CSS selectors (``::attr(...)``)
which allows to get attribute values::

    >>> selector.css('a::attr(href)').getall()
    ['image1.html', 'image2.html', 'image3.html', 'image4.html', 'image5.html']

In addition to that, there is a ``.attrib`` property of Selector.
You can use it if you prefer to lookup attributes in Python
code, without using XPaths or CSS extensions::

    >>> [a.attrib['href'] for a in selector.css('a')]
    ['image1.html', 'image2.html', 'image3.html', 'image4.html', 'image5.html']

This property is also available on SelectorList; it returns a dictionary
with attributes of a first matching element. It is convenient to use when
a selector is expected to give a single result (e.g. when selecting by element
ID, or when selecting an unique element on a page)::

    >>> selector.css('base').attrib
    {'href': 'http://example.com/'}
    >>> selector.css('base').attrib['href']
    'http://example.com/'

``.attrib`` property of an empty SelectorList is empty::

    >>> selector.css('foo').attrib
    {}

Using selectors with regular expressions
----------------------------------------

:class:`~parsel.selector.Selector` also has a ``.re()`` method for extracting
data using regular expressions. However, unlike using ``.xpath()`` or
``.css()`` methods, ``.re()`` returns a list of strings. So you
can't construct nested ``.re()`` calls.

Here's an example used to extract image names from the :ref:`HTML code
<topics-selectors-htmlcode>` above::

    >>> selector.xpath('//a[contains(@href, "image")]/text()').re(r'Name:\s*(.*)')
    ['My image 1 ',
     'My image 2 ',
     'My image 3 ',
     'My image 4 ',
     'My image 5 ']

There's an additional helper reciprocating ``.get()`` (and its
alias ``.extract_first()``) for ``.re()``, named ``.re_first()``.
Use it to extract just the first matching string::

    >>> selector.xpath('//a[contains(@href, "image")]/text()').re_first(r'Name:\s*(.*)')
    'My image 1 '

.. _topics-selectors-relative-xpaths:

Working with relative XPaths
----------------------------

Keep in mind that if you are nesting selectors and use an XPath that starts
with ``/``, that XPath will be absolute to the document and not relative to the
selector you're calling it from.

For example, suppose you want to extract all ``<p>`` elements inside ``<div>``
elements. First, you would get all ``<div>`` elements::

    >>> divs = selector.xpath('//div')

At first, you may be tempted to use the following approach, which is wrong, as
it actually extracts all ``<p>`` elements from the document, not only those
inside ``<div>`` elements::

    >>> for p in divs.xpath('//p'):  # this is wrong - gets all <p> from the whole document
    ...     print(p.get())

This is the proper way to do it (note the dot prefixing the ``.//p`` XPath)::

    >>> for p in divs.xpath('.//p'):  # extracts all <p> inside
    ...     print(p.get())

Another common case would be to extract all direct ``<p>`` children::

    >>> for p in divs.xpath('p'):
    ...     print(p.get())

For more details about relative XPaths see the `Location Paths`_ section in the
XPath specification.

.. _Location Paths: https://www.w3.org/TR/xpath#location-paths


Removing elements
-----------------

If for any reason you need to remove elements based on a Selector or
a SelectorList, you can do it with the ``remove()`` method, available for both
classes.

.. warning:: this is a destructive action and cannot be undone. The original
    content of the selector is removed from the elements tree. This could be useful
    when trying to reduce the memory footprint of Responses.

Example removing an ad from a blog post:

    >>> from parsel import Selector
    >>> doc = """
    ... <article>
    ...     <div class="row">Content paragraph...</div>
    ...     <div class="row">
    ...         <div class="ad">
    ...             Ad content...
    ...             <a href="http://...">Link</a>
    ...         </div>
    ...     </div>
    ...     <div class="row">More content...</div>
    ... </article>
    ... """
    >>> sel = Selector(text=doc)
    >>> sel.xpath('//div/text()').getall()
    ['Content paragraph...', '\n        ', '\n            Ad content...\n            ', '\n        ', '\n    ', 'More content...']
    >>> sel.xpath('//div[@class="ad"]').remove()
    >>> sel.xpath('//div//text()').getall()
    ['Content paragraph...', 'More content...']


Using EXSLT extensions
----------------------

Being built atop `lxml`_, parsel selectors support some `EXSLT`_ extensions
and come with these pre-registered namespaces to use in XPath expressions:


======  =====================================    =======================
prefix  namespace                                usage
======  =====================================    =======================
re      \http://exslt.org/regular-expressions    `regular expressions`_
set     \http://exslt.org/sets                   `set manipulation`_
======  =====================================    =======================

Regular expressions
~~~~~~~~~~~~~~~~~~~

The ``test()`` function, for example, can prove quite useful when XPath's
``starts-with()`` or ``contains()`` are not sufficient.

Example selecting links in list item with a "class" attribute ending with a digit::

    >>> from parsel import Selector
    >>> doc = """
    ... <div>
    ...     <ul>
    ...         <li class="item-0"><a href="link1.html">first item</a></li>
    ...         <li class="item-1"><a href="link2.html">second item</a></li>
    ...         <li class="item-inactive"><a href="link3.html">third item</a></li>
    ...         <li class="item-1"><a href="link4.html">fourth item</a></li>
    ...         <li class="item-0"><a href="link5.html">fifth item</a></li>
    ...     </ul>
    ... </div>
    ... """
    >>> sel = Selector(text=doc)
    >>> sel.xpath('//li//@href').getall()
    ['link1.html', 'link2.html', 'link3.html', 'link4.html', 'link5.html']
    >>> sel.xpath(r'//li[re:test(@class, "item-\d$")]//@href').getall()
    ['link1.html', 'link2.html', 'link4.html', 'link5.html']
    >>>

.. warning:: C library ``libxslt`` doesn't natively support EXSLT regular
    expressions so `lxml`_'s implementation uses hooks to Python's ``re`` module.
    Thus, using regexp functions in your XPath expressions may add a small
    performance penalty.

Set operations
~~~~~~~~~~~~~~

These can be handy for excluding parts of a document tree before
extracting text elements for example.

Example extracting microdata (sample content taken from http://schema.org/Product)
with groups of itemscopes and corresponding itemprops::

    >>> doc = """
    ... <div itemscope itemtype="http://schema.org/Product">
    ...   <span itemprop="name">Kenmore White 17" Microwave</span>
    ...   <img src="kenmore-microwave-17in.jpg" alt='Kenmore 17" Microwave' />
    ...   <div itemprop="aggregateRating"
    ...     itemscope itemtype="http://schema.org/AggregateRating">
    ...    Rated <span itemprop="ratingValue">3.5</span>/5
    ...    based on <span itemprop="reviewCount">11</span> customer reviews
    ...   </div>
    ...
    ...   <div itemprop="offers" itemscope itemtype="http://schema.org/Offer">
    ...     <span itemprop="price">$55.00</span>
    ...     <link itemprop="availability" href="http://schema.org/InStock" />In stock
    ...   </div>
    ...
    ...   Product description:
    ...   <span itemprop="description">0.7 cubic feet countertop microwave.
    ...   Has six preset cooking categories and convenience features like
    ...   Add-A-Minute and Child Lock.</span>
    ...
    ...   Customer reviews:
    ...
    ...   <div itemprop="review" itemscope itemtype="http://schema.org/Review">
    ...     <span itemprop="name">Not a happy camper</span> -
    ...     by <span itemprop="author">Ellie</span>,
    ...     <meta itemprop="datePublished" content="2011-04-01">April 1, 2011
    ...     <div itemprop="reviewRating" itemscope itemtype="http://schema.org/Rating">
    ...       <meta itemprop="worstRating" content = "1">
    ...       <span itemprop="ratingValue">1</span>/
    ...       <span itemprop="bestRating">5</span>stars
    ...     </div>
    ...     <span itemprop="description">The lamp burned out and now I have to replace
    ...     it. </span>
    ...   </div>
    ...
    ...   <div itemprop="review" itemscope itemtype="http://schema.org/Review">
    ...     <span itemprop="name">Value purchase</span> -
    ...     by <span itemprop="author">Lucas</span>,
    ...     <meta itemprop="datePublished" content="2011-03-25">March 25, 2011
    ...     <div itemprop="reviewRating" itemscope itemtype="http://schema.org/Rating">
    ...       <meta itemprop="worstRating" content = "1"/>
    ...       <span itemprop="ratingValue">4</span>/
    ...       <span itemprop="bestRating">5</span>stars
    ...     </div>
    ...     <span itemprop="description">Great microwave for the price. It is small and
    ...     fits in my apartment.</span>
    ...   </div>
    ...   ...
    ... </div>
    ... """
    >>> sel = Selector(text=doc, type="html")
    >>> for scope in sel.xpath('//div[@itemscope]'):
    ...     print("current scope:", scope.xpath('@itemtype').getall())
    ...     props = scope.xpath('''
    ...                 set:difference(./descendant::*/@itemprop,
    ...                                .//*[@itemscope]/*/@itemprop)''')
    ...     print("    properties: %s" % (props.getall()))
    ...     print("")
    current scope: ['http://schema.org/Product']
        properties: ['name', 'aggregateRating', 'offers', 'description', 'review', 'review']
    <BLANKLINE>
    current scope: ['http://schema.org/AggregateRating']
        properties: ['ratingValue', 'reviewCount']
    <BLANKLINE>
    current scope: ['http://schema.org/Offer']
        properties: ['price', 'availability']
    <BLANKLINE>
    current scope: ['http://schema.org/Review']
        properties: ['name', 'author', 'datePublished', 'reviewRating', 'description']
    <BLANKLINE>
    current scope: ['http://schema.org/Rating']
        properties: ['worstRating', 'ratingValue', 'bestRating']
    <BLANKLINE>
    current scope: ['http://schema.org/Review']
        properties: ['name', 'author', 'datePublished', 'reviewRating', 'description']
    <BLANKLINE>
    current scope: ['http://schema.org/Rating']
        properties: ['worstRating', 'ratingValue', 'bestRating']


Here we first iterate over ``itemscope`` elements, and for each one,
we look for all ``itemprops`` elements and exclude those that are themselves
inside another ``itemscope``.

.. _EXSLT: http://exslt.org/
.. _regular expressions: http://exslt.org/regexp/index.html
.. _set manipulation: http://exslt.org/set/index.html

.. _topics-xpath-other-extensions:

Other XPath extensions
----------------------

Parsel also defines a sorely missed XPath extension function ``has-class`` that
returns ``True`` for nodes that have all of the specified HTML classes::

    >>> from parsel import Selector
    >>> sel = Selector("""
    ...         <p class="foo bar-baz">First</p>
    ...         <p class="foo">Second</p>
    ...         <p class="bar">Third</p>
    ...         <p>Fourth</p>
    ... """)
    ...
    >>> sel = Selector("""
    ...         <p class="foo bar-baz">First</p>
    ...         <p class="foo">Second</p>
    ...         <p class="bar">Third</p>
    ...         <p>Fourth</p>
    ... """)
    ...
    >>> sel.xpath('//p[has-class("foo")]')
    [<Selector xpath='//p[has-class("foo")]' data='<p class="foo bar-baz">First</p>'>,
     <Selector xpath='//p[has-class("foo")]' data='<p class="foo">Second</p>'>]
    >>> sel.xpath('//p[has-class("foo", "bar-baz")]')
    [<Selector xpath='//p[has-class("foo", "bar-baz")]' data='<p class="foo bar-baz">First</p>'>]
    >>> sel.xpath('//p[has-class("foo", "bar")]')
    []

So XPath ``//p[has-class("foo", "bar-baz")]`` is roughly equivalent to CSS
``p.foo.bar-baz``.  Please note, that it is slower in most of the cases,
because it's a pure-Python function that's invoked for every node in question
whereas the CSS lookup is translated into XPath and thus runs more efficiently,
so performance-wise its uses are limited to situations that are not easily
described with CSS selectors.

Parsel also simplifies adding your own XPath extensions.

.. autofunction:: parsel.xpathfuncs.set_xpathfunc



Some XPath tips
---------------

Here are some tips that you may find useful when using XPath
with Parsel, based on `this post from Zyte's blog`_.
If you are not much familiar with XPath yet,
you may want to take a look first at this `XPath tutorial`_.


.. _`XPath tutorial`: http://www.zvon.org/comp/r/tut-XPath_1.html
.. _`this post from Zyte's blog`: https://www.zyte.com/blog/xpath-tips-from-the-web-scraping-trenches/


Using text nodes in a condition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you need to use the text content as argument to an `XPath string function`_,
avoid using ``.//text()`` and use just ``.`` instead.

This is because the expression ``.//text()`` yields a collection of text elements -- a *node-set*.
And when a node-set is converted to a string, which happens when it is passed as argument to
a string function like ``contains()`` or ``starts-with()``, it results in the text for the first element only.

Example::

    >>> from parsel import Selector
    >>> sel = Selector(text='<a href="#">Click here to go to the <strong>Next Page</strong></a>')

Converting a *node-set* to string::

    >>> sel.xpath('//a//text()').getall() # take a peek at the node-set
    ['Click here to go to the ', 'Next Page']
    >>> sel.xpath("string(//a[1]//text())").getall() # convert it to string
    ['Click here to go to the ']

A *node* converted to a string, however, puts together the text of itself plus of all its descendants::

    >>> sel.xpath("//a[1]").getall() # select the first node
    ['<a href="#">Click here to go to the <strong>Next Page</strong></a>']
    >>> sel.xpath("string(//a[1])").getall() # convert it to string
    ['Click here to go to the Next Page']

So, using the ``.//text()`` node-set won't select anything in this case::

    >>> sel.xpath("//a[contains(.//text(), 'Next Page')]").getall()
    []

But using the ``.`` to mean the node, works::

    >>> sel.xpath("//a[contains(., 'Next Page')]").getall()
    ['<a href="#">Click here to go to the <strong>Next Page</strong></a>']

.. _`XPath string function`: https://www.w3.org/TR/xpath/#section-String-Functions

Beware of the difference between //node[1] and (//node)[1]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``//node[1]`` selects all the nodes occurring first under their respective parents.

``(//node)[1]`` selects all the nodes in the document, and then gets only the first of them.

Example::

    >>> from parsel import Selector
    >>> sel = Selector(text="""
    ...     <ul class="list">
    ...         <li>1</li>
    ...         <li>2</li>
    ...         <li>3</li>
    ...     </ul>
    ...     <ul class="list">
    ...         <li>4</li>
    ...         <li>5</li>
    ...         <li>6</li>
    ...     </ul>""")
    >>> xp = lambda x: sel.xpath(x).getall()

This gets all first ``<li>``  elements under whatever it is its parent::

    >>> xp("//li[1]")
    ['<li>1</li>', '<li>4</li>']

And this gets the first ``<li>``  element in the whole document::

    >>> xp("(//li)[1]")
    ['<li>1</li>']

This gets all first ``<li>``  elements under an ``<ul>``  parent::

    >>> xp("//ul/li[1]")
    ['<li>1</li>', '<li>4</li>']

And this gets the first ``<li>``  element under an ``<ul>``  parent in the whole document::

    >>> xp("(//ul/li)[1]")
    ['<li>1</li>']

When querying by class, consider using CSS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because an element can contain multiple CSS classes, the XPath way to select elements
by class is the rather verbose::

    *[contains(concat(' ', normalize-space(@class), ' '), ' someclass ')]

If you use ``@class='someclass'`` you may end up missing elements that have
other classes, and if you just use ``contains(@class, 'someclass')`` to make up
for that you may end up with more elements that you want, if they have a different
class name that shares the string ``someclass``.

As it turns out, parsel selectors allow you to chain selectors, so most of the time
you can just select by class using CSS and then switch to XPath when needed::

    >>> from parsel import Selector
    >>> sel = Selector(text='<div class="hero shout"><time datetime="2014-07-23 19:00">Special date</time></div>')
    >>> sel.css('.shout').xpath('./time/@datetime').getall()
    ['2014-07-23 19:00']

This is cleaner than using the verbose XPath trick shown above. Just remember
to use the ``.`` in the XPath expressions that will follow.


Beware of how script and style tags differ from other tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Following the standard`__, the contents of ``script`` and ``style`` elements
are parsed as plain text.

__ https://www.w3.org/TR/html401/types.html#type-cdata

This means that XML-like structures found within them, including comments, are
all treated as part of the element text, and not as separate nodes.

For example::

    >>> from parsel import Selector
    >>> selector = Selector(text="""
    ...     <script>
    ...         text
    ...         <!-- comment -->
    ...         <br/>
    ...     </script>
    ...     <style>
    ...         text
    ...         <!-- comment -->
    ...         <br/>
    ...     </style>
    ...     <div>
    ...         text
    ...         <!-- comment -->
    ...         <br/>
    ...     </div>""")
    >>> for tag in selector.xpath('//*[contains(text(), "text")]'):
    ...     print(tag.xpath('name()').get())
    ...     print('    Text: ' + (tag.xpath('text()').get() or ''))
    ...     print('    Comment: ' + (tag.xpath('comment()').get() or ''))
    ...     print('    Children: ' + ''.join(tag.xpath('*').getall()))
    ...
    script
        Text:
            text
            <!-- comment -->
            <br/>
    <BLANKLINE>
        Comment:
        Children:
    style
        Text:
            text
            <!-- comment -->
            <br/>
    <BLANKLINE>
        Comment:
        Children:
    div
        Text:
            text
    <BLANKLINE>
        Comment: <!-- comment -->
        Children: <br>

.. _old-extraction-api:

extract() and extract_first()
-----------------------------

If you're a long-time parsel (or Scrapy) user, you're probably familiar
with ``.extract()`` and ``.extract_first()`` selector methods. These methods
are still supported by parsel, there are no plans to deprecate them.

However, ``parsel`` usage docs are now written using ``.get()`` and
``.getall()`` methods. We feel that these new methods result in more concise
and readable code.

The following examples show how these methods map to each other.

.. invisible-code-block: python

   selector = load_selector('selectors-sample1.html')

1. ``SelectorList.get()`` is the same as ``SelectorList.extract_first()``::

     >>> selector.css('a::attr(href)').get()
     'image1.html'
     >>> selector.css('a::attr(href)').extract_first()
     'image1.html'

2. ``SelectorList.getall()`` is the same as ``SelectorList.extract()``::

     >>> selector.css('a::attr(href)').getall()
     ['image1.html', 'image2.html', 'image3.html', 'image4.html', 'image5.html']
     >>> selector.css('a::attr(href)').extract()
     ['image1.html', 'image2.html', 'image3.html', 'image4.html', 'image5.html']

3. ``Selector.get()`` is the same as ``Selector.extract()``::

     >>> selector.css('a::attr(href)')[0].get()
     'image1.html'
     >>> selector.css('a::attr(href)')[0].extract()
     'image1.html'

4. For consistency, there is also ``Selector.getall()``, which returns a list::

    >>> selector.css('a::attr(href)')[0].getall()
    ['image1.html']

With the ``.extract()`` method it was not always obvious if a result is a list
or not; to get a single result either ``.extract()`` or ``.extract_first()``
needed to be called, depending whether you had a ``Selector`` or ``SelectorList``.

So, the main difference is that the outputs of ``.get()`` and ``.getall()``
are more predictable: ``.get()`` always returns a single result,
``.getall()`` always returns a list of all extracted results.


Using CSS selectors in multi-root documents
-------------------------------------------

Some webpages may have multiple root elements. It can happen, for example, when
a webpage has broken code, such as missing closing tags.

.. invisible-code-block: python

   selector = load_selector('multiroot.html')

You can use XPath to determine if a page has multiple root elements:

>>> len(selector.xpath('/*')) > 1
True

CSS selectors only work on the first root element, because the first root
element is always used as the starting current element, and CSS selectors do
not allow selecting parent elements (XPath’s ``..``) or elements relative to
the document root (XPath’s ``/``).

If you want to use a CSS selector that takes into account all root elements,
you need to precede your CSS query by an XPath query that reaches all root
elements::

    selector.xpath('/*').css('<your CSS selector>')


Command-Line Interface Tools
============================

There are third-party tools that allow using Parsel from the command line:

-   `Parsel CLI <https://github.com/rmax/parsel-cli>`_ allows applying
    Parsel selectors to the standard input. For example, you can apply a Parsel
    selector to the output of cURL_.

-   `parselcli
    <https://github.com/Granitosaurus/parsel-cli>`_ provides an interactive
    shell that allows applying Parsel selectors to a remote URL or a local
    file.

.. _cURL: https://curl.haxx.se/


.. _selector-examples-html:

Examples
========

Working on HTML
---------------

Here are some :class:`~parsel.selector.Selector` examples to illustrate
several concepts. In all cases, we assume there is already
a :class:`~parsel.selector.Selector` instantiated with an HTML text like this::

      sel = Selector(text=html_text)

1. Select all ``<h1>`` elements from an HTML text, returning a list of
   :class:`~parsel.selector.Selector` objects
   (ie. a :class:`~parsel.selector.SelectorList` object)::

      sel.xpath("//h1")

2. Extract the text of all ``<h1>`` elements from an HTML text,
   returning a list of strings::

      sel.xpath("//h1").getall()         # this includes the h1 tag
      sel.xpath("//h1/text()").getall()  # this excludes the h1 tag

3. Iterate over all ``<p>`` tags and print their class attribute::

      for node in sel.xpath("//p"):
          print(node.attrib['class'])


.. _selector-examples-xml:

Working on XML (and namespaces)
-------------------------------

Here are some examples to illustrate concepts for
:class:`~parsel.selector.Selector` objects instantiated with an XML text
like this::

      sel = Selector(text=xml_text, type='xml')

1. Select all ``<product>`` elements from an XML text, returning a list
   of :class:`~parsel.selector.Selector` objects
   (ie. a :class:`~parsel.selector.SelectorList` object)::

      sel.xpath("//product")

2. Extract all prices from a `Google Base XML feed`_ which requires registering
   a namespace::

      sel.register_namespace("g", "http://base.google.com/ns/1.0")
      sel.xpath("//g:price").getall()

.. _removing-namespaces:

Removing namespaces
~~~~~~~~~~~~~~~~~~~

When dealing with scraping projects, it is often quite convenient to get rid of
namespaces altogether and just work with element names, to write more
simple/convenient XPaths. You can use the
:meth:`Selector.remove_namespaces <parsel.selector.Selector.remove_namespaces>`
method for that.

Let's show an example that illustrates this with the Python Insider blog atom feed.

Let's download the atom feed using :mod:`requests` and create a selector:

.. skip: start

>>> import requests
>>> from parsel import Selector
>>> text = requests.get('https://feeds.feedburner.com/PythonInsider').text
>>> sel = Selector(text=text, type='xml')

.. skip: end

.. invisible-code-block: python

   sel = load_selector('python-insider.xml', type='xml')

This is how the file starts:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <?xml-stylesheet ... ?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:openSearch="http://a9.com/-/spec/opensearchrss/1.0/"
          xmlns:blogger="http://schemas.google.com/blogger/2008"
          xmlns:georss="http://www.georss.org/georss"
          xmlns:gd="http://schemas.google.com/g/2005"
          xmlns:thr="http://purl.org/syndication/thread/1.0"
          xmlns:feedburner="http://rssnamespace.org/feedburner/ext/1.0">
      ...
    </feed>

You can see several namespace declarations including a default
"http://www.w3.org/2005/Atom" and another one using the "gd:" prefix for
"http://schemas.google.com/g/2005".

We can try selecting all ``<link>`` objects and then see that it doesn't work
(because the Atom XML namespace is obfuscating those nodes)::

    >>> sel.xpath("//link")
    []

But once we call the :meth:`Selector.remove_namespaces
<parsel.selector.Selector.remove_namespaces>` method, all nodes can be accessed
directly by their names::

    >>> sel.remove_namespaces()
    >>> sel.xpath("//link")
    [<Selector xpath='//link' data='<link rel="alternate" type="text/html...'>,
     <Selector xpath='//link' data='<link rel="next" type="application/at...'>,
     ...]

If you wonder why the namespace removal procedure isn't called always by default
instead of having to call it manually, this is because of two reasons, which, in order
of relevance, are:

1. Removing namespaces requires to iterate and modify all nodes in the
   document, which is a reasonably expensive operation to perform by default
   for all documents.

2. There could be some cases where using namespaces is actually required, in
   case some element names clash between namespaces. These cases are very rare
   though.

.. _Google Base XML feed: https://support.google.com/merchants/answer/160589?hl=en&ref_topic=2473799
.. _requests: https://www.python-requests.org/


Ad-hoc namespaces references
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`~parsel.selector.Selector` objects also allow passing namespaces
references along with the query, through a ``namespaces`` argument,
with the prefixes you declare being used in your XPath or CSS query.

Let's use the same Python Insider Atom feed:

.. skip: start

>>> import requests
>>> from parsel import Selector
>>> text = requests.get('https://feeds.feedburner.com/PythonInsider').text
>>> sel = Selector(text=text, type='xml')

.. skip: end

.. invisible-code-block: python

   sel = load_selector('python-insider.xml', type='xml')

And try to select the links again, now using an "atom:" prefix
for the "link" node test::

    >>> sel.xpath("//atom:link", namespaces={"atom": "http://www.w3.org/2005/Atom"})
    [<Selector xpath='//atom:link' data='<link xmlns="http://www.w3.org/2005/A...'>,
     <Selector xpath='//atom:link' data='<link xmlns="http://www.w3.org/2005/A...'>,
     ...]

You can pass several namespaces (here we're using shorter 1-letter prefixes)::

    >>> sel.xpath("//a:entry/a:author/g:image/@src",
    ...           namespaces={"a": "http://www.w3.org/2005/Atom",
    ...                       "g": "http://schemas.google.com/g/2005"}).getall()
    ['https://img1.blogblog.com/img/b16-rounded.gif',
     'https://img1.blogblog.com/img/b16-rounded.gif',
     ...]

.. _topics-xpath-variables:

Variables in XPath expressions
------------------------------

XPath allows you to reference variables in your XPath expressions, using
the ``$somevariable`` syntax. This is somewhat similar to parameterized
queries or prepared statements in the SQL world where you replace
some arguments in your queries with placeholders like ``?``,
which are then substituted with values passed with the query.

.. invisible-code-block: python

   selector = load_selector('selectors-sample1.html')

Here's an example to match an element based on its normalized string-value::

    >>> str_to_match = "Name: My image 3"
    >>> selector.xpath('//a[normalize-space(.)=$match]',
    ...                match=str_to_match).get()
    '<a href="image3.html">Name: My image 3 <br><img src="image3_thumb.jpg"></a>'

All variable references must have a binding value when calling ``.xpath()``
(otherwise you'll get a ``ValueError: XPath error:`` exception).
This is done by passing as many named arguments as necessary.

Here's another example using a position range passed as two integers::

    >>> start, stop = 2, 4
    >>> selector.xpath('//a[position()>=$_from and position()<=$_to]',
    ...                _from=start, _to=stop).getall()
    ['<a href="image2.html">Name: My image 2 <br><img src="image2_thumb.jpg"></a>',
     '<a href="image3.html">Name: My image 3 <br><img src="image3_thumb.jpg"></a>',
     '<a href="image4.html">Name: My image 4 <br><img src="image4_thumb.jpg"></a>']

Named variables can be useful when strings need to be escaped for single
or double quotes characters. The example below would be a bit tricky to
get right (or legible) without a variable reference::

    >>> html = '''<html>
    ... <body>
    ...   <p>He said: "I don't know why, but I like mixing single and double quotes!"</p>
    ... </body>
    ... </html>'''
    >>> selector = Selector(text=html)
    >>>
    >>> selector.xpath('//p[contains(., $mystring)]',
    ...                mystring='''He said: "I don't know''').get()
    '<p>He said: "I don\'t know why, but I like mixing single and double quotes!"</p>'


Converting CSS to XPath
-----------------------

.. autofunction:: parsel.css2xpath

When you're using an API that only accepts XPath expressions, it's sometimes
useful to convert CSS to XPath. This allows you to take advantage of the
conciseness of CSS to query elements by classes and the easeness of
manipulating XPath expressions at the same time.

On those occasions, use the function :func:`~parsel.css2xpath`:

::

    >>> from parsel import css2xpath
    >>> css2xpath('h1.title')
    "descendant-or-self::h1[@class and contains(concat(' ', normalize-space(@class), ' '), ' title ')]"
    >>> css2xpath('.profile-data') + '//h2'
    "descendant-or-self::*[@class and contains(concat(' ', normalize-space(@class), ' '), ' profile-data ')]//h2"

As you can see from the examples above, it returns the translated CSS query
into an XPath expression as a string, which you can use as-is or combine to
build a more complex expression, before feeding to a function expecting XPath.


Similar libraries
=================


 * `BeautifulSoup`_ is a very popular screen scraping library among Python
   programmers which constructs a Python object based on the structure of the
   HTML code and also deals with bad markup reasonably well.

 * `lxml`_ is an XML parsing library (which also parses HTML) with a pythonic
   API based on `ElementTree`_. (lxml is not part of the Python standard
   library.). Parsel uses it under-the-hood.

 * `PyQuery`_ is a library that, like Parsel, uses `lxml`_ and
   :doc:`cssselect <cssselect:index>` under the hood, but it offers a jQuery-like API to
   traverse and manipulate XML/HTML documents.

Parsel is built on top of the `lxml`_ library, which means they're very similar
in speed and parsing accuracy. The advantage of using Parsel over `lxml`_ is
that Parsel is simpler to use and extend, unlike the `lxml`_ API which is much
bigger because the `lxml`_ library can be used for many other tasks, besides
selecting markup documents.


.. _BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
.. _lxml: https://lxml.de/
.. _PyQuery: https://pypi.python.org/pypi/pyquery
.. _ElementTree: https://docs.python.org/2/library/xml.etree.elementtree.html
