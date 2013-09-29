from django import template

from .. import en_index

register = template.Library()

TEMPLATE = u"""
<li data-model="{result_type}" class="searchresult">
    <strong>{result_type}:</strong>
    <a href="{result_url}">{result_display}</a>
    {result_body}
</li>
"""

def get_doc_type(label):
    dt, = [dt for _, dt in en_index.document_types.items()
           if dt.type_label == label]
    return dt

@register.filter
def render_search_result(result_dict):
    result_type = result_dict['_type']
    doc_type = get_doc_type(result_type)
    display_field = doc_type.display_field

    serialized = result_dict['_source']['serialized']
    highlights = result_dict.get('highlight', {})

    if display_field in highlights:
        result_display = highlights.pop(display_field)[0]
    else:
        result_display = reduce(
            lambda source_dict, attr: source_dict.get(attr),
            display_field.split('.'),
            result_dict['_source'])

    if len(highlights):
        result_body = ''.join(
            [u'<div class="fragment">...{}...</div>'.format(html)
             for highlighted_fields in highlights.values()
             for html in highlighted_fields])
    else:
        result_body = u''

    return TEMPLATE.format(result_type=result_type.title(),
                           result_url=serialized['url'],
                           result_display=result_display,
                           result_body=result_body)
