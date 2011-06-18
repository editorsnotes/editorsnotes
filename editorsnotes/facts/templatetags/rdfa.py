from django import template
from django.utils.safestring import mark_safe
from editorsnotes.facts import utils
from urlparse import urlparse
import RDF

register = template.Library()
model = RDF.Model(utils.open_triplestore())

@register.filter
def as_netloc(uri):
    return mark_safe(u'<a href="%s">%s</a>' % (uri, urlparse(uri).netloc))

@register.filter
def as_rdfa(uri_or_node):
    if type(uri_or_node) is str:
        uri = uri_or_node
    elif type(uri_or_node) is RDF.Node:
        if uri_or_node.is_literal():
            return mark_safe(uri_or_node.literal[0])
        elif uri_or_node.is_blank():
            return 'ERROR: blank node'
        else:
            uri = str(uri_or_node.uri)
    else:
        return 'ERROR: unknown type: %s' % type(uri_or_node)
    label = utils.get_cached_label(model, uri, 'en') or uri
    return mark_safe(u'<a href="%s">%s</a>' % (uri, label))
