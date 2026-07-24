==============
XPath Tutorial
==============

Part 1: What is XPath?
======================

XPath is a language
-------------------

    *"XPath is a language for addressing parts of an XML document"*

    (from the `XML Path Language 1.0 <https://www.w3.org/TR/xpath/>`__
    specification)

In other words: you write an XPath expression as a string, pass it to an XPath
engine together with an XML (or HTML) document, and get back the parts of that
document it points to -- following the data model described below.

Why learn XPath?
----------------

-  with XPath, you can navigate **everywhere** inside a DOM tree
-  it's a must-have skill for accurate web data extraction
-  XPath is more powerful than CSS selectors
-  it allows selection and filtering with a fine-grained look at the
   text content
-  XPath allows complex conditioning with axes
-  XPath is extensible with custom functions (we won’t cover that in
   this tutorial though)

XPath data model
----------------

XPath's `data model <http://www.w3.org/TR/xpath/#data-model>`__ is a
tree of nodes representing a document. Nodes can be either:

-  **element nodes** (``<p>This is a paragraph</p>``),
-  or **attribute nodes** (``href="page.html"`` inside an ``<a>`` tag),
-  or **text nodes** (``"I have something to say"``),
-  or **comment nodes** (``<!-- a comment -->``),
-  (or root nodes, or namespace nodes, or processing instructions nodes
   but we will not cover them here.)

In XPath's data model, everything is a node : elements, attributes,
comments... (**but not all nodes are elements.**)

And nodes have an order, the **document order**: the order in which they
appear in the XML/HTML source.

In effect, this data model allows you to represent everything inside an
XML or HTML document, in a structured, ordered and hierarchical way.

Throughout this tutorial, we'll use the following sample HTML page to
illustrate how XPath works:

::

    <html>
    <head>
      <title>This is a title</title>
      <meta content="text/html; charset=utf-8" http-equiv="content-type">
    </head>
    <body>
      <div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>
    </body>
    </html>

Here is an ASCII tree representation of our toy HTML document for an
XPath engine, according to the data model:

::

    # 0--(ROOT)
     +-- # 1--<html>
         +-- # 2--(TXT): '\n'
         +-- # 3--<head>
         |   +-- # 4--(TXT): '\n  '
         |   +-- # 5--<title>
         |   |   +-- # 6--(TXT): 'This is a title'
         |   +-- # 7--(TXT): '\n  '
         |   +-- # 8--<meta>
         |   |   +-- # 9--(ATTR): content: 'text/html; charset=utf-8'
         |   |   +-- #10--(ATTR): http-equiv: 'content-type'
         |   +-- #11--(TXT): '\n'
         +-- #12--(TXT): '\n'
         +-- #13--<body>
         |   +-- #14--(TXT): '\n  '
         |   +-- #15--<div>
         |   |   +-- #16--(TXT): '\n    '
         |   |   +-- #17--<div>
         |   |   |   +-- #18--(TXT): '\n      '
         |   |   |   +-- #19--<p>
         |   |   |   |   +-- #20--(TXT): 'This is a paragraph.'
         |   |   |   +-- #21--(TXT): '\n      '
         |   |   |   +-- #22--<p>
         |   |   |   |   +-- #23--(TXT): 'Is this '
         |   |   |   |   +-- #24--<a>
         |   |   |   |   |   +-- #25--(ATTR): href: 'page2.html'
         |   |   |   |   |   +-- #26--(TXT): 'a link'
         |   |   |   |   +-- #27--(TXT): '?'
         |   |   |   +-- #28--(TXT): '\n      '
         |   |   |   +-- #29--<br>
         |   |   |   +-- #30--(TXT): '\n      Apparently.\n    '
         |   |   +-- #31--(TXT): '\n    '
         |   |   +-- #32--<div>
         |   |   |   +-- #33--(ATTR): class: 'second'
         |   |   |   +-- #34--(TXT): '\n      Nothing to add.\n      Except maybe this '
         |   |   |   +-- #35--<a>
         |   |   |   |   +-- #36--(ATTR): href: 'page3.html'
         |   |   |   |   +-- #37--(TXT): 'other link'
         |   |   |   +-- #38--(TXT): '. \n      '
         |   |   |   +-- #39--(COMM): ' And this comment '
         |   |   |   +-- #40--(TXT): '\n    '
         |   |   +-- #41--(TXT): '\n  '
         |   +-- #42--(TXT): '\n'
         +-- #43--(TXT): '\n'

You can see various tree branches and leaves:

-  e.g. ``<div>`` or ``<p>``: these are element nodes
-  ``(TXT)`` represent text nodes
-  ``(ATTR)`` represent attribute nodes
-  ``(COMM)`` represent comment nodes

The ``#<number>`` are the document orders of each node.

.. note::
    You can also notice that **text with only whitespace** (space and
    newlines in our example) **are proper nodes**, they do have their
    document order and can be selected with XPath.

In-browser widget and using parsel
----------------------------------

To illustrate and learn XPath, we will use an in-browser widget
allowing you to play around with XPath expressions and see the output
live.
We will also illustrate some Python pattern for data extraction with
XPath using the `parsel <https://github.com/scrapy/parsel>`__ library
which powers Scrapy selectors under the hood.
It is a Python module written on top of `lxml <http://lxml.de/>`__.

.. note::
    lxml itself is built using the C library `libxml2 <http://www.xmlsoft.org/>`__,
    which has a conformant XPath 1.0 engine.
    You should be able to run the same XPath expressions with
    any XPath 1.0 engine, and get the same results.

This tutorial only showcases XPath 1.0. (`XPath has reached version 3
<https://www.w3.org/TR/xpath-3/>`__, but you can already do a
lot with XPath 1.0 and Python. And there's no XPath>1.0 implementation
in Python today.)

When showing Python code snippets using Parsel, we assume that we have
a ``Selector`` -- called ``doc`` -- created with the HTML content, similarly
to the following:

.. code:: python

    import parsel

    htmlsample = """<html>
    <head>
      <title>This is a title</title>
      <meta content="text/html; charset=utf-8" http-equiv="content-type" />
    </head>
    <body>
      <div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br />
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>
    </body>
    </html>"""

    #
    # Below is a small "hack" to change the representation of extracted
    #  nodes when using parsel.
    # This is to represent return values as serialized HTML element or
    # string, and not parsel's wrapper objects.
    #
    parsel.Selector.__str__ = parsel.Selector.extract
    parsel.Selector.__repr__ = parsel.Selector.__str__
    parsel.SelectorList.__repr__ = lambda x: "[{}]".format(
        "\n ".join("({}) {!r}".format(i, repr(s)) for i, s in enumerate(x, start=1))
    ).replace(r"\n", "\n")

    doc = parsel.Selector(text=htmlsample)

XPath return types
------------------

When applied over a document, an XPath expression can return either:

-  a node-set -- this is the most common case, and often it's a set of
   element nodes
-  a string
-  a number (floating point)
-  a boolean

.. note::
    **When an XPath expression returns a node-set, you do get a set of
    nodes, even if there's only one node in the set.**
    With parsel, you get a ``list`` of nodes though, not a Python ``set``.

XPath expressions
-----------------

We will now take a look at some example XPath expressions to get a
feeling of how they work. We'll explain the syntax in more details later
on.

XPath expressions are passed to an XPath engine as strings.

Selecting the root node (a special case)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One of the shortest XPath expressions, ``"/"`` (a string with only a forward
slash), selects the *root node* of the document -- the invisible node whose
only child is the document element (the top-level ``<html>`` element here).

.. xpathdemo:: /

This is very similar to ``cd /`` in a Unix shell (going to the root directory).

.. warning::
    This ``"/"`` expression does not work as expected with parsel: you get an
    empty list instead of the root node. It is an lxml limitation (it works with
    libxml2 directly). In practice this rarely matters -- the root node is
    virtually never used directly.

Selecting elements
~~~~~~~~~~~~~~~~~~

Elements build the structure and hierarchy of the document. An element
in HTML (and XML) is what you see in the source code between an opening
and corresponding closing tag, and everything in between.

-  ``<title>This is a title</title>`` is a ``title`` element,
-  ``<p>Is this <a href="page2.html">a link</a>?</p>`` is a ``p``
   (paragraph) element.

Selecting elements is probably the most common use-case for XPath on
HTML documents.

Elements can have children -- the root node being the ancestor of them
all. Their children can also have children and so on. Sometimes,
elements only have one child. This hierarchy forms a family tree of nodes.

.. note::
    **Text nodes are not elements.** (They are still nodes, obviously.)
    They do not have children nodes, but they are always children
    of some element.

    Therefore, text nodes are always leaves of the document tree.

We said earlier that the document element is a child of the root node.
In fact, the document element is the only child of the root node. And
for our sample HTML document, it's the top-level ``<html>...</html>`` element.
Still, selecting it will return a single-node node-set, the XPath expression
being ``/*``:

.. xpathdemo:: /*

The asterisk here, ``*``, means "any element". And ``/*`` means "any
element under the root node". HTML documents have only one element like
this: the ``<html>`` element.

Another example: how to get ``<title>`` elements? Use ``/html/head/title``:

.. xpathdemo:: /html/head/title

Again, if you are familiar with the Unix filesystem, you probably
intuitively understand what this does:

* start from the root (of the document)

    * select the ``<html>`` node (with ``/html``)

        * select the ``<head>`` node under the ``<html>`` node
          (appending ``/head``)

            * select the ``<title>`` node under the ``<head>`` node
              (appending ``/title``)

In other words, the XPath expression represents the path from the root
node down to the target node(s). Parts of this path are read **from left to right**,
and represent a top-to-bottom direction in the document tree.

Much like a Unix filepath represents the path from the filesystem's root
to the target file(s) or directory(ies).
There's one major difference with a Unix filesystem though: in an HTML
or XML document, an element can have multiple children with the same name.
For example, the ``<div>`` just under the ``<body>`` has 2 ``<div>`` children:

.. xpathdemo:: /html/body/div/div

Another example is getting the paragraphs inside the first child of that
``<div>`` under ``<body>``, there are two of them:

.. xpathdemo:: /html/body/div/div[1]/p

Here we're introducing a **positional predicate**, ``[1]``. The ``div[1]``
part means *"the first <div> child under its parent"*.

If you recall, earlier we used a ``*`` asterisk to mean *any element*.
There are other elements with those two paragraphs under that very
``<div>``. Let's try and select all of them, regardless of their name:

.. xpathdemo:: /html/body/div/div[1]/*

.. note::
    Continuing the filesystem analogy, ``*`` is similar in effect to what
    you can do in a Unix shell to find files or directories without explicit
    full names.

See the ``<br/>`` being selected? It's an empty element (i.e. with no child
nodes) but it is there nonetheless.

Selecting text nodes
~~~~~~~~~~~~~~~~~~~~

If we stay around these ``<p>`` and ``<br>`` elements, you may have noticed
that the ASCII tree representation from the beginning also shows some text after the
``<br/>`` break: the string ``"Apparently."``. It is a text node.

Selecting text nodes is a bit different than selecting elements:
you use the special ``text()`` syntax. Let's try it by replacing the last
part of our last XPath expression, forming ``/html/body/div/div[1]/text()``:

.. xpathdemo:: /html/body/div/div[1]/text()

You may have expected only one text result, the last one, ``"Apparently."``.
But we got four! And three of them are blank even. Why is that?

In fact, HTML authors usually indent their tags with whitespace for
readability. This does not usually change the layout in your browser.
But this **whitespace counts as text nodes** for XPath's data model,
it is not stripped nor filtered.

Let's represent that ``<div>`` as a Python string as it appears in the
HTML source::

    #
    #   text node #1                       text node #2                                           text node #3
    #     <------>                           <------>                                               <------>
    '<div>\n      <p>This is a paragraph.</p>\n      <p>Is this <a href="page2.html">a link</a>?</p>\n      <br>\n  Apparently.\n    </div>'

We've marked the first three text nodes before the non-whitespace only
text node.

Another example is to get the text nodes of ``<title>`` elements
(remember that ``<title>`` is an element, and that it happens it
contains a text node, with the string content "This is a title"):

.. xpathdemo:: /html/head/title/text()

.. note::
    Again, there's only one ``<title>``, and it contains only one text node,
    but selecting text nodes in ``<title>`` returns a single string-value
    in a list, not one string.

Selecting nodes without a full, explicit path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

What we did until now is tell the XPath engine how to get to nodes,
node by node, from parent to child, from root node down to target nodes.
This assumes that you know the hierarchy of nodes beforehand.
This *can* be the case, but more often than not,
either you do not know or you do not want to indicate all the steps from
the root node down to the node(s) you are interested in (this can be
very error prone -- have you put enough ``div/div/div...``?).

XPath provides a handy shortcut when you do not know at what level you
expect your target node to be.
Say for example that we want to select all ``<p>`` paragraph elements
inside the ``<body>``. We don't *a-priori* know what their parent node is.
(For all we know, they can be anywhere under the ``<body>`` element.)
The shortcut to use is ``//`` (two forward slashes).
Let's try this: ``//body//p``

.. xpathdemo:: //body//p

So we got 2 paragraphs, what we expected.

This also works for text nodes (there are a lot of them in our sample
document!). Try ``//body//text()``:

.. xpathdemo:: //body//text()

Selecting attributes
~~~~~~~~~~~~~~~~~~~~

Elements can also have attributes.
In our sample document, we have two ``<a>`` elements, each with a
``href`` attribute. There's also a ``<meta>`` element with two
attributes: ``content`` and ``http-equiv``.

This is how you can select these attributes, with an ``@`` prefix before
the attribute name:

.. xpathdemo:: //a/@href

.. xpathdemo:: //meta/@*

The ``*`` (asterisk) here after ``@`` means the same thing as in ``/*``
except that this is for attributes, and not elements: meaning that you
want any attributes, whatever their name.

Get a string representation of an element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The XPath language also comes with a few string functions, that you can
wrap around an XPath expression selecting elements:

.. xpathdemo:: string(/html/head/title)

This example uses ``string(<xpathexpression>)``, one of several handy
`functions <https://www.w3.org/TR/xpath/#section-String-Functions>`__ in XPath.
``string()`` will concatenate all text content from the selected node
and all of its children, recursively, effectively stripping HTML tags.

You may wonder what's the difference between ``string(/html/head/title)``
and ``/html/head/title/text()`` from earlier? Here, in fact, you get the same
result because ``<title>`` only has one child text node.
(Concatenating this list of one text node is the same as getting it
directly with ``text()`` at the end.)

But string functions can be very handy when you apply them on nodes that
have multiple children and multiple text node children or descendant.
What happens when you apply ``string()`` on the document ``<body>`` for example?
You get a text representation of the document, without the tags:

.. xpathdemo:: string(//body)

Counting elements
~~~~~~~~~~~~~~~~~

We said earlier that XPath expressions could also return numbers.
One example of this is counting the number of paragraphs in the
document:

.. xpathdemo:: count(//p)

.. note::
    With parsel, you get a floating point number back, and in the form of a
    string. This is specific to parsel. Another XPath engine might return a
    native floating point number.

Another example: get the number of attributes in the document (whatever
their parent element):

.. xpathdemo:: count(//@*)

Boolean operations
~~~~~~~~~~~~~~~~~~

XPath expressions can also return booleans. This is not that useful
by itself, but it becomes handy when used in predicates (that we will
cover a bit later).

For example, testing the number of paragraphs:

.. xpathdemo:: count(//p) = 2

.. xpathdemo:: count(//p) = 42

Part 2: Location Paths: how to move inside the document tree
============================================================

A **Location path** is the most common XPath expression.
It is used to move in any direction from a starting point (*the context
node*) to any node(s) in the tree:

-  It is a string, with a series of **“location steps”**:
   ``"step1 / step2 / step3 ..."``;
-  It represents the **selection and filtering of nodes**, processed step by
   step, **from left to right**;
-  Each step is of the form ``axis :: nodetest [predicate]*``

   - an *axis* (implicit or explicit),
   - a *node test*,
   - zero or more *predicates*.

So the examples we saw earlier are (or contain) an XPath location path:
``/html/head/title``, ``//body//p`` etc.

.. tip::
    Whitespace does NOT matter in XPath.

    (Except for ``“//”`` and ``“..”``;
    ``“/   /”`` and ``“.  .”`` are syntax errors.)

    For example, the following three expressions produce the same result:

    .. code:: pycon

        >>> doc.xpath("/html/head/title")
        [(1) '<title>This is a title</title>']

    .. code:: pycon

        >>> doc.xpath("/    html   / head   /title")
        [(1) '<title>This is a title</title>']

    .. code:: pycon

        >>> doc.xpath("""
        ...     /html
        ...         /head
        ...             /title""")
        ...
        [(1) '<title>This is a title</title>']

    So **don’t be afraid to indent your XPath expressions to improve
    readability.**

Relative vs. absolute paths
---------------------------

Location paths can be relative or absolute:

-  ``"step1/step2/step3"`` is relative
-  ``"/step1/step2/step3"`` is absolute

In other words, an absolute path is a relative path starting with "/" (forward slash).
Absolute paths are relative to the root node.

.. tip::
    Use relative paths whenever possible. This prevents unexpected
    selection of duplicate nodes in loop iterations.

    For example, in our sample document, only one ``<div>`` contains
    paragraphs. Looping on each ``<div>`` and using the absolute location
    path ``//p`` will produce the same result for each iteration: returning
    ALL paragraphs in the document everytime.

    .. code:: pycon

        >>> for div in doc.xpath("//body//div"):
        ...     print(div.xpath("//p"))
        ...
        [(1) '<p>This is a paragraph.</p>'
         (2) '<p>Is this <a href="page2.html">a link</a>?</p>']
        [(1) '<p>This is a paragraph.</p>'
         (2) '<p>Is this <a href="page2.html">a link</a>?</p>']
        [(1) '<p>This is a paragraph.</p>'
         (2) '<p>Is this <a href="page2.html">a link</a>?</p>']

    Compare this with using the relative ``'p'`` or ``'./p'`` expression
    that will only look at children ``<p>`` under each ``<div>``, and only
    one of those ``<div>`` will show having paragraphs as shown below:

    .. code:: pycon

        >>> for div in doc.xpath("//body//div"):
        ...     print(div.xpath("p"))
        ...
        []
        [(1) '<p>This is a paragraph.</p>'
         (2) '<p>Is this <a href="page2.html">a link</a>?</p>']
        []

    .. code:: pycon

        >>> for div in doc.xpath("//body//div"):
        ...     print(div.xpath("./p"))
        ...
        []
        [(1) '<p>This is a paragraph.</p>'
         (2) '<p>Is this <a href="page2.html">a link</a>?</p>']
        []

Abbreviated syntax vs. full syntax
----------------------------------

What we’ve seen earlier is in fact the “`abbreviated syntax
<https://www.w3.org/TR/xpath/#path-abbrev>`__” for XPath
expressions. The full syntax is quite verbose (but you sometimes need it):

.. list-table::
   :header-rows: 1

   * - Abbreviated syntax
     - Full syntax
   * - ``/html/head/title``
     - ``/child::html /child:: head /child:: title``
   * - ``//meta/@content``
     - ``/descendant-or-self::node() /child::meta / attribute::content``
   * - ``//div/div[@class="second"]``
     - ``/descendant-or-self::node() /child::div /child::div [attribute::class = "second"]``
   * - ``//div/a/text()``
     - ``/descendant-or-self::node() /child::div /child::a /child::text()``

What are these ``child::``, ``descendant-or-self::`` and
``attribute::``, you may ask? They are axes.

Axes: moving around
-------------------

.. important::
    Remember that each step of an XPath location path is of the form
    ``AXIS :: nodetest [predicate]*``.

    The "axis" is the first part of each location path step. It can be
    explicit, or implicit in abbreviated syntax. For example, in
    ``/html/head/title``, the ``child::`` axis is omitted in each step.

    In this section, we'll use explicit axes as much as we can.

**Axes give the direction to go next, one location step at a time.**

-  ``self`` (where you are)
-  ``parent``, ``child`` (direct hop up or down the document tree)
-  ``ancestor``, ``ancestor-or-self``, ``descendant``,
   ``descendant-or-self`` (multi-hop)
-  ``following``, ``following-sibling``, ``preceding``,
   ``preceding-sibling`` (document order)
-  ``attribute``, ``namespace`` (non-element)

Stay where you are: self
~~~~~~~~~~~~~~~~~~~~~~~~

Let's assume that we have selected the first ``<div>`` element in our
sample document, the one just under the ``<body>`` element:

.. code:: pycon

    >>> first_div = doc.xpath("//body/div")[0]
    >>> first_div
    <div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>

The ``self`` axis represents *the context node*, i.e. where you are
currently in the Location Path steps. (This may not sound very useful,
but we will see later when this can be handy.)

.. code:: pycon

    >>> first_div.xpath("self::*")
    [(1) '<div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>']

``self::`` is usually seen in its abbreviated form, ``.`` (one dot), which
means ``self::node()``. Chaining ``self`` steps (``self::*/self::*`` or
``././.``) just keeps you on the same context node, so ``.`` is a compact way
of saying "right here":

.. code:: pycon

    >>> first_div.xpath(".")
    [(1) '<div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>']

Move up or down the tree: child, descendant, parent, ancestor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``child`` axis is for immediate children nodes of the context node.
Here, our context node ``<div>`` has two ``<div>`` children:

.. code:: pycon

    >>> first_div.xpath("child::*")
    [(1) '<div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>'
     (2) '<div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>']

``child`` is in fact the default axis, hence it can be omitted (e.g. we
saw that ``/html/head/title`` is equivalent of
``/child::html/child::head/child::title``.)

The ``parent`` axis is the dual of ``child``: you go up one level in the
document tree:

.. code:: pycon

    >>> first_div.xpath("parent::*")
    [(1) '<body>
      <div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>
    </body>']

There's an alias for ``parent::``: it's ``..`` (two dots, much like in a
Unix filesystem):

.. code:: pycon

    >>> first_div.xpath("..")
    [(1) '<body>
      <div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>
    </body>']

Let's simplify our ASCII tree representation from earlier to only
consider element nodes:

::

    # 0--(ROOT)
     +-- # 1--<html>
         +-- # 3--<head>
         |   +-- # 5--<title>
         |   +-- # 8--<meta>
         +-- #13--<body>
             +-- #15--<div>
                 +-- #17--<div>
                 |   +-- #19--<p>
                 |   +-- #22--<p>
                 |   |   +-- #24--<a>
                 |   +-- #29--<br>
                 +-- #32--<div>
                     +-- #35--<a>

With this simplified tree representation, this is what ``self``,
``child`` and ``parent`` select:

::

                    # 0--(ROOT)
                     +-- # 1--<html>
                         +-- # 3--<head>
                         |   +-- # 5--<title>
                         |   +-- # 8--<meta>
    parent::* ---------> +-- #13--<body>
                             |
    self::* ------------->   +-- #15--<div>
                                 |
    child::*----+----------->    +-- #17--<div>
                |                |   +-- #19--<p>
                |                |   +-- #22--<p>
                |                |   |   +-- #24--<a>
                |                |   +-- #29--<br>
                +----------->    +-- #32--<div>
                                     +-- #35--<a>

Recursively go up or down
^^^^^^^^^^^^^^^^^^^^^^^^^

The ``descendant`` axis is similar to ``child`` but also goes deeper down
the tree, looking at children of each child, recursively:

.. code:: pycon

    >>> first_div.xpath("descendant::*")
    [(1) '<div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>'
     (2) '<p>This is a paragraph.</p>'
     (3) '<p>Is this <a href="page2.html">a link</a>?</p>'
     (4) '<a href="page2.html">a link</a>'
     (5) '<br>'
     (6) '<div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>'
     (7) '<a href="page3.html">other link</a>']

You might guess already what ``ancestor`` is for: it is the dual axis of
``descendant``. It goes to the parent of the context node, the parent of
this parent, the parent of the parent of this parent, etc.

.. code:: pycon

    >>> first_div.xpath("ancestor::*")
    [(1) '<html>
    <head>
      <title>This is a title</title>
      <meta content="text/html; charset=utf-8" http-equiv="content-type">
    </head>
    <body>
      <div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>
    </body>
    </html>'
     (2) '<body>
      <div>
        <div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>
    </body>']

Special case of ``descendant-or-/ancestor-or-self`` axes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The last axes to be aware of when you need to move up or down the document
tree are ``descendant-or-self`` and ``ancestor-or-self``.
They are the same as ``descendant`` or ``ancestor`` except they also
include the context node.

.. code:: pycon

    >>> first_div.xpath("./descendant-or-self::node()/text()")
    [(1) '
        '
     (2) '
          '
     (3) 'This is a paragraph.'
     (4) '
          '
     (5) 'Is this '
     (6) 'a link'
     (7) '?'
     (8) '
          '
     (9) '
          Apparently.
        '
     (10) '
        '
     (11) '
          Nothing to add.
          Except maybe this '
     (12) 'other link'
     (13) '.
          '
     (14) '
        '
     (15) '
      ']

Move "sideways": children nodes of the same parent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If nodes can have parents, children, ancestors and descendants, they can
also have siblings (to continue the family analogy). **Siblings are
nodes that have the same parent node.**

Some siblings may come before the context node (they appear before in
the document, their order is lower), or they can come after the context
node. There are two axis for these two directions: ``preceding-sibling`` and
``following-sibling``.

Let's first select this paragraph from our sample document:
``<p>Is this <a href="page2.html">a link</a>?</p>``. It's the 2nd child
of the 1st ``<div>`` of the ``<div>`` we used above:

.. code:: python

    paragraph = first_div.xpath("child::div[1]/child::p[2]")[0]

Here we started using 2 new patterns along with the axes:

-  ``child::div`` vs. ``child::*``:

   - ``*`` means "any element node" (this is a *node-test* that we'll cover afterwards),
   - while ``child::div`` means "any child that is a ``<div>`` element".

-  ``[1]`` and ``[2]``: which mean *first* and *second* in the current
   step's node-set (this is a kind of *predicate* that we'll cover
   afterwards also)

.. code:: pycon

    >>> paragraph.xpath("preceding-sibling::*")
    [(1) '<p>This is a paragraph.</p>']

.. code:: pycon

    >>> paragraph.xpath("following-sibling::*")
    [(1) '<br>']

Again, let's see which elements were selected in our ASCII tree
representation:

::

                    # 0--(ROOT)
                     +-- # 1--<html>
                         +-- # 3--<head>
                         |   +-- # 5--<title>
                         |   +-- # 8--<meta>
                         +-- #13--<body>
                             |
                             +-- #15--<div>
                                 |
                                 +-- #17--<div>
                                 |   |
                                 |   |
    preceding-sibling::* ----------> +-- #19--<p>
                                 |   |
                                 |   |
    self::* -----------------------> +-- #22--<p>
                                 |   |   |
                                 |   |   +-- #24--<a>
                                 |   |
                                 |   |
    following-sibling::* ----------> +-- #29--<br>
                                 |
                                 |
                                 +-- #32--<div>
                                     +-- #35--<a>

Earlier we were also able to get text nodes that were siblings of these
``<p>`` elements. Why did they not get selected?

The reason is that ``child::*`` means "any child *element*", not "any node."
(Remember that text nodes are not elements.)

To also get text node siblings, you need to use either ``child::text()``
or ``child::node()``. (But we may be getting ahead of ourselves with *node tests*.)

.. code:: pycon

    >>> paragraph.xpath("following-sibling::node()")
    [(1) '
          '
     (2) '<br>'
     (3) '
          Apparently.
        ']

.. code:: pycon

    >>> paragraph.xpath("following-sibling::text()")
    [(1) '
          '
     (2) '
          Apparently.
        ']

Nodes before and after, in document order
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``preceding`` and ``following`` are two special axes that do not look at
the tree hierarchy, but work on the document order of nodes.

.. important::
    Remember, all nodes in XPath data model have an order, called the
    *document order*. Node 1 is the first node in the HTML source, node 2 is
    the node appearing next etc.

    ::

          #1    #2    #3   ...
        <html><head><title>...

.. code:: pycon

    >>> paragraph.xpath("preceding::*")
    [(1) '<head>
      <title>This is a title</title>
      <meta content="text/html; charset=utf-8" http-equiv="content-type">
    </head>'
     (2) '<title>This is a title</title>'
     (3) '<meta content="text/html; charset=utf-8" http-equiv="content-type">'
     (4) '<p>This is a paragraph.</p>']

.. code:: pycon

    >>> paragraph.xpath("following::*")
    [(1) '<br>'
     (2) '<div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>'
     (3) '<a href="page3.html">other link</a>']

This is what these axes select in our ASCII-tree representation:

::

                    # 0--(ROOT)
                     +-- # 1--<html>
                         |   |
                    +--> +-- # 3--<head>
                    |    |   |
                    +------> +-- # 5--<title>
                    |    |   |
                    +------> +-- # 8--<meta>
                    |    |
                    |    +-- #13--<body>
                    |        |
                    |        +-- #15--<div>
                    |            |
                    |            +-- #17--<div>
                    |            |   |
                    |            |   |
    preceding::* ---+--------------> +-- #19--<p>
                                 |   |
                                 |   |
    self::* -----------------------> +-- #22--<p>
                                 |   |   |
                                 |   |   +-- #24--<a>
                                 |   |
                                 |   |
    following::* -----------+------> +-- #29--<br>
                            |    |
                            |    |
                            +--> +-- #32--<div>
                            |        |
                            +------> +-- #35--<a>

.. note::
    Notice that ``preceding`` does not include ancestors and ``following``
    does not include descendants.
    This property `is mentioned in XPath specs <https://www.w3.org/TR/xpath/#axes>`__
    like this:

        *"The ancestor, descendant, following, preceding and self axes
        partition a document (ignoring attribute and namespace nodes): they
        do not overlap and together they contain all the nodes in the
        document."*

    In other words::

        document == self ∪ (ancestor ∪ preceding) ∪ (descendant ∪ following)

    (``∪`` denoting the "union" for node-sets.)

Attribute axis
~~~~~~~~~~~~~~

Attributes are nodes too, but they are special: they are **not children** of
their element. This is why none of the axes we have seen so far (``child``,
``descendant``, ``following``...) ever returned an attribute node. Attributes
live on their own axis, ``attribute``.

To reach them, use the ``attribute`` axis explicitly:

.. xpathdemo:: //a/attribute::href

Because selecting attributes is so common, the ``attribute::`` axis has a
short form: the ``@`` sign. So ``//a/@href`` means exactly the same thing as
``//a/attribute::href``:

.. xpathdemo:: //a/@href

You can select **every** attribute of an element with ``@*``, and every
attribute in the whole document with ``//@*``:

.. xpathdemo:: //@*

.. note::
    An attribute node has a *name* and a *string value*. When you extract an
    attribute with parsel, you get its value:

    .. code:: pycon

        >>> doc.xpath("//a/@href")
        [(1) 'page2.html'
         (2) 'page3.html']

Attributes are most often used inside *predicates*, to keep only the elements
that carry a given attribute (or a given attribute value). We will use them a
lot in the `Predicates`_ section below. As a taste, ``//div[@class]`` selects
the ``<div>`` elements that have a ``class`` attribute, whatever its value:

.. xpathdemo:: //div[@class]

Node tests
----------

.. important::
    A "node test" is the second part of each step in a location path.

    ::

        axis :: NODETEST [predicate]*

    Node tests select node types along the step's axis.

a node test can be:

-  a *name test*:

    -  such as ``p``, ``title`` or ``a`` for elements: ``/html/head/title``
       contains 3 steps, each with a *name test* node-test
    -  or ``href`` or ``src`` for attributes: ``/a/@href`` selects "href"
       attributes of ``<a>`` elements

-  a *node type test*:

    -  ``node()``: any node type
    -  ``text()``: text nodes
    -  ``comment()``: comment nodes
    -  ``*`` (an asterisk): the meaning depends on the axis:

       -  an ``*`` step alone selects any element node
       -  an ``@*`` selects any attribute node

.. warning::
    ``text()`` is not a function call that converts a node to it's
    text representation, it's just a test on the node type.

    Compare these two expressions:

    .. code:: pycon

        >>> paragraph.xpath("child::text()")
        [(1) 'Is this '
         (2) '?']

    .. code:: pycon

        >>> paragraph.xpath("string(self::*)")
        [(1) 'Is this a link?']

    ``child::text()`` selects all children nodes that are also text nodes.

    The "a" string is part of the ``<a>`` inside the paragraph, so it's not selected.
    It is not a direct child of the ``<p>`` element.

    Whereas ``string(self::*)`` applies to the paragraph (the context node,
    selected with ``self::*``) and recursively gets text content of
    children, children of children and so on.

Abbreviation cheatsheet
-----------------------

.. list-table::
   :header-rows: 1

   * - Abbreviated step
     - Meaning

   * - ``*`` (asterisk)
     - all **element** nodes (i.e. not text nodes, not attribute nodes).

       Remember that ``.//*`` is not the same as ``.//node()``.

       Also, there's no ``element()`` node test.

   * - ``@*``
     - ``attribute::*`` (all attribute nodes)

   * - ``//``
     - ``/descendant-or-self::node()/`` (exactly this, nothing more, nothing less)

       so ``//*`` is not the same as ``/descendant-or-self::*``

   * - ``.`` (a single dot)
     - ``self::node()``, the context node; useful for making XPaths relative,
       e.g. ``.//tr``

   * - ``..`` (2 dots)
     - ``parent::node()``

Why ``//*`` is not ``/descendant-or-self::*``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The abbreviation ``//`` is a frequent source of confusion. It does **not**
expand to ``/descendant-or-self::``; it expands to
``/descendant-or-self::node()/`` -- note the ``node()`` node test *and* the
trailing slash, which introduces another step.

So ``//*`` is really::

    /descendant-or-self::node()/child::*

which reads as "every element that is the child of any node", i.e. every
element in the document.

``/descendant-or-self::*``, on the other hand, is a **single step**: "the
context node or any of its descendants, provided it is an element".

From the root node these two happen to select the same set (the root is not an
element, so both return every element). The difference becomes visible as soon
as you use them **relative to an element**, because ``descendant-or-self``
includes the context node itself, while the ``child::*`` step at the end of
``.//*`` never can:

.. code:: pycon

    >>> paragraph = doc.xpath("//p[2]")[0]
    >>> paragraph.xpath(".//*")  # descendants only
    [(1) '<a href="page2.html">a link</a>']
    >>> paragraph.xpath("descendant-or-self::*")  # the <p> itself, then its descendants
    [(1) '<p>Is this <a href="page2.html">a link</a>?</p>'
     (2) '<a href="page2.html">a link</a>']

This is also why ``.//node()`` and ``.//*`` differ: ``*`` is a name test that
only matches elements, while ``node()`` matches every node type.

Predicates
----------

.. important::
    Predicates are the last part of each step in a location path. Predicates
    are optional.
    ::

        axis :: nodetest [PREDICATE]*

    They are used to further filter nodes on properties that cannot be
    expressed with the step's axis and node test.

Remember that XPath location paths work step by step. Each step produces
a node-set for each node from the previous step's node-set, with
possibly more than 1 node in each node set.

You may not be interested in all nodes from a node test. And predicates
are used to tell the XPath engine the condition(s) they should meet.

The syntax for predicates is simple: just surround conditions within
square brackets. What's inside the square brackets can be:

-  a number (see positional predicates below)
-  a location path: the predicate will select nodes for which the
   location path matches at least a node
-  a boolean operation: for example to test a condition on text content
   or count of children

Positional predicates
~~~~~~~~~~~~~~~~~~~~~

The first use-case is selecting nodes based on their position in a
node-set. (Node-sets order depends on the axis, but let's consider that
the order of a node in a node-set is the document order.)

Remember the two paragraphs in the ``<div>`` we looked at
earlier:

.. code:: pycon

    >>> doc.xpath("//body/div/div/p")
    [(1) '<p>This is a paragraph.</p>'
     (2) '<p>Is this <a href="page2.html">a link</a>?</p>']

Let's say that we are not interested in the two paragraphs but only
the first one. You would use ``[1]`` as predicate:

.. xpathdemo:: //body/div/div/p[1]

.. warning::
    Positions in XPath start from 1, not 0.

If you want the last node in a node-set, you can use ``last()``:

.. xpathdemo:: //body/div/div[last()]

.. warning::
    Because location paths work step by step, from left to right,
    positional predicates are about the **position of a node in a node-set
    produced by the current step**,
    not about the position of the node in the document tree.

    For example, ``//body//div[1]`` is NOT the first ``<div>`` under the
    ``<body>`` element; it will select **all** ``<div>`` that are the first
    child of their parent:

    .. xpathdemo:: //body//div[1]

    This becomes more apparent when you expand the expression to its
    full syntax::

        /descendant-or-self::node()
            /child::body
                /descendant-or-self::node()
                                       ^
                                       |
                    # first child of this parent
                    /child::div[1]

    You can however select the first ``<div>`` (in document order)
    in a ``<body>`` using parentheses to group nodes into a new node-set:

    - first select all ``<div>`` elements -- ``//body//div``,
    - then group them -- ``( //body//div )``,
    - and finally select the first one -- ``( //body//div ) [1]``,

    .. xpathdemo:: ( //body//div ) [1]

Position ranges
^^^^^^^^^^^^^^^

Sometimes you need more than one node in a node-set but not all of them.
For that you can use boolean expression in your predicate in conjunction
with the ``position()`` function that returns the node's position.

Let's change our sample HTML document a bit to include a list of five items.
Say we need all but the 1st and last one.
You can use ``[position()>1 and position()<last()]``:

.. xpathdemo:: //body//div//li[position()>1 and position()<last()]

    <html>
    <body>
      <div>
        <div>
          <ol>
           <li>first item</li>
           <li>second item</li>
           <li>third item</li>
           <li>fourth item</li>
           <li>fifth item</li>
          </ol>
        </div>
        <div class="second">
          Nothing to add.
          Except maybe this <a href="page3.html">other link</a>.
          <!-- And this comment -->
        </div>
      </div>
    </body>
    </html>

``//body//div//li[position()>1 and position()<last()]`` correctly
selects the 2nd, 3rd and 4th items.

Location paths as predicates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Location paths can also serve as predicates within a parent location path.

It can happen that your HTML markup does not distinguish the elements
you are after with any "class" or "id" attributes, but maybe these
elements have a structural feature that you can use to identify them.

For example, a ``<table>`` element may have rows -- ``table/tr`` --
with or without link anchors in them.
Within each ``<tr>`` row, ``td/a`` selects something on some rows,
nothing for others:

.. xpathdemo:: //table/tr [ td/a ]

    <html>
    <body>
      <div>
        <div>
          <table>
           <tr><td>first row</td></tr>
           <tr><td>second row with <a href="http://www.example.com/2">a link</a></td></tr>
           <tr><td>third row</td></tr>
           <tr><td>fourth row with <a href="http://www.example.com/4">another link</a></td></tr>
          </table>
        </div>
      </div>
    </body>
    </html>

Boolean predicates
~~~~~~~~~~~~~~~~~~

We saw boolean predicates earlier with positional ranges. But you can
craft complex boolean filters based on any features of nodes; structural
information on children or parent nodes, text values, position, etc.

A simple example could be selecting a ``<table>`` that has a specific
number of rows, say, 5. You can simply count the number of rows:

.. xpathdemo:: //table[ count(tr)=5 ]

    <html>
    <body>
      <div>
        <div>
          <table>
           <tr><td>first row</td></tr>
           <tr><td>second row</td></tr>
           <tr><td>third row</td></tr>
          </table>
        </div>
        <div>
          <table>
           <tr><td>first row</td></tr>
           <tr><td>second row</td></tr>
           <tr><td>third row</td></tr>
           <tr><td>fourth row</td></tr>
           <tr><td>fifth row</td></tr>
          </table>
        </div>
      </div>
    </body>
    </html>

Special case of string value tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

XPath also allows comparing string values of nodes within predicates.
If you use an equality operation with a location path and a string,
each node of the location path will be converted to its string value
and then compared with the string value to match.

This may sound more obscure than it is. Say for example that you have
two tables, with different headers. You know the string value
of the header in the table you want, "The header I want."

::

        <div>
          <table>
           <tr><th>The header I want</th></tr>
           <tr><td>second row</td></tr>
           <tr><td>third row</td></tr>
          </table>
        </div>
        <div>
          <table>
           <tr><th>Another header I do NOT want</th></tr>
           <tr><td>second row</td></tr>
           <tr><td>third row</td></tr>
           <tr><td>fourth row</td></tr>
           <tr><td>fifth row</td></tr>
          </table>
        </div>

To select the different headers, you would use ``//table/tr/th``.
You want the ``<table>`` so you can move the ``tr/th`` part inside
a predicate and compare it with string "The header I want".

.. xpathdemo:: //table[ tr/th = "The header I want" ]

    <html>
    <body>
      <div>
        <div>
          <table>
           <tr><th>The header I want</th></tr>
           <tr><td>second row</td></tr>
           <tr><td>third row</td></tr>
          </table>
        </div>
        <div>
          <table>
           <tr><th>Another header I do NOT want</th></tr>
           <tr><td>second row</td></tr>
           <tr><td>third row</td></tr>
           <tr><td>fourth row</td></tr>
           <tr><td>fifth row</td></tr>
          </table>
        </div>
      </div>
    </body>
    </html>

This kind of predicates also works for attribute values, e.g. testing
links to some website::

    //body//p [ a/@href="http://www.example.com" ]

Special trick for testing multiple node names
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a predicate you can also test the current node of the node-set.
For example if you want to test for several wanted element names.
This is when ``self::`` axis can be helpful.

One example is testing different kind of lists, ordered or unordered:

.. xpathdemo:: //body//*[self::ul or self::ol]//li

    <html>
    <body>
      <div>
        <div>
          <ol>
           <li>first ordered item</li>
           <li>second ordered item</li>
           <li>third ordered item</li>
          </ol>
        </div>
        <div>
          <ul>
           <li>first unordered item</li>
           <li>second unordered item</li>
           <li>third unordered item</li>
          </ul>
        </div>
      </div>
    </body>
    </html>

.. note::
    Here we saw that predicates can also appear in the middle of the location
    path. Indeed, predicates are an (optional) part of each location step.

Nested predicates
~~~~~~~~~~~~~~~~~

We said that location paths can be used as predicate. And location paths
can have predicates. So it's possible to end up with nested predicates.
(And that's ok.)

.. code:: pycon

    >>> #                <------predicate --------->
    >>> #                    <-nested predicate->
    >>> doc.xpath('//div[p  [a/@href="page2.html"]  ]')
    [(1) '<div>
          <p>This is a paragraph.</p>
          <p>Is this <a href="page2.html">a link</a>?</p>
          <br>
          Apparently.
        </div>']

In fact, the above is equivalent to ``//div[p/a/@href="page2.html"]``
with no nesting:

    .. xpathdemo:: //div[p  [a/@href="page2.html"]  ]

    .. xpathdemo:: //div[p/a/@href="page2.html"]

Order of predicates is important
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can have multiple predicates in sequence per step, each within its
``[]`` brackets, i.e. steps in the form of
``axis::nodetest[predicate#1][predicate#2][predicate#3]...``.

Predicates are processed in order, from left to right. And the output of
one predicate is fed into the next predicate filter, much like steps
produce node-sets for the next step to process.

So **the order of predicates is important.**

The following 2 location paths produce different results:

- ``//div[@class="second"][2]``: will output one ``<div>``
- ``//div[2][@class="second"]``: will select **nothing**

See for yourself:

.. xpathdemo:: //div[2][@class="second"]

.. xpathdemo:: //div[@class="second"][2]

The second produces nothing indeed. Why is that?

``//div[2][@class="second"]`` looks at ``div`` elements that are the 2nd
child of their parent.
``div`` means ``child::div``, and ``[2]`` will select the 2nd node in the current node-set.
In our document this happens only once.
The final predicate, ``[@class="second"]``, filters nodes that have a
"class" attribute with value "second".
This happens to be valid for that 2nd child ``div``.

On the contrary, ``//div[@class="second"][2]`` will first produce
``//div[@class="second"]``, which only produces single-node node-sets
(again, there's only one ``div`` with "class" attribute with value
"second"). So the subsequent ``[2]`` predicate will never match with
single-node node-sets (you cannot select the 2nd element of a 1-element list)

.. warning::
    Beware of ``position()`` in chained predicates.

    Much like ``[...][2]`` is different from ``[2][...]``, if you chain
    positional predicates, remember that the position is relative to
    the node-set processed by the previous predicate.

    For example, we saw that ``position()>1`` would filter out the first
    nodes in a node-set. Chaining ``[position()>1]`` will remove the first
    node each time it's used:

    .. xpathdemo:: //ol/li[position()>1][position()>1][position()>1]

        <html>
        <body>
          <div>
            <ol>
              <li>first item</li>
              <li>second item</li>
              <li>third item</li>
              <li>fourth item</li>
              <li>fifth item</li>
            </ol>
          </div>
        </body>
        </html>

String functions
----------------

So far we have mostly *selected* nodes. XPath can also *compute* values from
them, thanks to a small standard library of functions. The ones you will reach
for the most when scraping work on strings.

.. important::
    A node test like ``text()`` is **not** a function; it selects text nodes.
    ``string()``, ``normalize-space()``, ``contains()``... on the other hand
    are real functions that take arguments and return a string, a number or a
    boolean.

``string()``: the string value of a node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``string(node)`` returns the *string value* of a node: for an element, that is
the concatenation of **all** its descendant text nodes, in document order.
This is the easiest way to get "all the text under this element" as a single
string, even when it is split by inline tags:

.. xpathdemo:: string(//p[2])

Compare this with ``//p[2]/text()``, which returns the direct text-node
children **separately** and skips the text inside ``<a>``:

.. code:: pycon

    >>> doc.xpath("string(//p[2])").get()
    'Is this a link?'
    >>> doc.xpath("//p[2]/text()").getall()
    ['Is this ', '?']

.. warning::
    ``string()`` (and, as we will see, ``normalize-space()``) applied to a
    **node-set** only looks at the **first node in document order**. Everything
    else is silently ignored:

    .. code:: pycon

        >>> doc.xpath("string(//p)").get()  # first <p> only
        'This is a paragraph.'

    To get the string value of *each* node, apply the function per node instead,
    for instance by looping (see `Loop on elements (table rows, lists)`_) or
    with ``.getall()`` on ``text()``.

``normalize-space()``: trim and collapse whitespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

HTML is full of insignificant whitespace: indentation, newlines, runs of
spaces. ``normalize-space()`` strips leading and trailing whitespace and
collapses every inner run of whitespace to a single space. It is invaluable for
cleaning up extracted text:

.. xpathdemo:: normalize-space(//div[@class="second"])

Called with no argument, ``normalize-space()`` operates on the string value of
the context node, which makes it very handy inside a loop:

.. code:: pycon

    >>> for paragraph in doc.xpath("//p"):
    ...     print(repr(paragraph.xpath("normalize-space()").get()))
    ...
    'This is a paragraph.'
    'Is this a link?'

Testing the content: ``contains()`` and ``starts-with()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``contains(haystack, needle)`` and ``starts-with(string, prefix)`` return a
boolean. They are most useful **inside predicates**, to filter nodes on their
text or on an attribute value.

Keep only the links whose ``href`` contains ``page2``:

.. xpathdemo:: //a[contains(@href, "page2")]

A very common idiom combines ``contains()`` with the string value of an element
(``.``) to find elements "containing some text":

.. xpathdemo:: //p[contains(., "paragraph")]

.. tip::
    ``contains(@class, "foo")`` is a classic way to match one class among many,
    but it also matches ``foobar``. To match a whole class token, test against
    the class value padded with spaces:
    ``contains(concat(" ", normalize-space(@class), " "), " foo ")``. This is
    exactly what CSS selectors compile to (see `CSS Selectors`_).

More string helpers
~~~~~~~~~~~~~~~~~~~~

XPath 1.0 ships a few more string functions worth knowing:

.. list-table::
   :header-rows: 1

   * - Function
     - Returns

   * - ``concat(s1, s2, ...)``
     - The concatenation of its arguments.

   * - ``string-length(s)``
     - The number of characters in ``s``.

   * - ``substring(s, start[, length])``
     - A substring of ``s`` (**1-based** positions).

   * - ``substring-before(s, sep)`` / ``substring-after(s, sep)``
     - The part of ``s`` before / after the first ``sep``.

   * - ``translate(s, from, to)``
     - ``s`` with each character of ``from`` replaced by the character at the
       same position in ``to`` (a poor man's lowercasing tool).

.. note::
    XPath also has *number* functions (``count()``, ``sum()``, ``round()``,
    ``floor()``, ``ceiling()``) and *boolean* functions (``not()``,
    ``boolean()``, ``true()``, ``false()``). We already met ``count()`` and
    ``last()`` in the `Predicates`_ section.

    When a function returns a number, parsel gives it back to you as a string
    (e.g. ``count(//a)`` yields ``'2.0'``); the in-browser widget above shows
    it as ``2``. Either way it is the same value.

Part 3: Use-cases for web scraping
==================================

Parts 1 and 2 covered XPath the *language*. This part is a cookbook of the
patterns that come up again and again when you extract data from real pages
with parsel and Scrapy.

Throughout this part we use parsel's practical extraction API:

- ``.get()`` returns the first match as a string (or ``None``),
- ``.getall()`` returns every match as a list of strings,
- ``.attrib`` gives a mapping of the attributes of the first matched element.

Text extraction
---------------

There are two complementary ways to pull text out of an element:

- ``text()`` selects the **direct** text-node children, each on its own,
- ``string(.)`` (or ``normalize-space(.)``) returns **all** the text underneath
  it, joined into one string.

.. code:: pycon

    >>> doc.xpath("//p[2]/text()").getall()  # direct text nodes, split
    ['Is this ', '?']
    >>> doc.xpath("//p[2]//text()").getall()  # every descendant text node
    ['Is this ', 'a link', '?']
    >>> doc.xpath("string(//p[2])").get()  # everything, joined
    'Is this a link?'

Use ``//text()`` (or ``.//text()`` relative to an element) when you want to
keep the pieces, and ``string(.)`` / ``normalize-space(.)`` when you want a
single, clean string:

.. code:: pycon

    >>> doc.xpath('normalize-space(//div[@class="second"])').get()
    'Nothing to add. Except maybe this other link.'

.. tip::
    Prefer ``normalize-space()`` over calling Python's ``str.strip()`` on the
    result: it also collapses the newlines and indentation that HTML sources are
    riddled with, in a single step.

Attributes extraction
---------------------

To read an attribute value, select it with ``@name`` and extract it:

.. code:: pycon

    >>> doc.xpath("//a/@href").getall()
    ['page2.html', 'page3.html']
    >>> doc.xpath("//a/@href").get()
    'page2.html'

parsel also exposes attributes as a Python mapping through ``.attrib``, which is
often more readable when you already have an element in hand:

.. code:: pycon

    >>> link = doc.xpath("//a")[0]
    >>> link.attrib["href"]
    'page2.html'
    >>> link.attrib.get("rel")  # missing attributes don't raise
    >>> doc.css("a::attr(href)").getall()  # the CSS equivalent
    ['page2.html', 'page3.html']

Attribute names extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you care about the attribute *names* rather than their values -- for
instance to discover ``data-*`` attributes. Select the attribute nodes with
``@*`` and read their name with the ``name()`` function:

.. code:: pycon

    >>> doc.xpath("//meta/@*").getall()  # attribute values
    ['text/html; charset=utf-8', 'content-type']
    >>> doc.xpath("name(//meta/@*[1])").get()  # name of the first attribute
    'content'

Loop on elements (table rows, lists)
------------------------------------

Repeated structures -- table rows, list items, cards -- are the bread and butter
of scraping. The pattern is always the same: select the repeating elements,
then iterate and extract from **each** one with a **relative** XPath.

.. code:: pycon

    >>> products = parsel.Selector(text="""
    ...     <ul class="products">
    ...       <li><span class="name">Laptop</span><span class="price">1200</span></li>
    ...       <li><span class="name">Mouse</span><span class="price">25</span></li>
    ...     </ul>""")
    ...
    >>> for li in products.xpath('//ul[@class="products"]/li'):
    ...     name = li.xpath('.//span[@class="name"]/text()').get()
    ...     price = li.xpath('.//span[@class="price"]/text()').get()
    ...     print(name, price)
    ...
    Laptop 1200
    Mouse 25

.. warning::
    Inside the loop, the leading dot in ``.//span`` matters a lot. Without it,
    ``//span`` is **absolute**: it restarts from the document root and returns
    the same nodes on every iteration, ignoring the current ``li``:

    .. code:: pycon

        >>> for li in products.xpath("//li"):
        ...     print(li.xpath('//span[@class="name"]/text()').get())  # BUG: no dot
        ...
        Laptop
        Laptop

    This is the single most common XPath mistake in scraping. When you loop,
    make your inner expressions **relative** with a leading ``.``.

CSS Selectors
-------------

parsel lets you use CSS selectors too, via ``.css()``. Under the hood they are
translated to XPath by the :doc:`cssselect <cssselect:index>` library, so CSS is
really a friendlier syntax for a subset of what XPath can do. You can even see
the translation:

.. code:: pycon

    >>> from parsel import css2xpath
    >>> css2xpath("div.second > a")
    "descendant-or-self::div[@class and contains(concat(' ', normalize-space(@class), ' '), ' second ')]/a"

CSS is more concise for the common cases -- classes, ids, descendants, child
combinators -- and parsel adds the non-standard ``::text`` and ``::attr(name)``
pseudo-elements so you can extract without dropping back to XPath:

.. code:: pycon

    >>> doc.css("div.second a::attr(href)").getall()
    ['page3.html']
    >>> doc.css("title::text").get()
    'This is a title'

You can also **mix** both languages by chaining, using each where it shines --
CSS to reach a container, XPath for the parts CSS cannot express (text
predicates, axes, positions):

.. code:: pycon

    >>> doc.css("div.second").xpath(".//a/@href").get()
    'page3.html'

.. note::
    CSS selectors cannot do everything XPath can: there is no way in CSS to
    select by text content, to walk *up* to an ancestor, or to reach preceding
    siblings. When you hit those walls, switch to XPath.

Element boundaries & XPath buckets (advanced)
---------------------------------------------

Some pages are "flat": instead of wrapping each group in its own container, they
put headings and their content side by side as siblings.

.. code:: html

    <div class="content">
      <h2>Fruits</h2>
      <p>Apple</p>
      <p>Banana</p>
      <h2>Vegetables</h2>
      <p>Carrot</p>
    </div>

There is no element that contains "everything under *Fruits*", so a plain
descendant query cannot group the paragraphs by heading. The trick is to
identify each paragraph's *bucket* by **counting the headings before it** with
``count(preceding-sibling::h2)``:

.. xpathdemo:: //p[count(preceding-sibling::h2)=1]

    <html>
    <body>
      <div class="content">
        <h2>Fruits</h2>
        <p>Apple</p>
        <p>Banana</p>
        <h2>Vegetables</h2>
        <p>Carrot</p>
      </div>
    </body>
    </html>

Every ``<p>`` that has exactly one ``<h2>`` before it belongs to the first
heading. Iterating over the headings gives you the groups:

.. code:: pycon

    >>> flat_html = """
    ...     <div class="content">
    ...       <h2>Fruits</h2>
    ...       <p>Apple</p>
    ...       <p>Banana</p>
    ...       <h2>Vegetables</h2>
    ...       <p>Carrot</p>
    ...     </div>"""
    ...
    >>> sel = parsel.Selector(text=flat_html)
    >>> for i, h2 in enumerate(sel.xpath("//h2"), start=1):
    ...     title = h2.xpath("normalize-space()").get()
    ...     items = sel.xpath(f"//p[count(preceding-sibling::h2)={i}]/text()").getall()
    ...     print(title, "->", items)
    ...
    Fruits -> ['Apple', 'Banana']
    Vegetables -> ['Carrot']

Related tools for the same problem are the sibling axes
(``following-sibling::``, ``preceding-sibling::``) and positional predicates,
which we covered earlier.

EXSLT extensions
----------------

libxml2 (and therefore parsel, lxml and Scrapy) supports a couple of
`EXSLT <https://exslt.github.io/>`__ extension namespaces on top of plain
XPath 1.0. parsel registers them for you under two prefixes:

- ``re`` -- `regular expressions <https://exslt.github.io/regexp/>`__,
- ``set`` -- `set operations <https://exslt.github.io/set/>`__.

The most useful one is ``re:test()``, which filters nodes with a regular
expression -- far more powerful than ``contains()`` or ``starts-with()``:

.. code:: pycon

    >>> links = parsel.Selector(
    ...     text="<html><body>"
    ...     '<a href="page2.html">a</a>'
    ...     '<a href="page3.html">b</a>'
    ...     '<a href="contact.html">c</a>'
    ...     "</body></html>"
    ... )
    >>> links.xpath(r'//a[re:test(@href, "page\d")]/@href').getall()
    ['page2.html', 'page3.html']
    >>> links.xpath(r'//a[re:test(@href, "PAGE\d", "i")]/@href').getall()  # case-insensitive
    ['page2.html', 'page3.html']

The ``set`` namespace helps when you need to subtract one node-set from another,
for example to collect the ``itemprop`` of an element while excluding those that
belong to nested scopes. See :ref:`the selectors documentation
<topics-selectors>` for a worked ``set:difference`` example.

.. note::
    EXSLT functions are **not** part of standard XPath 1.0, so the in-browser
    widget in this tutorial (which uses the browser's native engine) does not
    understand them. They do work in parsel, lxml and Scrapy.

Summary of tips
===============

.. tip::
    -  Use relative XPath expressions whenever possible
    -  Know your axes!
    -  Don't forget that XPath has ``string()`` and ``normalize-space()``
       functions
    -  **text() is a node test**, not a function call
    -  CSS selectors are very handy, easier to maintain, but also less
       powerful than XPath
