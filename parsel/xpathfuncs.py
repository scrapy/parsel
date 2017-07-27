from lxml import etree


def set_xpathfunc(fname, func):
    """Register a custom extension function to use in XPath expressions.

    The function ``func`` registered under ``fname`` identifier will be called
    for every matching node, being passed a ``context`` parameter as well as
    any parameters passed from the corresponding XPath expression.

    If ``func`` is ``None``, the extension function will be removed.

    See more `in lxml documentation`_.

    .. _`in lxml documentation`: http://lxml.de/extensions.html#xpath-extension-functions

    """
    ns_fns = etree.FunctionNamespace(None)
    if func is not None:
        ns_fns[fname] = func
    else:
        del ns_fns[fname]


def setup():
    set_xpathfunc('has-class', has_class)


def has_class(context, *classes):
    """has-class function.

    Return True if all ``classes`` are present in element's class attr.

    """
    node_cls = context.context_node.get('class')
    if node_cls is None:
        return False
    node_cls = ' ' + node_cls + ' '
    for cls in classes:
        if ' ' + cls + ' ' not in node_cls:
            return False
    return True
