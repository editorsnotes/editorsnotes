from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.relations import RelatedField

from editorsnotes.main.models.topics import (
    Topic, TopicNode, ProjectTopicContainer)

from .base import RelatedTopicSerializerMixin

class TopicSerializer(RelatedTopicSerializerMixin, serializers.ModelSerializer):
    topic_node_id = Field(source='topic.id')
    topics = RelatedField('related_topics', many=True)
    type = Field(source='topic.type')
    class Meta:
        model = ProjectTopicContainer
        fields = ('topic_node_id', 'preferred_name', 'type', 'topics', 'summary',)
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
