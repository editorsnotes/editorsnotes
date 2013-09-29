from collections import OrderedDict

from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView, GenericAPIView)
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from editorsnotes.main.models.auth import Project
from editorsnotes.search import en_index

from ..filters import ElasticSearchFilterBackend
from ..permissions import ProjectSpecificPermissions

class CreateReversionMixin(object):
    def get_serializer_context(self):
        context = super(CreateReversionMixin, self).get_serializer_context()
        context['create_revision'] = True
        return context

class ElasticSearchRetrieveMixin(RetrieveModelMixin):
    def retrieve(self, request, *args, **kwargs):

        if not settings.ELASTICSEARCH_ENABLED:
            return super(ElasticSearchRetrieveMixin, self).retrieve(request, *args, **kwargs)

        # Still need to get the object to check for perms
        self.object = self.get_object()
        data = en_index.data_for_object(self.object)
        return Response(data['_source']['serialized'])

class ElasticSearchListMixin(ListModelMixin):
    def list(self, request, *args, **kwargs):

        if not settings.ELASTICSEARCH_ENABLED:
            return super(ElasticSearchListMixin, self).list(request, *args, **kwargs)

        self.filter_backend = ElasticSearchFilterBackend
        result = self.filter_queryset(None)

        data = {
            'count': result['hits']['total'],
            'next': None,
            'previous': None,
            'results': [ doc['_source']['serialized'] for doc in
                         result['hits']['hits'] ]
        }

        return Response(data)


class ProjectSpecificAPIView(APIView):
    """
    Base API view for project-specific views.

    Sets request.project to the project being accessed, and includes the
    ProjectSpecificPermissions class by default.
    """
    permission_classes = (ProjectSpecificPermissions,)
    parser_classes = (JSONParser,)
    renderer_classes = (JSONRenderer,)
    def initialize_request(self, request, *args, **kwargs):
        request = super(ProjectSpecificAPIView, self)\
                .initialize_request(request, *args, **kwargs)
        request._request.project = Project.objects.get(
            slug=kwargs.pop('project_slug'))
        return request

class BaseListAPIView(ListCreateAPIView, ProjectSpecificAPIView):
    paginate_by = 50
    paginate_by_param = 'page_size'
    def pre_save(self, obj):
        obj.creator = obj.last_updater = self.request.user

class BaseDetailView(RetrieveUpdateDestroyAPIView, ProjectSpecificAPIView):
    def pre_save(self, obj):
        obj.last_updater = self.request.user

@api_view(('GET',))
def root(request):
    return Response({
        'auth-token': reverse('obtain-auth-token'),
        'notes': reverse('api-notes-list'),
        'topics': reverse('api-topics-list'),
        'documents': reverse('api-documents-list')
    })
