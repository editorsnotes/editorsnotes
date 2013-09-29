from rest_framework.filters import BaseFilterBackend

from editorsnotes.search import en_index

class ElasticSearchFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        query = {}
        params = request.QUERY_PARAMS

        if hasattr(request, 'project') or 'project' in params:
            project = params.get('project', request.project.slug)
            query['filter'] = {
                'term': {
                    'project': project
                }
            }

        if 'updater' in params:
            query['filter'] = {
                'term': {
                    'updaters': params.get('updater')
                }
            }

        if 'q' in params:
            q = params.get('q')
            query['query'] = {
                'match': {
                    'autocomplete.input': {
                        'query': q,
                        'operator': 'and',
                        'fuzziness': '0.3'
                    }
                }
            }
            query['highlight'] = {
                'fields': {'_all': {}},
                'pre_tags': ['&lt;strong&gt;'],
                'post_tags': ['&lt;/strong&gt;']
            }
        else:
            query['query'] = { 'match_all': {} }

        return en_index.search_model(view.model, query)
