"""
XPath selectors based on lxml
"""

import six
from lxml import etree

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
}


def _st(st):
    if st is None:
        return 'html'
    elif st in _ctgroup:
        return st
    else:
        raise ValueError('Invalid type: %s' % st)


def create_root_node(text, parser_cls, base_url=None):
    """Create root node for text using given parser class.
    """
    body = text.strip().encode('utf8') or b'<html/>'
    parser = parser_cls(recover=True, encoding='utf8')
    return etree.fromstring(body, parser=parser, base_url=base_url)


class SelectorList(list):

    def __getslice__(self, i, j):
        return self.__class__(list.__getslice__(self, i, j))

    def xpath(self, xpath):
        return self.__class__(flatten([x.xpath(xpath) for x in self]))

    def css(self, xpath):
        return self.__class__(flatten([x.css(xpath) for x in self]))

    def re(self, regex):
        return flatten([x.re(regex) for x in self])

    def re_first(self, regex):
        for el in iflatten(x.re(regex) for x in self):
            return el

    def extract(self):
        return [x.extract() for x in self]

    def extract_first(self, default=None):
        for x in self:
            return x.extract()
        else:
            return default


class Selector(object):

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

        if text is not None:
            if not isinstance(text, six.text_type):
                raise TypeError("text argument should be of type %s" % six.text_type)
            root = self._get_root(text, base_url)
        elif root is None:
            raise ValueError("Selector needs either text or root argument")

        self.namespaces = dict(self._default_namespaces)
        if namespaces is not None:
            self.namespaces.update(namespaces)
        self.root = root
        self._expr = _expr

    def _get_root(self, text, base_url=None):
        return create_root_node(text, self._parser, base_url=base_url)

    def xpath(self, query):
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

    def css(self, query):
        return self.xpath(self._css2xpath(query))

    def _css2xpath(self, query):
        return self._csstranslator.css_to_xpath(query)

    def re(self, regex):
        return extract_regex(regex, self.extract())

    def extract(self):
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

    def register_namespace(self, prefix, uri):
        if self.namespaces is None:
            self.namespaces = {}
        self.namespaces[prefix] = uri

    def remove_namespaces(self):
        for el in self.root.iter('*'):
            if el.tag.startswith('{'):
                el.tag = el.tag.split('}', 1)[1]
            # loop on element attributes also
            for an in el.attrib.keys():
                if an.startswith('{'):
                    el.attrib[an.split('}', 1)[1]] = el.attrib.pop(an)

    def __nonzero__(self):
        return bool(self.extract())

    def __str__(self):
        data = repr(self.extract()[:40])
        return "<%s xpath=%r data=%s>" % (type(self).__name__, self._expr, data)
    __repr__ = __str__
