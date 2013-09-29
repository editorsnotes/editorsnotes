from collections import OrderedDict

from rest_framework.views import APIView
from rest_framework.response import Response

from editorsnotes.search import en_index

class SearchView(APIView):
    def get(self, request, format=None):
        query = {'query': {}}
        params = request.QUERY_PARAMS

        if 'q' in params:
            query['query']['query_string'] = {'query': params.get('q')}

        if 'sort' in params:
            pass

        if 'order' in params:
            pass

        if 'page' in params:
            pass

        if not query['query']:
            query = {'query': {'match_all': {}}}

        es_query = en_index.es.search(query)

        hits = []

        for hit in es_query['hits']['hits']:
            item_type = hit['_type']
            item_data = hit['_source']['serialized']
            filter_method = getattr(self, 'filter_{}_hits'.format(item_type),
                                    None)
            if filter_method is not None:
                item_data = filter_method(item_data)
            hits.append({'data': item_data, 'type': item_type})

        return Response(OrderedDict((
            ('results', es_query['hits']['total']),
            ('data', hits),
        )))
