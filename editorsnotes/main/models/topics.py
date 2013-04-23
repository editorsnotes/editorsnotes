# -*- coding: utf-8 -*-

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from .. import fields, utils
from base import (Administered, CreationMetadata, LastUpdateMetadata,
                  ProjectSpecific, URLAccessible)

TYPE_CHOICES = (
    ('EVT', 'Event'),
    ('ORG', 'Organization'),
    ('PER', 'Person'),
    ('PUB', 'Publication')
)

class Topic(LastUpdateMetadata, Administered, URLAccessible, ProjectSpecific):
    """ 
    A controlled topic such as a person name, an organization name, a
    place name, an event name, a publication name, or the name of a
    topic or theme.
    """
    preferred_name = models.CharField(max_length='80', unique=True)
    slug = models.CharField(max_length='80', unique=True, editable=False, db_index=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, blank=True)
    related_topics = models.ManyToManyField('self', blank=True)
    topics = generic.GenericRelation('TopicAssignment', related_name='parent_topic')
    summary = fields.XHTMLField(verbose_name='article', blank=True, null=True)
    summary_citations = generic.GenericRelation('Citation')
    has_candidate_facts = models.BooleanField(default=False)
    has_accepted_facts = models.BooleanField(default=False)
    class Meta:
        app_label = 'main'
        ordering = ['slug']
    def __init__(self, *args, **kwargs):
        super(Topic, self).__init__(*args, **kwargs)
        if 'preferred_name' in kwargs:
            self.slug = Topic.make_slug(kwargs['preferred_name'])
    @staticmethod
    def make_slug(preferred_name):
        return utils.unicode_slugify(preferred_name)
    def __setattr__(self, key, value):
        super(Topic, self).__setattr__(key, value)
        if key == 'preferred_name':
            self.slug = Topic.make_slug(value)
    def has_summary(self):
        return self.summary is not None
    def get_aliases(self):
        return u' '.join([ a.name for a in self.aliases.all() ])
    @models.permalink
    def get_absolute_url(self):
        return ('topic_view', [self.slug])
    def as_text(self):
        return self.preferred_name
    def validate_unique(self, exclude=None):
        if 'slug' in exclude:
            exclude.remove('slug')
        try:
            super(Topic, self).validate_unique(exclude)
        except ValidationError as e:
            if ('slug' in e.message_dict and 
                u'Topic with this Slug already exists.' in e.message_dict['slug']):
                e.message_dict['slug'].remove(
                    u'Topic with this Slug already exists.')
                if len(e.message_dict['slug']) == 0:
                    del e.message_dict['slug']
                if not ('preferred_name' in e.message_dict and
                        u'Topic with this Preferred name already exists.' in e.message_dict['preferred_name']):
                    if not 'preferred_name' in e.message_dict:
                        e.message_dict['preferred_name'] = []
                    e.message_dict['preferred_name'].append(u'Topic with a very similar Preferred name already exists.')
            raise e
    def related_objects(self, model=None):
        u"""
        If provided with a model, returns a queryset for that model. Otherwise,
        simply return a list of objects
        """
        if model:
            return model.objects.filter(
                id__in=[ ta.object_id for ta in self.assignments.filter(
                    content_type=ContentType.objects.get_for_model(model)) ])
        else:
            return sorted([ta.content_object for ta in self.assignments.all()],
                          key=lambda o: o.__repr__())

class Alias(CreationMetadata):
    u"""
    An alternate name for a topic.
    """
    topic = models.ForeignKey(Topic, related_name='aliases')
    name = models.CharField(max_length='80')
    class Meta(CreationMetadata.Meta):
        app_label = 'main'
        unique_together = ('topic', 'name')
        verbose_name_plural = 'aliases'
    def __unicode__(self):
        return self.name

class TopicAssignmentManager(models.Manager):
    def assigned_to_model(self, model):
        return self.select_related('topic')\
            .filter(content_type=ContentType.objects.get_for_model(model))\
            .order_by('topic__slug')

class TopicAssignment(CreationMetadata):
    u""" 
    An assignment of a topic to any other object.
    """
    topic = models.ForeignKey(Topic, related_name='assignments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    objects = TopicAssignmentManager()
    class Meta:
        app_label = 'main'
        unique_together = ('content_type', 'object_id', 'topic')
    def __unicode__(self):
        return self.topic.preferred_name
