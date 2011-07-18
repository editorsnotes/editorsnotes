from django import template
import re
import json
import djotero.utils

register = template.Library()

# as_csl & get_names moved to utils.py

@register.filter
def as_citeproc_ref(obj, num):
    csl = json.loads(as_csl(obj))
    csl['id'] = 'ITEM-%s' % (num)
    return json.dumps(csl)
