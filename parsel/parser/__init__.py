from lxml import etree
from lxml.etree import XMLParser as _UnsafeXMLParser
from lxml.html import HTMLParser as _HTMLParser


class _LXMLBaseParser(object):

    def __init__(self, parser_cls):
        self._parser = parser_cls(recover=True, encoding='utf8')

    def parse(self, text, base_url):
        body = text.strip().replace('\x00', '').encode('utf8') or b'<html/>'
        root = etree.fromstring(body, parser=self._parser, base_url=base_url)
        if root is None:
            root = etree.fromstring(b'<html/>', parser=self._parser,
                                    base_url=base_url)
        return root


class HTMLParser(_LXMLBaseParser):

    def __init__(self):
        super(HTMLParser, self).__init__(_HTMLParser)


class _XMLParser(_UnsafeXMLParser):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('resolve_entities', False)
        super(_XMLParser, self).__init__(*args, **kwargs)


class XMLParser(_LXMLBaseParser):

    def __init__(self):
        super(XMLParser, self).__init__(_XMLParser)
