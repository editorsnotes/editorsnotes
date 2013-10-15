from django.contrib.contenttypes.models import ContentType

from rest_framework.relations import RelatedField
from rest_framework.serializers import Field, ModelSerializer
import reversion

from editorsnotes.main.models.topics import (
    ProjectTopicContainer, TopicNodeAssignment)

class URLField(Field):
    read_only = True
    def field_to_native(self, obj, field_name):
        return obj.get_absolute_url()

class ProjectSlugField(Field):
    read_only = True
    def field_to_native(self, obj, field_name):
        project = obj.get_affiliation()
        return { 'name': project.name,
                 'url': project.get_absolute_url() }

class UpdatersField(Field):
    read_only = True
    def field_to_native(self, obj, field_name):
        return [u.username for u in obj.get_all_updaters()]

class TopicAssignmentField(RelatedField):
    def __init__(self, *args, **kwargs):
        super(TopicAssignmentField, self).__init__(*args, **kwargs)
        self.many = True
    def field_to_native(self, obj, field_name):
        return [{'name': ta.container.preferred_name,
                 'url': ta.container.get_absolute_url()}
                for ta in obj.topics.all()]
    def field_from_native(self, data, files, field_name, into):
        if self.read_only:
            return
        into[field_name] = data.get(field_name, [])

class ReversionSerializerMixin(object):
    def save_object(self, *args, **kwargs):
        _save_object = super(ReversionSerializerMixin, self).save_object
        if self.context.get('create_revision', False):
            with reversion.create_revision():
                saved = _save_object(*args, **kwargs)
                reversion.set_user(self.context['request'].user)
        else:
            saved = _save_object(*args, **kwargs)
        return saved

class RelatedTopicSerializerMixin(object):
    def get_default_fields(self):
        self.field_mapping
        ret = super(RelatedTopicSerializerMixin, self).get_default_fields()
        opts = self.opts.model._meta
        topic_fields = [ f for f in opts.many_to_many
                         if f.related.parent_model == TopicNodeAssignment ]

        # There should only be one, probably, but iterate just in case?
        if len(topic_fields):
            for model_field in topic_fields:
                self.field_mapping[model_field.__class__] = TopicAssignmentField
                ret[model_field.name] = self.get_field(model_field)
                if model_field.name in self.opts.read_only_fields:
                    ret[model_field.name].read_only = True
                else:
                    ret[model_field.name].read_only = False
        return ret

    def save_related_topics(self, obj, topics):
        """
        Given an array of names, make sure obj is related to those topics.
        """
        to_create = topics[:]
        to_delete = []

        for assignment in obj.topics.select_related('container').all():
            topic_name = assignment.container.preferred_name
            if topic_name in topics:
                to_create.remove(topic_name)
            else:
                to_delete.append(assignment)

        for assignment in to_delete:
            assignment.delete()

        user = self.context['request'].user
        project = self.context['request'].project

        for topic_name in to_create:
            container = ProjectTopicContainer.objects.get_or_create_by_name(
                topic_name, project, user)
            obj.topics.create(container=container, creator_id=user.id)

    def save_object(self, obj, **kwargs):
        # Need to change to allow partial updates, etc.
        topics = []
        if getattr(obj, '_m2m_data', None):
            topics = obj._m2m_data.pop('topics')
        super(RelatedTopicSerializerMixin, self).save_object(obj, **kwargs)
        self.save_related_topics(obj, topics)
