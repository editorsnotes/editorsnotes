from rest_framework.decorators import api_view
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from editorsnotes.main.models.auth import Project

from ..permissions import ProjectSpecificPermissions

class CreateReversionMixin(object):
    def get_serializer_context(self):
        context = super(CreateReversionMixin, self).get_serializer_context()
        context['create_revision'] = True
        return context

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
