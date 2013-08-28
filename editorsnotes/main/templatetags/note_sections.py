from django import template

from ..models.notes import NoteSection

register = template.Library()

@register.filter
def ns_template_name(ns):
    if hasattr(ns, 'template_name'):
        return ns.template_name
    return 'includes/note_sections/{}.html'.format(ns.section_type)

