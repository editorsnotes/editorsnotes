import re
from haystack.query import SearchQuerySet
from rest_framework.filters import BaseFilterBackend

class HaystackFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        query = []

        view_model = getattr(view, 'model')
        filter_fields = ('q', 'project_id',)

        for field in filter_fields:
            query += self.make_field_query(field, request.QUERY_PARAMS)

        if not query:
            return queryset or view_model.objects.all()

        qs = SearchQuerySet()\
                .models(view_model)\
                .narrow(' AND '.join(query))\
                .load_all()
        return view_model.objects.filter(pk__in=[r.pk for r in qs])

    def make_field_query(self, field, params):
        if not params.get(field, None):
            return []

        elif field == 'q':
            return ['text:{}'.format(q) for q in re.split(r'[+\s]', params.get('q'))]

        elif field == 'project_id':
            return ['project_id:{}'.format(p) for p in params.get(field).split(',')]

        else:
            return []

