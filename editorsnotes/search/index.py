from collections import OrderedDict
from itertools import chain
import json

from django.conf import settings

from pyelasticsearch import ElasticSearch
from pyelasticsearch.exceptions import InvalidJsonResponseError

from .types import DocumentTypeAdapter

class OrderedResponseElasticSearch(ElasticSearch):
    def _decode_response(self, response):
        try:
            json_response = json.loads(response.content,
                                       object_pairs_hook=OrderedDict)
        except ValueError:
            raise InvalidJsonResponseError(response)
        return json_response

class ENIndex(object):
    def __init__(self, name=settings.ELASTICSEARCH_INDEX_NAME):
        self.document_types = {}
        self.name = name
        self.es = OrderedResponseElasticSearch(settings.ELASTICSEARCH_URLS)
        if not self.exists():
            self.create()

    def exists(self):
        server_url, _ = self.es.servers.get()
        resp = self.es.session.head(server_url + '/' + self.name)
        return resp.status_code == 200

    def register(self, model, adapter=None, highlight_fields=None,
                 display_field=None):
        if adapter is None:
            doc_type = DocumentTypeAdapter(self.es, self.name, model,
                                           highlight_fields, display_field)
        else:
            doc_type = adapter(self.es, self.name, model)
        self.document_types[model] = doc_type

    def data_for_object(self, obj):
        doc_type = self.document_types.get(obj.__class__, None)
        if doc_type is None:
            return None

        # will raise an exception if it's not there! should change
        return self.es.get(index=self.name, doc_type=doc_type.type_label,
                           id=obj.id)

    def search_model(self, model, query, **kwargs):
        doc_type = self.document_types.get(model)
        return self.es.search(query, index=self.name,
                              doc_type=doc_type.type_label, **kwargs)

    def search(self, query, highlight=False, **kwargs):

        if isinstance(query, basestring):
            prepared_query = {
                'query': {
                    'query_string': { 'query': query }
                }
            }

        else:
            prepared_query = query

        if highlight:
            prepared_query['highlight'] = {
                'fields': {},
                'pre_tags': ['<span class="highlighted">'],
                'post_tags': ['</span>']
            }
            highlight_fields = chain(
                *[doc_type.highlight_fields
                for doc_type in self.document_types.values()])
            for field_name in highlight_fields:
                prepared_query['highlight']['fields'][field_name] = {}

        return self.es.search(prepared_query, index=self.name, **kwargs)

    def create(self):
        created = self.es.create_index(self.name)
        return created

    def delete(self):
        return self.es.delete_index(self.name)
