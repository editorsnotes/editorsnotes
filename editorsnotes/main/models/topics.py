# -*- coding: utf-8 -*-

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
import reversion

from .. import fields, utils
from auth import Project, ProjectPermissionsMixin
from base import (
    Administered, CreationMetadata, LastUpdateMetadata, URLAccessible)


TYPE_CHOICES = (
    ('EVT', 'Event'),
    ('ORG', 'Organization'),
    ('PER', 'Person'),
    ('PUB', 'Publication')
)

class TopicMergeError(Exception):
    pass


#########################
# Main topic node model #
#########################

class TopicNode(LastUpdateMetadata, URLAccessible):
    """
    The container for projects' connections to topics.

    A Topic can be described as a person, organization, place, event,
    publication, or a generic topic/theme. The names of topics are contained in
    a separate model, but Topic nodes are identified site-wide with the most
    common names used by projects to refer to them.

    When all connections between a Topic node and projects are removed (either
    through simple deletion or merging), we can classify that Topic node as
    "empty". Instead of deleting the model, however, we specify that it was
    deleted and optionally point to the new Topic node that it was merged into.
    """
    _preferred_name = models.CharField(max_length='200')
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, blank=True, null=True)
    deleted = models.BooleanField(default=False, editable=False)
    merged_into = models.ForeignKey('self', blank=True, null=True, editable=False)
    class Meta:
        app_label = 'main'
    def as_text(self):
        return self.preferred_name
    @property
    def preferred_name(self):
        return self._preferred_name
reversion.register(TopicNode)


#################################
# Project-specific topic models #
#################################

class ProjectTopicContainerManager(models.Manager):
    def create_from_name(self, name, project, user, topic_type=None):
        topic_node = TopicNode.objects.create(preferred_name=name, creator=user,
                                              last_updater=user, type=topic_type)
        return self.create(topic_id=topic_node.id, project_id=project.id,
                           preferred_name=name, creator_id=user.id,
                           last_updater_id=user.id)
    def create_from_node(self, topic, project, user, name=None):
        return self.create(topic=topic, project=project,
                           creator=user, last_updater=user,
                           preferred_name=name or topic.preferred_name)
    def get_or_create_from_node(self, topic, project, user, name=None):
        defaults = {'creator': user, 'last_updater': user
                    'preferred_name': name or topic.preferred_name}
        return self.get_or_create(topic=topic, project=project, defaults=defaults)

class ProjectTopicContainer(LastUpdateMetadata, URLAccessible, ProjectPermissionsMixin):
    project = models.ForeignKey('Project', related_name='topic_containers')
    topic = models.ForeignKey(TopicNode, related_name='project_containers')
    preferred_name = models.CharField(max_length=200)

    deleted = models.BooleanField(default=False, editable=False)
    merged_into = models.ForeignKey('self', blank=True, null=True, editable=False)

    objects = ProjectTopicContainerManager()
    class Meta:
        app_label = 'main'
    def as_text(self):
        return '({}): {}'.format(self.project.slug, self.preferred_name)
    def has_summary(self):
        return hasattr(self, 'summary')
    @transaction.commit_on_success
    def merge_into_container(self, target):
        """
        Merge all connections from this container into another.
        """
        if self.project_id != target.project_id:
            raise TopicMergeError(
                'Can only merge topics within the same project.')

        # Move summary to new container if it exists
        if self.has_summary():
            if target.has_summary():
                raise TopicMergeError(
                    'Can\'t merge two summaries. Delete a summary before continuing.')
            self.summary.container_id = target.id
            self.summary.save()

        # Move topic assignments to the new container, but only if those
        # assignments don't already exist in the target.
        assignments = (
            ta for ta in self.assignments.all()
            if (ta.content_type_id, ta.object_id) not in
            target.assignments.values_list('content_type_id', 'object_id')
        )
        for assignment in assignments:
            assignment.container_id = target.id
            assignment.save()
        for stale_assignment in self.assignments.all():
            stale_assignment.delete()

        # Move topic names to the new container, making sure they are not marked
        # as preferred. Delete any names that exist in the target.
        target_names = target.names.values_list('name', flat=True)
        for name in self.names.all():
            if name.name in target_names:
                name.delete()
                continue
            name.is_preferred = False
            name.container_id = target.id
            name.save()

        # Save the topic to check if it should be deleted as well (see below).
        topic = self.topic

        # Point this node toward the new node.
        self.deleted = True
        self.merged_into = target
        self.save()

        # If no projects point to origin's topic node anymore, merge it into the
        # target's topic node.
        if not topic.project_containers.exists():
            topic.deleted = True
            topic.merged_into = target.topic
            topic.save()

class TopicSummary(LastUpdateMetadata, ProjectPermissionsMixin):
    """
    A summary about a topic, specific to a project.

    Projects may only create one summary for a topic.
    """
    container = models.OneToOneField(ProjectTopicContainer, related_name='summary',
                                     blank=True, null=True)
    citations = generic.GenericRelation('Citation')
    content = fields.XHTMLField()
    class Meta:
        app_label = 'main'
    def __unicode__(self):
        return u'Summary by {} for {}'.format(self.container.project.slug,
                                              self.container.topic.preferred_name)
    def get_affiliation(self):
        return self.project
reversion.register(TopicSummary)

class TopicNodeAssignment(CreationMetadata, ProjectPermissionsMixin):
    """
    An assignment of a topic to any other object, specific to a project.

    Optionally, a specific name can be used for an assignment, otherwise the
    projects' preferred name for that topic will be used.
    """
    container = models.ForeignKey(ProjectTopicContainer, blank=True, null=True, related_name='assignments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    class Meta:
        app_label = 'main'
        unique_together = ('content_type', 'object_id', 'container')
    def __unicode__(self):
        return u'{} --> {}: {} ({})'.format(
            self.container.topic.preferred_name,
            self.content_object._meta.module_name,
            self.content_object,
            self.container.project.slug)
    def get_affiliation(self):
        return self.project
reversion.register(TopicNodeAssignment)


##############################################################
# Legacy topic models (will be removed after data migration) #
##############################################################

class Topic(models.Model, URLAccessible):
    """ 
    A controlled topic such as a person name, an organization name, a
    place name, an event name, a publication name, or the name of a
    topic or theme.
    """
    preferred_name = models.CharField(max_length='80', unique=True)
    slug = models.CharField(max_length='80', unique=True, editable=False, db_index=True)
    merged_into = models.ForeignKey(TopicNode, blank=True, null=True, editable=False)
    class Meta:
        app_label = 'main'
        ordering = ['slug']
    @models.permalink
    def get_absolute_url(self):
        return ('topic_view', [self.slug])
    def as_text(self):
        return 'DEPRECATED: {}'.format(self.preferred_name)
