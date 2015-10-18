from collections import OrderedDict

from rest_framework import renderers

from .ld import CONTEXT


class BrowsableJSONAPIRenderer(renderers.BrowsableAPIRenderer):
    def get_default_renderer(self, view):
        return JSONLDRenderer()


class JSONLDRenderer(renderers.JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        data_with_context = OrderedDict()

        # If there are any values for `@context`, add them to the default
        # context dict.
        context = CONTEXT.copy()
        context.update(data.pop('@context', {}))

        data_with_context['@context'] = context
        data_with_context.update(data)

        return super(JSONLDRenderer, self)\
            .render(data_with_context, accepted_media_type, renderer_context)
