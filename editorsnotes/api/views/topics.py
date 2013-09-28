from django.shortcuts import get_object_or_404
from rest_framework.mixins import CreateModelMixin

from editorsnotes.main.models.topics import ProjectTopicContainer, TopicNode

from .base import BaseListAPIView, BaseDetailView
from ..serializers.topics import TopicSerializer

class TopicList(BaseListAPIView):
    model = ProjectTopicContainer
    serializer_class = TopicSerializer
    def pre_save(self, obj):
        super(TopicList, self).pre_save(obj)
        obj.project = self.request.project

class TopicDetail(BaseDetailView, CreateModelMixin):
    model = ProjectTopicContainer
    serializer_class = TopicSerializer
    def pre_save(self, obj):
        super(TopicDetail, self).pre_save(obj)
        if not obj.id:
            obj.project = self.request.project
    def get_object(self, queryset=None):
        filtered_queryset = self.filter_queryset(self.get_queryset())
        return get_object_or_404(filtered_queryset,
                                 project=self.request.project,
                                 topic_id=self.kwargs['topic_node_id'])
