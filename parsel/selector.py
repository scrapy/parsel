"""
XPath selectors based on lxml
"""

import typing
from typing import Any, Dict, List, Optional, Mapping, Pattern, Union

from lxml import etree, html
from lxml.html.clean import Cleaner  # pylint: disable=no-name-in-module
import html_text

from .utils import flatten, iflatten, extract_regex, shorten
from .csstranslator import HTMLTranslator, GenericTranslator

_SelectorType = typing.TypeVar("_SelectorType", bound="Selector")


class CannotRemoveElementWithoutRoot(Exception):
    pass


class CannotRemoveElementWithoutParent(Exception):
    pass


class SafeXMLParser(etree.XMLParser):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("resolve_entities", False)
        super().__init__(*args, **kwargs)


_ctgroup = {
    "html": {
        "_parser": html.HTMLParser,
        "_csstranslator": HTMLTranslator(),
        "_tostring_method": "html",
    },
    "xml": {
        "_parser": SafeXMLParser,
        "_csstranslator": GenericTranslator(),
        "_tostring_method": "xml",
    },
}


def _st(st: Optional[str]) -> str:
    if st is None:
        return "html"
    elif st in _ctgroup:
        return st
    else:
        raise ValueError(f"Invalid type: {st}")


def create_root_node(text, parser_cls, base_url=None):
    """Create root node for text using given parser class."""
    body = text.strip().replace("\x00", "").encode("utf8") or b"<html/>"
    parser = parser_cls(recover=True, encoding="utf8")
    root = etree.fromstring(body, parser=parser, base_url=base_url)
    if root is None:
        root = etree.fromstring(b"<html/>", parser=parser, base_url=base_url)
    return root


class SelectorList(List[_SelectorType]):
    """
    The :class:`SelectorList` class is a subclass of the builtin ``list``
    class, which provides a few additional methods.
    """

    @typing.overload
    def __getitem__(self, pos: int) -> _SelectorType:
        pass

    @typing.overload
    def __getitem__(self, pos: slice) -> "SelectorList[_SelectorType]":
        pass

    def __getitem__(
        self, pos: Union[int, slice]
    ) -> Union[_SelectorType, "SelectorList[_SelectorType]"]:
        o = super().__getitem__(pos)
        return self.__class__(o) if isinstance(pos, slice) else o

    def __getstate__(self) -> None:
        raise TypeError("can't pickle SelectorList objects")

    def xpath(
        self,
        xpath: str,
        namespaces: Optional[Mapping[str, str]] = None,
        **kwargs,
    ) -> "SelectorList[_SelectorType]":
        """
        Call the ``.xpath()`` method for each element in this list and return
        their results flattened as another :class:`SelectorList`.

        ``query`` is the same argument as the one in :meth:`Selector.xpath`

        ``namespaces`` is an optional ``prefix: namespace-uri`` mapping (dict)
        for additional prefixes to those registered with ``register_namespace(prefix, uri)``.
        Contrary to ``register_namespace()``, these prefixes are not
        saved for future calls.

        Any additional named arguments can be used to pass values for XPath
        variables in the XPath expression, e.g.::

            selector.xpath('//a[href=$url]', url="http://www.example.com")
        """
        return self.__class__(
            flatten([x.xpath(xpath, namespaces=namespaces, **kwargs) for x in self])
        )

    def css(self, query: str) -> "SelectorList[_SelectorType]":
        """
        Call the ``.css()`` method for each element in this list and return
        their results flattened as another :class:`SelectorList`.

        ``query`` is the same argument as the one in :meth:`Selector.css`
        """
        return self.__class__(flatten([x.css(query) for x in self]))

    def re(
        self, regex: Union[str, Pattern[str]], replace_entities: bool = True
    ) -> List[str]:
        """
        Call the ``.re()`` method for each element in this list and return
        their results flattened, as a list of strings.

        By default, character entity references are replaced by their
        corresponding character (except for ``&amp;`` and ``&lt;``.
        Passing ``replace_entities`` as ``False`` switches off these
        replacements.
        """
        return flatten([x.re(regex, replace_entities=replace_entities) for x in self])

    @typing.overload
    def re_first(
        self,
        regex: Union[str, Pattern[str]],
        default: None = None,
        replace_entities: bool = True,
    ) -> Optional[str]:
        pass

    @typing.overload
    def re_first(
        self,
        regex: Union[str, Pattern[str]],
        default: str,
        replace_entities: bool = True,
    ) -> str:
        pass

    def re_first(
        self,
        regex: Union[str, Pattern[str]],
        default: Optional[str] = None,
        replace_entities: bool = True,
    ) -> Optional[str]:
        """
        Call the ``.re()`` method for the first element in this list and
        return the result in an string. If the list is empty or the
        regex doesn't match anything, return the default value (``None`` if
        the argument is not provided).

        By default, character entity references are replaced by their
        corresponding character (except for ``&amp;`` and ``&lt;``.
        Passing ``replace_entities`` as ``False`` switches off these
        replacements.
        """
        for el in iflatten(
            x.re(regex, replace_entities=replace_entities) for x in self
        ):
            return el
        return default

    def getall(
        self,
        text: bool = False,
        cleaner: Union[str, None, Cleaner] = "auto",
        guess_punct_space: bool = True,
        guess_layout: bool = True,
    ) -> List[str]:
        """
        Call the ``.get()`` method for each element is this list and return
        their results flattened, as a list of strings.

        ``text``, ``cleaner``, ``guess_punct_space`` and ``guess_layout``
        options are passed to :meth:`~.Selector.get`; see
        :meth:`~.Selector.get` for more details.
        """
        return [
            x.get(
                text=text,
                cleaner=cleaner,
                guess_punct_space=guess_punct_space,
                guess_layout=guess_layout,
            )
            for x in self
        ]

    extract = getall

    # TODO: bring types back
    # @typing.overload
    # def get(self, default: None = None) -> Optional[str]:
    #     pass
    #
    # @typing.overload
    # def get(self, default: str) -> str:
    #     pass
    def get(
        self,
        default: Optional[str] = None,
        text: bool = False,
        cleaner: Union[str, None, Cleaner] = "auto",
        guess_punct_space: bool = True,
        guess_layout: bool = True,
    ) -> Optional[str]:
        """
        Return the result of ``.get()`` for the first element in this list.
        If the list is empty, return the ``default`` value.

        ``text``, ``cleaner``, ``guess_punct_space`` and ``guess_layout``
        options are passed to :meth:`Selector.get`; see :meth:`~.Selector.get`
        for more details.
        """
        for x in self:
            return x.get(
                text=text,
                cleaner=cleaner,
                guess_punct_space=guess_punct_space,
                guess_layout=guess_layout,
            )
        return default

    extract_first = get

    @property
    def attrib(self) -> Mapping[str, str]:
        """Return the attributes dictionary for the first element.
        If the list is empty, return an empty dict.
        """
        for x in self:
            return x.attrib
        return {}

    def remove(self) -> None:
        """
        Remove matched nodes from the parent for each element in this list.
        """
        for x in self:
            x.remove()


class Selector:
    """
    :class:`Selector` allows you to select parts of an XML or HTML text using CSS
    or XPath expressions and extract data from it.

    ``text`` is a `str`` object

    ``type`` defines the selector type, it can be ``"html"``, ``"xml"`` or ``None`` (default).
    If ``type`` is ``None``, the selector defaults to ``"html"``.

    ``base_url`` allows setting a URL for the document. This is needed when looking up external entities with relative paths.
    See [`lxml` documentation](https://lxml.de/api/index.html) ``lxml.etree.fromstring`` for more information.
    """

    __slots__ = [
        "text",
        "namespaces",
        "type",
        "_expr",
        "root",
        "__weakref__",
        "_parser",
        "_csstranslator",
        "_tostring_method",
    ]

    _default_type: Optional[str] = None
    _default_namespaces = {
        "re": "http://exslt.org/regular-expressions",
        # supported in libxslt:
        # set:difference
        # set:has-same-node
        # set:intersection
        # set:leading
        # set:trailing
        "set": "http://exslt.org/sets",
    }
    _lxml_smart_strings = False
    selectorlist_cls = SelectorList["Selector"]
    _text_cleaner = html_text.cleaner
    _html_cleaner = Cleaner()

    def __init__(
        self,
        text: Optional[str] = None,
        type: Optional[str] = None,
        namespaces: Optional[Mapping[str, str]] = None,
        root: Optional[Any] = None,
        base_url: Optional[str] = None,
        _expr: Optional[str] = None,
    ) -> None:
        self.type = st = _st(type or self._default_type)
        self._parser = _ctgroup[st]["_parser"]
        self._csstranslator = _ctgroup[st]["_csstranslator"]
        self._tostring_method = _ctgroup[st]["_tostring_method"]

        if text is not None:
            if not isinstance(text, str):
                msg = f"text argument should be of type str, got {text.__class__}"
                raise TypeError(msg)
            root = self._get_root(text, base_url)
        elif root is None:
            raise ValueError("Selector needs either text or root argument")

        self.namespaces = dict(self._default_namespaces)
        if namespaces is not None:
            self.namespaces.update(namespaces)
        self.root = root
        self._expr = _expr

    def __getstate__(self) -> Any:
        raise TypeError("can't pickle Selector objects")

    def _get_root(self, text: str, base_url: Optional[str] = None) -> Any:
        return create_root_node(text, self._parser, base_url=base_url)

    def xpath(
        self: _SelectorType,
        query: str,
        namespaces: Optional[Mapping[str, str]] = None,
        **kwargs,
    ) -> SelectorList[_SelectorType]:
        """
        Find nodes matching the xpath ``query`` and return the result as a
        :class:`SelectorList` instance with all elements flattened. List
        elements implement :class:`Selector` interface too.

        ``query`` is a string containing the XPATH query to apply.

        ``namespaces`` is an optional ``prefix: namespace-uri`` mapping (dict)
        for additional prefixes to those registered with ``register_namespace(prefix, uri)``.
        Contrary to ``register_namespace()``, these prefixes are not
        saved for future calls.

        Any additional named arguments can be used to pass values for XPath
        variables in the XPath expression, e.g.::

            selector.xpath('//a[href=$url]', url="http://www.example.com")
        """
        try:
            xpathev = self.root.xpath
        except AttributeError:
            return self.selectorlist_cls([])

        nsp = dict(self.namespaces)
        if namespaces is not None:
            nsp.update(namespaces)
        try:
            result = xpathev(
                query, namespaces=nsp, smart_strings=self._lxml_smart_strings, **kwargs
            )
        except etree.XPathError as exc:
            raise ValueError(f"XPath error: {exc} in {query}")

        if type(result) is not list:
            result = [result]

        result = [
            self.__class__(
                root=x, _expr=query, namespaces=self.namespaces, type=self.type
            )
            for x in result
        ]
        return self.selectorlist_cls(result)

    def css(self: _SelectorType, query: str) -> SelectorList[_SelectorType]:
        """
        Apply the given CSS selector and return a :class:`SelectorList` instance.

        ``query`` is a string containing the CSS selector to apply.

        In the background, CSS queries are translated into XPath queries using
        `cssselect`_ library and run ``.xpath()`` method.

        .. _cssselect: https://pypi.python.org/pypi/cssselect/
        """
        return self.xpath(self._css2xpath(query))

    def _css2xpath(self, query: str) -> Any:
        return self._csstranslator.css_to_xpath(query)

    def re(
        self, regex: Union[str, Pattern[str]], replace_entities: bool = True
    ) -> List[str]:
        """
        Apply the given regex and return a list of strings with the
        matches.

        ``regex`` can be either a compiled regular expression or a string which
        will be compiled to a regular expression using ``re.compile(regex)``.

        By default, character entity references are replaced by their
        corresponding character (except for ``&amp;`` and ``&lt;``).
        Passing ``replace_entities`` as ``False`` switches off these
        replacements.
        """
        return extract_regex(regex, self.get(), replace_entities=replace_entities)

    @typing.overload
    def re_first(
        self,
        regex: Union[str, Pattern[str]],
        default: None = None,
        replace_entities: bool = True,
    ) -> Optional[str]:
        pass

    @typing.overload
    def re_first(
        self,
        regex: Union[str, Pattern[str]],
        default: str,
        replace_entities: bool = True,
    ) -> str:
        pass

    def re_first(
        self,
        regex: Union[str, Pattern[str]],
        default: Optional[str] = None,
        replace_entities: bool = True,
    ) -> Optional[str]:
        """
        Apply the given regex and return the first string which matches. If
        there is no match, return the default value (``None`` if the argument
        is not provided).

        By default, character entity references are replaced by their
        corresponding character (except for ``&amp;`` and ``&lt;``).
        Passing ``replace_entities`` as ``False`` switches off these
        replacements.
        """
        return next(
            iflatten(self.re(regex, replace_entities=replace_entities)), default
        )

    def get(
        self,
        text: bool = False,
        cleaner: Union[str, None, Cleaner] = "auto",
        guess_punct_space: bool = True,
        guess_layout: bool = True,
    ) -> str:
        """
        Serialize and return the matched nodes in a single string.
        Percent encoded content is unquoted.

        When ``text`` is False (default), HTML or XML is extracted. Pass
        ``text=True`` to extract text content (html-text library is used).
        Text extraction algorithm assumes that the document is an HTML
        document, and uses HTML-specific rules.

        ``cleaner`` argument allows cleaning HTML before extracting the
        content. Allowed values:

        * "auto" (default) - don't clean when text=False, clean with
          options tuned for text extraction when text=True;
        * "text" - clean with options tuned for text extraction: elements
          like ``<script>`` and ``<style>`` are removed, cleaning options
          are tuned for speed, assuming text extraction is the end goal;
        * "html" - use default ``lxml.html.clean.Cleaner``. This is useful
          if you want to make .get() output more human-readable, but still
          preserve HTML tags.
        * None - don't clean, even when ``text=True``. Useful if you have
          an already cleaned tree, e.g. after calling :meth:`Selector.cleaned`.
        * custom ``lxml.html.clean.Cleaner`` objects are also supported.

        ``guess_punct_space`` and ``guess_layout`` options allow to customize
        text extraction algorithm. By default, when ``text=True``,
        parsel tries to insert newlines and blank lines as appropriate,
        and be smart about whitespaces around inline tags,
        so that the text output looks similar to browser's.

        Pass ``guess_punct_space=False`` to disable punctuation handling.
        This option has no effect when ``text=False``.

        Use ``guess_layout=False`` to avoid adding newlines - content will
        be just a single line of text, using whitespaces as separators.
        This option has no effect when ``text=False``.
        """
        sel = self
        if cleaner == "auto":
            if text:
                sel = self.cleaned("text")
        elif cleaner is not None:
            sel = self.cleaned(cleaner)
        tree = sel.root

        if text:
            return html_text.etree_to_text(
                tree, guess_punct_space=guess_punct_space, guess_layout=guess_layout
            )

        try:
            return etree.tostring(
                tree, method=self._tostring_method, encoding="unicode", with_tail=False
            )
        except (AttributeError, TypeError):
            if tree is True:
                return "1"
            elif tree is False:
                return "0"
            else:
                return str(tree)

    extract = get

    def getall(
        self,
        text: bool = False,
        cleaner: Union[str, None, Cleaner] = "auto",
        guess_punct_space: bool = True,
        guess_layout: bool = True,
    ) -> List[str]:
        """
        Serialize and return the matched node in a 1-element list of strings.

        See :meth:`~.Selector.get` for options.
        """
        return [
            self.get(
                text=text,
                cleaner=cleaner,
                guess_punct_space=guess_punct_space,
                guess_layout=guess_layout,
            )
        ]

    def register_namespace(self, prefix: str, uri: str) -> None:
        """
        Register the given namespace to be used in this :class:`Selector`.
        Without registering namespaces you can't select or extract data from
        non-standard namespaces. See :ref:`selector-examples-xml`.
        """
        self.namespaces[prefix] = uri

    def remove_namespaces(self) -> None:
        """
        Remove all namespaces, allowing to traverse the document using
        namespace-less xpaths. See :ref:`removing-namespaces`.
        """
        for el in self.root.iter("*"):
            if el.tag.startswith("{"):
                el.tag = el.tag.split("}", 1)[1]
            # loop on element attributes also
            for an in el.attrib:
                if an.startswith("{"):
                    el.attrib[an.split("}", 1)[1]] = el.attrib.pop(an)
        # remove namespace declarations
        etree.cleanup_namespaces(self.root)

    def remove(self) -> None:
        """
        Remove matched nodes from the parent element.
        """
        try:
            parent = self.root.getparent()
        except AttributeError:
            # 'str' object has no attribute 'getparent'
            raise CannotRemoveElementWithoutRoot(
                "The node you're trying to remove has no root, "
                "are you trying to remove a pseudo-element? "
                "Try to use 'li' as a selector instead of 'li::text' or "
                "'//li' instead of '//li/text()', for example."
            )

        try:
            parent.remove(self.root)
        except AttributeError:
            # 'NoneType' object has no attribute 'remove'
            raise CannotRemoveElementWithoutParent(
                "The node you're trying to remove has no parent, "
                "are you trying to remove a root element?"
            )

    @property
    def attrib(self) -> Dict[str, str]:
        """Return the attributes dictionary for underlying element."""
        return dict(self.root.attrib)

    def cleaned(
        self: _SelectorType, cleaner: Union[str, Cleaner] = "auto"
    ) -> _SelectorType:
        """
        Return a copy of a Selector, with underlying subtree cleaned.
        Allowed values of ``cleaner`` argument:

        * "html" (default) - use default ``lxml.html.clean.Cleaner``;
        * "text" - clean with options tuned for text extraction: elements
          like ``<script>`` and ``<style>`` are removed, cleaning options
          are tuned for speed, assuming text extraction is the end goal;
        * custom ``lxml.html.clean.Cleaner`` objects are also supported.
        """
        if isinstance(cleaner, str):
            if cleaner not in {"html", "text"}:
                raise ValueError(
                    "cleaner must be 'html', 'text' or "
                    "an lxml.html.clean.Cleaner instance"
                )
        if cleaner == "html":
            cleaner = self._html_cleaner
        elif cleaner == "text":
            cleaner = self._text_cleaner
        root = cleaner.clean_html(self.root)
        return self.__class__(
            root=root, _expr=self._expr, namespaces=self.namespaces, type=self.type
        )

    def __bool__(self) -> bool:
        """
        Return ``True`` if there is any real content selected or ``False``
        otherwise.  In other words, the boolean value of a :class:`Selector` is
        given by the contents it selects.
        """
        return bool(self.get())

    __nonzero__ = __bool__

    def __str__(self) -> str:
        data = repr(shorten(self.get(), width=40))
        return f"<{type(self).__name__} xpath={self._expr!r} data={data}>"

    __repr__ = __str__
