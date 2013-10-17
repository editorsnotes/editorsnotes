from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from licensing.models import License
from lxml import etree
from model_utils.managers import InheritanceManager
import reversion

from .. import fields
from auth import ProjectPermissionsMixin, UpdatersMixin
from base import Administered, LastUpdateMetadata, URLAccessible

NOTE_STATUS_CHOICES = (
    ('0', 'closed'),
    ('1', 'open'),
    ('2', 'hibernating')
)

class Note(LastUpdateMetadata, Administered, URLAccessible,
           ProjectPermissionsMixin, UpdatersMixin):
    u""" 
    Text written by an editor or curator. The text is stored as XHTML,
    so it may have hyperlinks and all the other features that XHTML
    enables.
    """
    title = models.CharField(max_length='80', unique=True)
    content = fields.XHTMLField()
    project = models.ForeignKey('Project', related_name='notes')
    assigned_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True)
    status = models.CharField(choices=NOTE_STATUS_CHOICES, max_length=1, default='1')
    license = models.ForeignKey(License, blank=True, null=True)
    related_topics = generic.GenericRelation('TopicNodeAssignment')
    sections_counter = models.PositiveIntegerField(default=0)
    class Meta:
        app_label = 'main'
        ordering = ['-last_updated']  
    def as_text(self):
        return self.title
    @models.permalink
    def get_absolute_url(self):
        return ('note_view', [self.project.slug, self.id])
    def get_affiliation(self):
        return self.project
    def has_topic(self, project_topic):
        return project_topic.id in \
                self.related_topics.values_list('container_id', flat=True)

class NoteSection(LastUpdateMetadata, ProjectPermissionsMixin):
    u"""
    The concrete base class for any note section.
    """
    _section_type = models.CharField(max_length=100)
    note = models.ForeignKey(Note, related_name='sections')
    note_section_id = models.PositiveIntegerField(blank=True, null=True)
    ordering = models.PositiveIntegerField(blank=True, null=True)
    related_topics = generic.GenericRelation('TopicNodeAssignment')
    objects = InheritanceManager()
    class Meta:
        app_label = 'main'
        ordering = ['ordering', 'note_section_id']
        unique_together = ['note', 'note_section_id']
    def get_affiliation(self):
        return self.note.project
    @property
    def section_type(self):
        return self._section_type
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
    def has_content(self):
        return self.content is not None

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

reversion.register(Note)

# to make this extendable to other note sections, should make this introspective
# or some such eventually
reversion.register(NoteSection)
reversion.register(CitationNS, follow=['notesection_ptr'])
reversion.register(TextNS, follow=['notesection_ptr'])
reversion.register(NoteReferenceNS, follow=['notesection_ptr'])
