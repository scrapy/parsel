"""
XPath selectors based on lxml
"""

import six
import jmespath as jpath
import json
import warnings
from lxml import etree
from jmespath.exceptions import JMESPathError

from .utils import flatten, iflatten, extract_regex
from .csstranslator import HTMLTranslator, GenericTranslator


class SafeXMLParser(etree.XMLParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('resolve_entities', False)
        super(SafeXMLParser, self).__init__(*args, **kwargs)

_ctgroup = {
    'html': {'_parser': etree.HTMLParser,
             '_csstranslator': HTMLTranslator(),
             '_tostring_method': 'html'},
    'xml': {'_parser': SafeXMLParser,
            '_csstranslator': GenericTranslator(),
            '_tostring_method': 'xml'},
    'json': {'_parser': None,
            '_csstranslator': None,
            '_tostring_method': None}
}


def _st(st):
    if st is None:
        return 'html'
    elif st in _ctgroup:
        return st
    else:
        raise ValueError('Invalid type: %s' % st)


def _translate_path(to_json):
    """
    this is a decorator that modifies the selector
    instance as needed by the methods jmespath and xpath
    when ``to_json`` is true converts selector
    instance to jmespath compatible type if required
    """
    def deco(func):
        def wrapped(selector_cls, *args, **kwargs):
            type = 'json' if to_json else None
            is_json = selector_cls._is_type_json()
            if (to_json and not is_json) or (not to_json and is_json):
                selector_cls = selector_cls.__class__(
                        text=selector_cls.extract(),
                        type=type)
            return func(selector_cls, *args, **kwargs)
        return wrapped
    return deco


def _json_incompatible(func):
    """
    this a decorator that gives a warning when a certain
    method is called which not compatible with the Selector
    of type `json`
    """
    def deco(selector_cls, *args, **kwargs):
        if selector_cls._is_type_json():
            warnings.warn('Cannot call this method when '
                          'Selector is instantiated with type: `json`')
            return None
        return func(selector_cls, *args, **kwargs)
    return deco


def create_root_node(text, parser_cls, base_url=None):
    """Create root node for text using given parser class.
    """
    body = text.strip().encode('utf8') or b'<html/>'
    parser = parser_cls(recover=True, encoding='utf8')
    return etree.fromstring(body, parser=parser, base_url=base_url)


class SelectorList(list):
    """
    The :class:`SelectorList` class is a subclass of the builtin ``list``
    class, which provides a few additional methods.
    """

    # __getslice__ is deprecated but `list` builtin implements it only in Py2
    def __getslice__(self, i, j):
        o = super(SelectorList, self).__getslice__(i, j)
        return self.__class__(o)

    def __getitem__(self, pos):
        o = super(SelectorList, self).__getitem__(pos)
        return self.__class__(o) if isinstance(pos, slice) else o

    def xpath(self, xpath):
        """
        Call the ``.xpath()`` method for each element in this list and return
        their results flattened as another :class:`SelectorList`.
        ``query`` is the same argument as the one in :meth:`Selector.xpath`
        """
        return self.__class__(flatten([x.xpath(xpath) for x in self]))

    def css(self, xpath):
        """
        Call the ``.css()`` method for each element in this list and return
        their results flattened as another :class:`SelectorList`.
        ``query`` is the same argument as the one in :meth:`Selector.css`
        """
        return self.__class__(flatten([x.css(xpath) for x in self]))

    def re(self, regex):
        """
        Call the ``.re()`` method for each element is this list and return
        their results flattened, as a list of unicode strings.
        """
        return flatten([x.re(regex) for x in self])

    def re_first(self, regex):
        for el in iflatten(x.re(regex) for x in self):
            return el

    def extract(self):
        """
        Call the ``.extract()`` method for each element is this list and return
        their results flattened, as a list of unicode strings.
        """
        return [x.extract() for x in self]

    def extract_first(self, default=None):
        for x in self:
            return x.extract()
        else:
            return default

    def jmespath(self, jmespath):
        """
        Call the ``.jmespath()`` method for each element in this list and return
        their results flattened as another :class:`SelectorList`.
        ``query`` is the same argument as the one in :meth:`Selector.xpath`
        """
        return self.__class__(flatten([x.jmespath(jmespath) for x in self]))


class Selector(object):
    """
    :class:`Selector` allows you to select parts of an XML or HTML text using CSS
    or XPath expressions and extract data from it.
    ``text`` is a ``unicode`` object in Python 2 or a ``str`` object in Python 3
    ``type`` defines the selector type, it can be ``"html"``, ``"xml"``, ``"json"`` or ``None`` (default).
    If ``type`` is ``None``, the selector defaults to ``"html"``.
    if ``type`` is ``json`` than Selector tries to decode text to a json object.
    If json decoding fails than Selector silently defaults back to ``"html"``
    """

    __slots__ = ['text', 'namespaces', 'type', '_expr', 'root',
                 '__weakref__', '_parser', '_csstranslator', '_tostring_method']

    _default_type = None
    _default_namespaces = {
        "re": "http://exslt.org/regular-expressions",

        # supported in libxslt:
        # set:difference
        # set:has-same-node
        # set:intersection
        # set:leading
        # set:trailing
        "set": "http://exslt.org/sets"
    }
    _lxml_smart_strings = False
    selectorlist_cls = SelectorList

    def __init__(self, text=None, type=None, namespaces=None, root=None,
                 base_url=None, _expr=None):

        self.type = st = _st(type or self._default_type)
        self._parser = _ctgroup[st]['_parser']
        self._csstranslator = _ctgroup[st]['_csstranslator']
        self._tostring_method = _ctgroup[st]['_tostring_method']

        reinit = False
        if text is not None:
            if not isinstance(text, six.text_type):
                raise TypeError("text argument should be of type %s" % six.text_type)
            if type == 'json':
                try:
                    root = json.loads(text)
                except ValueError:
                    reinit = True
            else:
                root = self._get_root(text, base_url)
        elif root is None:
            raise ValueError("Selector needs either text or root argument")

        self.namespaces = dict(self._default_namespaces)
        if namespaces is not None:
            self.namespaces.update(namespaces)

        self.root = root
        self._expr = _expr

        if reinit:
            self.__init__(text=text)

    def _get_root(self, text, base_url=None):
        return create_root_node(text, self._parser, base_url=base_url)

    @_translate_path(to_json=False)
    def xpath(self, query):
        """
        Find nodes matching the xpath ``query`` and return the result as a
        :class:`SelectorList` instance with all elements flattened. List
        elements implement :class:`Selector` interface too.
        ``query`` is a string containing the XPATH query to apply.
        """
        try:
            xpathev = self.root.xpath
        except AttributeError:
            return self.selectorlist_cls([])

        try:
            result = xpathev(query, namespaces=self.namespaces,
                             smart_strings=self._lxml_smart_strings)
        except etree.XPathError:
            msg = u"Invalid XPath: %s" % query
            raise ValueError(msg if six.PY3 else msg.encode("unicode_escape"))

        if type(result) is not list:
            result = [result]

        result = [self.__class__(root=x, _expr=query,
                                 namespaces=self.namespaces,
                                 type=self.type)
                  for x in result]
        return self.selectorlist_cls(result)

    @_translate_path(to_json=False)
    def css(self, query):
        """
        Apply the given CSS selector and return a :class:`SelectorList` instance.
        ``query`` is a string containing the CSS selector to apply.
        In the background, CSS queries are translated into XPath queries using
        `cssselect`_ library and run ``.xpath()`` method.
        """
        return self.xpath(self._css2xpath(query))

    def _css2xpath(self, query):
        return self._csstranslator.css_to_xpath(query)

    def re(self, regex):
        """
        Apply the given regex and return a list of unicode strings with the
        matches.
        ``regex`` can be either a compiled regular expression or a string which
        will be compiled to a regular expression using ``re.compile(regex)``
        """
        return extract_regex(regex, self.extract())

    def extract(self):
        """
        Serialize and return the matched nodes as a list of unicode strings.
        Percent encoded content is unquoted.
        """
        if self._is_type_json():
            if isinstance(self.root, six.string_types):
                return six.text_type(self.root)
            else:
                return six.text_type(json.dumps(self.root))

        try:
            return etree.tostring(self.root,
                                  method=self._tostring_method,
                                  encoding='unicode',
                                  with_tail=False)
        except (AttributeError, TypeError):
            if self.root is True:
                return u'1'
            elif self.root is False:
                return u'0'
            else:
                return six.text_type(self.root)

    @_json_incompatible
    def register_namespace(self, prefix, uri):
        """
        Register the given namespace to be used in this :class:`Selector`.
        Without registering namespaces you can't select or extract data from
        non-standard namespaces. See :ref:`selector-examples-xml`.
        """
        self.namespaces[prefix] = uri

    @_json_incompatible
    def remove_namespaces(self):
        """
        Remove all namespaces, allowing to traverse the document using
        namespace-less xpaths. See :ref:`removing-namespaces`.
        """
        for el in self.root.iter('*'):
            if el.tag.startswith('{'):
                el.tag = el.tag.split('}', 1)[1]
            # loop on element attributes also
            for an in el.attrib.keys():
                if an.startswith('{'):
                    el.attrib[an.split('}', 1)[1]] = el.attrib.pop(an)

    @_translate_path(to_json=True)
    def jmespath(self, query):
        """
        Find nodes matching the jmespath ``query`` and return the result as a
        :class:`SelectorList` instance with all elements flattened. List
        elements implement :class:`Selector` interface too.
        ``query`` is a string containing the jmespath query to apply.
        """
        try:
            result = jpath.search(query, self.root)
        except JMESPathError:
            msg = u"Invalid JMESPath: %s" % query
            raise ValueError(msg if six.PY3 else msg.encode("unicode_escape"))

        if type(result) is not list:
            result = [result]

        result = [self.__class__(type=self.type,
                                 root=x,
                                 _expr=query)
                  for x in flatten(result, lambda y: isinstance(y, list)) if x is not None]
        return self.selectorlist_cls(result)

    def _is_type_json(self):
        return self.type == 'json'

    def __bool__(self):
        """
        Return ``True`` if there is any real content selected or ``False``
        otherwise.  In other words, the boolean value of a :class:`Selector` is
        given by the contents it selects.
        """
        return bool(self.extract())
    __nonzero__ = __bool__

    def __str__(self):
        data = repr(self.extract()[:40])
        return "<%s type=%r path=%r data=%s>" % (type(self).__name__, self.type, self._expr, data)

    __repr__ = __str__
