from django import template

register = template.Library()

@register.tag(name='create_facet_field')
def do_create_facet_field(parser, token):
    try:
        tag_name, facet_title, facet_item_list = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            '%r requires two arguments' % token.contents.split()[0])
    if not (facet_title[0] == facet_title[-1] and facet_title[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            '%r tag\'s argument should be in quotes' % tag_name)
    return FacetNode(facet_title[1:-1], facet_item_list)

class FacetNode(template.Node):
    def __init__(self, facet_title, facet_item_list):
        self.facet_title = facet_title
        self.facet_name = facet_item_list[facet_item_list.rindex('.') + 1:]
        self.facet_item_list = template.Variable(facet_item_list)
    def render(self, context):
        templates = {
            'title': u'<h5>{}</h5>',
            'input': (
                u'<li>' +
                '<input id="facet-{name}-{counter}" type="checkbox" name="{name}" value="{value}">' +
                '<label for="facet-{name}-{counter}">{label} ({count})</label>' +
                '</li>'
            ),
            'list': u'<ul class="facet-list">{}</ul>'
        }

        html = u'<div class="select-facets-{}">'.format(self.facet_name)
        html += templates['title'].format(self.facet_title)

        try:
            facet = self.facet_item_list.resolve(context)
            facet_inputs = []
            counter = 0
            for value, label, count in facet:
                facet_inputs.append(templates['input'].format(
                    name=self.facet_name, value=value, label=label, count=count,
                    counter=counter))
                counter += 1

            if len(facet_inputs) > 5:
                # We want the first column to be the longer one if there are an odd
                # number of facets
                col_length = len(facet_inputs) / 2 + len(facet_inputs) % 2
                html += templates['list'].format('\n'.join(facet_inputs[:col_length]))
                html += templates['list'].format('\n'.join(facet_inputs[col_length:]))
            else:
                html += templates['list'].format('\n'.join(facet_inputs))
        except template.VariableDoesNotExist:
            html += u'<p>No values</p>'

        html += u'</div>'
        return html
