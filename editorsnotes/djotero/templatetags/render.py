from django import template
from djotero.utils import as_readable
import json

register = template.Library()

@register.filter
def readable(obj):
    content = json.loads(as_readable(obj))
    html = []
    for key, value in sorted(content.items()):
        html.append('<b>%s</b>: %s' % (key, value))
    return '<br>\n'.join(html)
