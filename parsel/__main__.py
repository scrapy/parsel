"""Parsel command line interface."""
from __future__ import print_function, unicode_literals

import argparse
import pprint
import re
import sys

import six

from . import Selector, __version__


def main(argv=None, progname=None):
    parser = argparse.ArgumentParser(prog=progname, description=__doc__)
    parser.add_argument('expr', metavar='EXPRESSION',
                        help="A CSSexpression, or a XPath expression if --xpath is given.")
    parser.add_argument('file', metavar='FILE', nargs='?',
                        help="If missing, it reads the HTML content from the standard input.")
    parser.add_argument('--xpath', action='store_true',
                        help="Given expression is a XPath expression.")
    parser.add_argument('--re', metavar='PATTERN',
                        help="Apply given regular expression.")
    parser.add_argument('--encoding', metavar='ENCODING', default='utf-8',
                        help="Input encoding. Default: utf-8.")
    parser.add_argument('--repr', action='store_true',
                        help="Output result object representation instead of as text.")
    parser.add_argument('-v', '--version', action='version', version=__version__)

    args = parser.parse_args(argv)

    if args.file:
        text = open(args.file).read()
    else:
        text = sys.stdin.read()

    if isinstance(text, six.binary_type):
        try:
            text = text.decode(args.encoding)
        except UnicodeDecodeError:
            parser.error("Failed to decode input using encoding: %s" % args.encoding)

    sel = Selector(text=text)

    if args.xpath:
        result = sel.xpath(args.expr)
    else:
        result = sel.css(args.expr)

    if args.re:
        regex = args.re.encode(args.encoding)
        regex = regex.decode('string_escape' if six.PY2 else 'unicode_escape')
        out = result.re(re.compile(regex, re.IGNORECASE | re.UNICODE))
    else:
        out = result.extract()

    if args.repr:
        pprint.pprint(out)
    else:
        print("\n".join(out))


if __name__ == "__main__":
    main(progname='python -m parsel')
