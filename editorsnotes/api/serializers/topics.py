from collections import OrderedDict

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.relations import RelatedField

from editorsnotes.main.models.topics import (
    Topic, TopicNode, ProjectTopicContainer)

from .base import RelatedTopicSerializerMixin, ProjectSlugField, URLField

class TopicNodeSerializer(serializers.ModelSerializer):
    name = Field(source='_preferred_name')
    url = URLField()
    alternate_forms = serializers.SerializerMethodField('get_alternate_forms')
    projects = serializers.SerializerMethodField('get_project_value')
    class Meta:
        model = TopicNode
        fields = ('id', 'name', 'url', 'alternate_forms', 'type', 'projects',)
    def get_alternate_forms(self, obj):
        topics = obj.project_containers.select_related('alternate_names')
        alternate_forms = set() 
        alternate_forms.update(topic.preferred_name for topic in topics)
        alternate_forms.update(
            alternate_name.name
            for topic in topics
            for alternate_name in topic.alternate_names.all())
        alternate_forms.remove(obj._preferred_name)
        return list(alternate_forms)
    def get_project_value(self, obj):
        return [OrderedDict((
            ('name', topic.project.name),
            ('url', topic.project.get_absolute_url()),
            ('preferred_name', topic.preferred_name),
            ('topic_url', reverse('api:api-topics-detail',
                                  args=(topic.project.slug, obj.id)))))
            for topic in obj.project_containers.select_related('project')]


class TopicSerializer(RelatedTopicSerializerMixin, serializers.ModelSerializer):
    id = Field(source='topic_id')
    type = Field(source='topic.type')
    url = URLField()
    project = ProjectSlugField()
    class Meta:
        model = ProjectTopicContainer
        fields = ('id', 'preferred_name', 'type', 'url', 'topics', 'project',
                  'last_updated', 'summary')
    def save_object(self, obj, **kwargs):
        if not obj.id:
            topic_node_id = self.context.get('topic_node_id', None)
            if topic_node_id is None and 'view' in self.context:
                topic_node_id = self.context['view'].kwargs.get(
                    'topic_node_id', None)
            if topic_node_id is None:
                topic_node = TopicNode.objects.create(
                    _preferred_name=obj.preferred_name,
                    creator_id=obj.creator_id,
                    last_updater_id=obj.creator_id)
                topic_node_id = topic_node.id
            obj.topic_id = topic_node_id
        return super(TopicSerializer, self).save_object(obj, **kwargs)
