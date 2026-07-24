"""Sphinx extension providing the ``xpathdemo`` directive.

The directive renders an interactive, in-browser playground where readers can
edit an HTML snippet and an XPath expression and see the matching nodes update
live. Evaluation happens entirely client-side using the browser's native
``document.evaluate()`` XPath 1.0 engine (see ``_static/xpathdemo.js``), so no
third-party JavaScript library is required.

Usage::

    .. xpathdemo:: //p

        <html><body><p>Hello</p></body></html>

The first argument is the initial XPath expression and the directive body is the
initial HTML input.

The widget is emitted as raw HTML, so it only appears on the HTML builder;
other builders (Markdown, LaTeX, …) ignore it. The example itself is still
available to those outputs through the reStructuredText source.
"""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

from docutils import nodes
from docutils.parsers.rst import Directive

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


class XPathDemoDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self) -> list[nodes.Node]:
        env = self.state.document.settings.env
        serial = env.new_serialno("xpathdemo")
        input_id = f"xpath-demo-input-{serial}"
        expression_id = f"xpath-demo-expression-{serial}"
        output_id = f"xpath-demo-output-{serial}"

        expression = escape(self.arguments[0], quote=True)
        html_input = escape("\n".join(self.content))

        widget = (
            f'<div class="xpath-demo">'
            f'<label class="xpath-demo-label" for="{input_id}">HTML input</label>'
            f'<textarea id="{input_id}" class="xpath-demo-input" rows="10" '
            f'spellcheck="false" autocapitalize="off" autocomplete="off" '
            f'autocorrect="off">{html_input}</textarea>'
            f'<label class="xpath-demo-label" for="{expression_id}">'
            f"XPath expression</label>"
            f'<input id="{expression_id}" class="xpath-demo-expression" '
            f'type="text" spellcheck="false" autocapitalize="off" '
            f'autocomplete="off" autocorrect="off" value="{expression}">'
            f'<div class="xpath-demo-label">Result</div>'
            f'<div id="{output_id}" class="xpath-demo-output" role="status" '
            f'aria-live="polite"></div>'
            f"</div>"
        )

        return [nodes.raw("", widget, format="html")]


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_directive("xpathdemo", XPathDemoDirective)
    app.add_css_file("xpathdemo.css")
    app.add_js_file("xpathdemo.js")

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
