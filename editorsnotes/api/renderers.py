from collections import OrderedDict

from rest_framework import renderers

from rdflib import ConjunctiveGraph
from rdflib.namespace import Namespace

from .ld import CONTEXT, NAMESPACES


class BrowsableJSONLDRenderer(renderers.BrowsableAPIRenderer):
    format = 'jsonld-browse'

    def get_default_renderer(self, view):
        return JSONLDRenderer()


class BrowsableTurtleRenderer(renderers.BrowsableAPIRenderer):
    format = 'ttl-browse'

    def get_default_renderer(self, view):
        return TurtleRenderer()


class JSONLDRenderer(renderers.JSONRenderer):
    media_type = 'application/ld+json'
    format = 'jsonld'

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


class TurtleRenderer(JSONLDRenderer):
    media_type = 'text/turtle'
    format = 'ttl'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        jsonld = super(TurtleRenderer, self)\
            .render(data, accepted_media_type, renderer_context)

        g = ConjunctiveGraph()
        for ns, uri in list(NAMESPACES.items()):
            g.bind(ns, Namespace(uri))

        g.parse(data=jsonld, format='json-ld')

        return g.serialize(format='turtle')
