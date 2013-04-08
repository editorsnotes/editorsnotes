from django.contrib.contenttypes import generic
from django.db import models, transaction
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
    _section_type = models.CharField(max_length=100)
    note = models.ForeignKey(Note, related_name='sections')
    note_section_id = models.PositiveIntegerField(blank=True, null=True)
    ordering = models.PositiveIntegerField(blank=True, null=True)
    topics = generic.GenericRelation('TopicAssignment')
    objects = InheritanceManager()
    class Meta:
        app_label = 'main'
        ordering = ['ordering', 'note_section_id']
        unique_together = ['note', 'note_section_id']
    def _get_section_subclass(self):
        """
        Get the subclass of this note section, used for caching.

        See this article for a good description of this method.
        http://alexgaynor.net/2009/feb/10/a-second-look-at-inheritance-and-polymorphism-with-django/
        """
        section_subclasses = NoteSection._meta.get_all_related_objects()
        for cls in section_subclasses:
            if isinstance(cls, models.related.RelatedObject) and \
                   cls.field.primary_key and \
                   cls.opts == self._meta:
                return cls.get_accessor_name()
        else:
            raise Exception('Could not find note section subclass')
    @transaction.commit_on_success
    def save(self, *args, **kwargs):
        if not self.id:
            n = self.note
            self.note_section_id = n.sections_counter = n.sections_counter + 1
            n.save()
            self._section_type = self._get_section_subclass()
        return super(NoteSection, self).save(*args, **kwargs)

class CitationNS(NoteSection):
    document = models.ForeignKey('Document')
    content = fields.XHTMLField(blank=True, null=True)
    section_type_label = 'citation'
    class Meta:
        app_label = 'main'
    def __unicode__(self):
        return u'Note section -- citation -- {}'.format(self.document)

class TextNS(NoteSection):
    content = fields.XHTMLField()
    section_type_label = 'text'
    class Meta:
        app_label = 'main'
    def __unicode__(self):
        content_str = etree.tostring(self.content)
        return u'Note section -- text -- {}'.format(
            content_str[:20] + '...' if len(content_str) > 20 else '')

class NoteReferenceNS(NoteSection):
    note_reference = models.ForeignKey(Note)
    content = fields.XHTMLField(blank=True, null=True)
    section_type_label = 'note_reference'
    class Meta:
        app_label = 'main'
    def __unicode__(self):
        return u'Note section -- reference -- {}'.format(self.note_reference)
    def has_content(self):
        return self.content is not None
