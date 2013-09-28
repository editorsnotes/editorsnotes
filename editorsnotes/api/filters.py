import re
from haystack.query import SearchQuerySet
from rest_framework.filters import BaseFilterBackend

class HaystackFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        query = []

        if 'q' in request.QUERY_PARAMS:
            terms = [term for term in 
                     re.split(r'[+\s]', request.QUERY_PARAMS.get('q'))
                     if term]
            query += ['text:{}*'.format(q) for q in terms]

        if hasattr(request, 'project'):
            query += ['project_slug:{}'.format(request.project.slug)]

        view_model = getattr(view, 'model')

        if not query:
            return queryset or view_model.objects.all()

        model_ids = SearchQuerySet()\
                .models(view_model)\
                .narrow(' AND '.join(query))\
                .load_all()\
                .values_list('pk', flat=True)

        qs = view_model.objects.filter(pk__in=model_ids)

        if hasattr(view_model, 'topics'):
            qs = qs.prefetch_related('topics__container__project')

        return qs
