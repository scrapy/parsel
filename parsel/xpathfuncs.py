import re
from lxml import etree

from w3lib.html import HTML5_WHITESPACE

regex = '[{}]+'.format(HTML5_WHITESPACE)
replace_html5_whitespaces = re.compile(regex).sub


def set_xpathfunc(fname, func):
    """Register a custom extension function to use in XPath expressions.

    The function ``func`` registered under ``fname`` identifier will be called
    for every matching node, being passed a ``context`` parameter as well as
    any parameters passed from the corresponding XPath expression.

    If ``func`` is ``None``, the extension function will be removed.

    See more `in lxml documentation`_.

    .. _`in lxml documentation`: https://lxml.de/extensions.html#xpath-extension-functions

    """
    ns_fns = etree.FunctionNamespace(None)
    if func is not None:
        ns_fns[fname] = func
    else:
        del ns_fns[fname]


def setup():
    set_xpathfunc('has-class', has_class)
    set_xpathfunc('rel-id', rel_id)


def has_class(context, *classes):
    """has-class function.

    Return True if all ``classes`` are present in element's class attr.

    """
    if not context.eval_context.get('args_checked'):
        if not classes:
            raise ValueError(
                'XPath error: has-class must have at least 1 argument')
        for c in classes:
            if not isinstance(c, str):
                raise ValueError(
                    'XPath error: has-class arguments must be strings')
        context.eval_context['args_checked'] = True

    node_cls = context.context_node.get('class')
    if node_cls is None:
        return False
    node_cls = ' ' + node_cls + ' '
    node_cls = replace_html5_whitespaces(' ', node_cls)
    for cls in classes:
        if ' ' + cls + ' ' not in node_cls:
            return False
    return True


_id_xpath = etree.XPath('id($node_id)')


def rel_id(context, node_id, nodeset=None):
    """Relative lookup by ID (rel-id function).

    Same as ``id`` function, but relative to some nodeset (current node by
    default).

    For example, the following XPath expressions will return the same result
    (however, with different performance)::

        document.xpath("id('foo')")        # fastest
        document.xpath("rel-id('foo')")    # fast
        document.xpath("//*[@id='foo']")   # slow, has to iterate

    This function is useful in relative lookups, for example::

        document.xpath("rel-id('bar', id('foo'))")  # fast
        document.xpath("id('foo')//*[@id='bar']")   # slow, has to iterate

    The above can also be done with::

        document.xpath("id('foo')").xpath("rel-id('bar')")  # fast

    which showcases the fact that the current node is the default nodeset.

    """
    if not context.eval_context.get('args_checked'):
        if not isinstance(node_id, string_types):
            raise ValueError(
                'XPath error: rel-id: first argument must be a string')
        if nodeset is not None and not isinstance(nodeset, list):
            raise ValueError(
                'XPath error: rel-id: second argument must be a nodeset')
        context.eval_context['args_checked'] = True
    if nodeset is None:
        nodeset = {context.context_node}
    else:
        nodeset = set(nodeset)

    result = _id_xpath(context.context_node, node_id=node_id)
    should_return_result = (
        not result or
        nodeset.intersection(result) or
        nodeset.intersection(result[0].iterancestors()))
    if should_return_result:
        return result
    return []
