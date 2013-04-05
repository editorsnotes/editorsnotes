from django.contrib.contenttypes import generic
from django.db import models

from .. import fields
from base import (Administered, LastUpdateMetadata, ProjectSpecific,
                  URLAccessible)

class Note(LastUpdateMetadata, Administered, URLAccessible, ProjectSpecific):
    u""" 
    Text written by an editor or curator. The text is stored as XHTML,
    so it may have hyperlinks and all the other features that XHTML
    enables.
    """
    NOTE_STATUS_CHOICES = (
        ('0', 'Closed'),
        ('1', 'Open'),
        ('2', 'Hibernating')
    )
    title = models.CharField(max_length='80', unique=True)
    content = fields.XHTMLField()
    assigned_users = models.ManyToManyField('UserProfile', blank=True, null=True)
    status = models.CharField(choices=NOTE_STATUS_CHOICES, max_length=1, default='1')
    topics = generic.GenericRelation('TopicAssignment')
    citations = generic.GenericRelation('Citation')
    def has_topic(self, topic):
        return topic.id in self.topics.values_list('topic_id', flat=True)
    def as_text(self):
        return self.title
    class Meta:
        app_label = 'main'
        ordering = ['-last_updated']  

class NoteSection(LastUpdateMetadata):
    u"""
    A section of a note, consisting of a text field and, optionally, a reference
    to a document and topic assignments.
    """
    note = models.ForeignKey(Note, related_name='sections')
    document = models.ForeignKey('Document', blank=True, null=True)
    content = fields.XHTMLField(blank=True, null=True)
    topics = generic.GenericRelation('TopicAssignment')
    class Meta:
        app_label = 'main'
    def has_content(self):
        return self.content is not None
    def get_all_related_topics(self):
        # Note sections can have their own topic assignments, but also inherit
        # the topic assignments of the parent note
        return set( [ta.topic for ta in self.note.topics.all()] +
                    [ta.topic for ta in self.topics.all()] )
