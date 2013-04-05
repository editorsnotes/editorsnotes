from django.contrib.contenttypes import generic
from django.db import models
from lxml import etree
from model_utils.managers import InheritanceManager

from .. import fields
from base import (Administered, LastUpdateMetadata, ProjectSpecific,
                  URLAccessible)

NOTE_STATUS_CHOICES = (
    ('0', 'Closed'),
    ('1', 'Open'),
    ('2', 'Hibernating')
)

class Note(LastUpdateMetadata, Administered, URLAccessible, ProjectSpecific):
    u""" 
    Text written by an editor or curator. The text is stored as XHTML,
    so it may have hyperlinks and all the other features that XHTML
    enables.
    """
    title = models.CharField(max_length='80', unique=True)
    content = fields.XHTMLField()
    assigned_users = models.ManyToManyField('UserProfile', blank=True, null=True)
    status = models.CharField(choices=NOTE_STATUS_CHOICES, max_length=1, default='1')
    topics = generic.GenericRelation('TopicAssignment')
    citations = generic.GenericRelation('Citation')
    sections_counter = models.PositiveIntegerField(default=0)
    def has_topic(self, topic):
        return topic.id in self.topics.values_list('topic_id', flat=True)
    def as_text(self):
        return self.title
    class Meta:
        app_label = 'main'
        ordering = ['-last_updated']  

class NoteSection(LastUpdateMetadata):
    u"""
    The concrete base class for any note section.
    """
    note = models.ForeignKey(Note, related_name='sections')
    note_section_id = models.PositiveIntegerField(blank=True, null=True)
    ordering = models.PositiveIntegerField(blank=True, null=True)
    topics = generic.GenericRelation('TopicAssignment')
    objects = InheritanceManager()
    class Meta:
        app_label = 'main'
        ordering = ['ordering', 'note_section_id']
        #unique_together = ['note', 'note_section_id']
    def save(self, *args, **kwargs):
        n = self.note
        save_note = False
        if not self.note_section_id:
            save_note = True
            self.note_section_id = n.sections_counter = n.sections_counter + 1
        super(NoteSection, self).save(*args, **kwargs)
        if save_note:
            n.save()

class CitationNS(NoteSection):
    document = models.ForeignKey('Document')
    content = fields.XHTMLField(blank=True, null=True)
    section_type = 'citation'
    class Meta:
        app_label = 'main'
    def __unicode__(self):
        return 'Note section -- citation -- {}'.format(self.document)

class TextNS(NoteSection):
    content = fields.XHTMLField()
    section_type = 'text'
    class Meta:
        app_label = 'main'
    def __unicode__(self):
        content_str = etree.tostring(self.content)
        return 'Note section -- text -- {}'.format(
            content_str[:20] + '...' if len(content_str) > 20 else '')

class NoteReferenceNS(NoteSection):
    note_reference = models.ForeignKey(Note)
    content = fields.XHTMLField(blank=True, null=True)
    section_type = 'note_reference'
    class Meta:
        app_label = 'main'
    def __unicode__(self):
        return 'Note section -- reference -- {}'.format(self.note_reference)
