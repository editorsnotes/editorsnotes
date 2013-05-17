# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
import reversion

from .. import fields, utils
from auth import Project, ProjectPermissionsMixin
from base import (Administered, CreationMetadata, LastUpdateMetadata,
                  ProjectSpecific, URLAccessible)

TYPE_CHOICES = (
    ('EVT', 'Event'),
    ('ORG', 'Organization'),
    ('PER', 'Person'),
    ('PUB', 'Publication')
)

class TopicNodeManager(models.Manager):
    @transaction.commit_on_success
    def create_project_topic(self, project, user, topic_node=None, name=None):
        """
        Connects a project & a topic, creating a topic if one is not given.
        """
        if topic_node is None and name is None:
            raise ValueError('Must pass either a topic node or a name')
        if not isinstance(project, Project) or not isinstance(user, User):
            raise ValueError('Must provide project and user as first arguments.')

        topic = topic_node or TopicNode.objects.create(
            _preferred_name=name,
            creator=user,
            last_updater=user
        )

        # If topic node is given but no name, use the most popular topic name
        name = name or topic._preferred_name
        topic.names.create(name=name, project=project, creator=user)
        return topic
    def get_or_create_project_topic(self, project, user, topic_node, name=None):
        project_topic = topic_node.names.filter(
            project_id=project.id, is_preferred=True)
        return topic_node if project_topic.exists() \
                else self.create_project_topic(project, user, topic_node, name)

class TopicMergeError(Exception):
    pass

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
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, blank=True)
    deleted = models.BooleanField(default=False, editable=False)
    merged_into = models.ForeignKey('self', blank=True, null=True, editable=False)
    related_topics = generic.GenericRelation('TopicNodeAssignment',
                                             related_name='parent_topic')
    objects = TopicNodeManager()
    class Meta:
        app_label = 'main'
    def as_text(self):
        return self._preferred_name
    @property
    def preferred_name(self):
        return self._preferred_name
    def related_objects(self, model=None, project=None):
        qs = self.assignments.all()
        if project is not None:
            qs = qs.filter(project_id=project.id)
        if model is not None:
            qs = qs.filter(content_type=ContentType.objects.get_for_model(model))
            return model.objects.filter(id__in=[ta.object_id for ta in qs])
        return sorted([ta.content_object for ta in qs], key=lambda o: repr(o))
    @transaction.commit_on_success
    def merge_project_topic_connections(self, project, into):
        names = list(TopicName.objects.select_related('topic').filter(
            project_id=project.id, topic__id__in=[self.id, into.id]))
        origin_name_objs = [n for n in names if n.topic_id == self.id]
        target_name_objs = [n for n in names if n.topic_id == into.id]

        if not len(origin_name_objs):
            raise TopicMergeError('No names connect this project & topic')

        summary_objs = list(TopicSummary.objects.filter(
            project_id=project.id, id__in=[self.id, into.id]))
        if len(summary_objs) > 1:
            raise TopicMergeError('Can\'t merge with two summaries. Delete a summary before continuing.')

        origin_summary = summary_objs[0] \
            if len(summary_objs) and summary_objs[0].project_id == project.id \
            else None

        # Keep the preferred name for the target if it exists
        target_preferred_exists = any(n.is_preferred for n in target_name_objs)
        target_names = [n.name for n in target_name_objs]

        for model in origin_name_objs:
            # If the other topic already has this name, delete it.
            if model.name in target_names:
                model.delete()
                continue
            model.topic = into
            if target_preferred_exists:
                model.is_preferred = False
            model.save()
        if origin_summary:
            origin_summary.topic = into
            origin_summary.save()

        self.deleted = True
        self.merged_into = into
        self.save()

        return into
    def get_connected_projects(self):
        """
        Return all projects connected to this topic.
        """
        return Project.objects.select_related('topicname')\
                .filter(topicname__topic_id=self.id)
    def get_project_connections(self, project):
        """
        Returns all objects connecting a topic and a project.

        Connecting objects include names, summaries, and assignments.
        """
        connections = []
        connections += [n for n in self.names.all()
                        if n.project_id == project.id]
        connections += [s for s in self.summaries.all()
                        if s.project_id == project.id]
        return connections
    def delete_project_connections(self, project, delete_empty=True):
        """
        Removes all topic connections, optionally deleting "empty" topic nodes.

        Does not return any value.

        A topic can be considered empty if it no longer has any projects
        connected to it.
        """
        connections = self.get_project_connections(project)
        for connection in connections:
            connection.delete()
        if delete_empty and self.names.count() == 0:
            self.deleted = True
            self.save()

reversion.register(TopicNode)

class ProjectTopicNameManager(models.Manager):
    def for_topic(self, topic):
        return self.get_queryset()\
                .filter(topic_id=topic.id)\
                .select_related('topic')\
                .order_by('-created')
    def counts_for_topic(self, topic):
        """
        Returns a (name, count) tuple for all names of given topic.
        """
        # This might be done faster in SQL but it's not worth it right now.
        names = self.for_topic(topic).values('name')
        names_ct = [(name, names.count(name)) for name in set(names)]
        names_ct.sort(key=lambda n: n[1])
        return names_ct
    def for_project(self, project):
        return self.get_queryset().filter(project_id=project.id)

class TopicName(CreationMetadata, ProjectPermissionsMixin):
    """
    A name identifying a topic, specific to a project.

    Project can specify multiple names to use for a topic, but at exactly one
    must be preferred.
    """
    name = models.CharField(max_length='200')
    topic = models.ForeignKey(TopicNode, related_name='names')
    project = models.ForeignKey('Project')
    is_preferred = models.BooleanField(default=True)
    objects = ProjectTopicNameManager()
    class Meta:
        app_label = 'main'
        unique_together = ('project', 'topic', 'is_preferred',)
    def __unicode__(self):
        return u'{} (topic node {})'.format(self.name, self.topic_id)
    def get_affiliation(self):
        return self.project
reversion.register(TopicName)

class TopicSummary(LastUpdateMetadata, ProjectPermissionsMixin):
    """
    A summary about a topic, specific to a project.

    Projects may only create one summary for a topic.
    """
    project = models.ForeignKey('Project')
    topic = models.ForeignKey(TopicNode, related_name='summaries')
    citations = generic.GenericRelation('Citation')
    content = fields.XHTMLField()
    class Meta:
        app_label = 'main'
        unique_together = ('project', 'topic',)
    def __unicode__(self):
        return u'Summary by {} for {}'.format(self.project.slug, self.topic)
    def get_affiliation(self):
        return self.project
reversion.register(TopicSummary)

class TopicNodeAssignment(CreationMetadata, ProjectPermissionsMixin):
    """
    An assignment of a topic to any other object, specific to a project.

    Optionally, a specific name can be used for an assignment, otherwise the
    projects' preferred name for that topic will be used.
    """
    topic = models.ForeignKey(TopicNode, related_name='assignments')
    project = models.ForeignKey('Project')
    topic_name = models.ForeignKey(TopicName, blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    class Meta:
        app_label = 'main'
        unique_together = ('content_type', 'object_id', 'topic', 'project')
    def __unicode__(self):
        return 'Topic assignment by {} for {}'.format(self.project.slug, self.topic)
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
