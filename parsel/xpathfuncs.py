from lxml import etree
from six import iteritems, get_function_code

_XPATH_FUNCS = {}


def register(func):
    fname = get_function_code(func).co_name.replace('_', '-')
    _XPATH_FUNCS[fname] = func
    return func


def setup():
    fns = etree.FunctionNamespace(None)
    for k, v in iteritems(_XPATH_FUNCS):
        fns[k] = v


@register
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
