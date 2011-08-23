from django import template
from collections import defaultdict
from djotero.utils import resolve_names
import json

register = template.Library()

@register.filter
def date_as_text(parts):
    date = json.loads(parts)
    months = {'1' : 'January', '2' : 'February', '3' : 'March', '4' : 'April', '5' : 'May', '6' : 'June', '7' : 'July', '8' : 'August', '9' : 'September', '10' : 'October', '11' : 'November', '12' : 'December', '13' : 'Spring', '14' : 'Summer', '15' : 'Fall', '16' : 'Winter'}
    if 'month' in date.keys():
        date['month'] = months[date['month']]
    date_text = sorted(date.items())
    return date_text
