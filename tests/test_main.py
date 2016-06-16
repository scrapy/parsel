import contextlib
import io
import sys
import tempfile
import unittest

import six

from parsel.__main__ import main


HTML = u"""
    <div><a href="foo">bar</a></div>
""".encode('utf-8')


@contextlib.contextmanager
def capture(stdin=None, encoding='utf-8'):
    orig_stdin, orig_stdout = sys.stdin, sys.stdout
    if six.PY2:
        sys.stdin = stdin or six.StringIO()
        sys.stdout = six.StringIO()
    else:
        sys.stdin = io.TextIOWrapper(stdin or io.BytesIO(), encoding=encoding)
        sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding=encoding)
    try:
        yield sys.stdout
    finally:
        sys.stdin = orig_stdin
        sys.stdout = orig_stdout


class MainTestCase(unittest.TestCase):

    def test_default_arguments(self):
        argv = ['a::attr(href)']
        with capture(stdin=io.BytesIO(HTML)) as stdout:
            main(argv)

        stdout.seek(0)
        self.assertEqual(stdout.read(), u'foo\n')

    def test_default_arguments_from_file(self):
        argv = ['a::attr(href)']
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            fp.write(HTML)
            fp.flush()
            argv.append(fp.name)
            with capture() as stdout:
                main(argv)

            stdout.seek(0)
            self.assertEqual(stdout.read(), u'foo\n')

    def test_with_all_arguments(self):
        argv = [
            '--re',
            '(foo|bar)',
            '--xpath',
            '//a[@href]',
            '--encoding',
            'latin1',
            '--repr',
        ]
        with capture(stdin=io.BytesIO(HTML)) as stdout:
            main(argv)

        stdout.seek(0)
        self.assertEqual(eval(stdout.read()), ['foo', 'bar'])
