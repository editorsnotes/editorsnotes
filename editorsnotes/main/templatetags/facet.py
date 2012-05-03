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
        html = ''
        html += '<h6>%s</h6>' % (self.facet_title)
        facet_inputs = []
        for val, label, count in self.facet_item_list.resolve(context):
            facet_inputs.append('<li><input type="checkbox" name="%s" value="%s">&nbsp;%s (%s)</li>' % (
                self.facet_name, val, label, count))
        if len(facet_inputs) > 5:
            col_length = len(facet_inputs) / 2

            html += '<ul class="unstyled span6">'
            html += '\n'.join(facet_inputs[:col_length])
            html += '</ul>'

            html += '<ul class="unstyled span6">'
            html += '\n'.join(facet_inputs[col_length:])
            html += '</ul>'

        else:
            html += '<ul class="unstyled">'
            html += '\n'.join(facet_inputs)
            html += '</ul>'
        return html

#        try:
#        except template.VariableDoesNotExist:
#            return
