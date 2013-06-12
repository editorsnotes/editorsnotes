# -*- coding: utf-8 -*-

import json
import re
from itertools import chain

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db import models
from django.utils.html import escape
from django.utils.safestring import mark_safe
from lxml import etree

from .. import fields, utils
from auth import ProjectPermissionsMixin
from base import CreationMetadata, LastUpdateMetadata, URLAccessible, Administered

class DocumentManager(models.Manager):
    use_for_related_fields = True
    # Include whether or not documents have scans/transcripts in default query.
    def get_query_set(self):
        return super(DocumentManager, self).get_query_set()\
            .select_related('_transcript', '_zotero_link', 'project')\
            .extra(select = { 'link_count': '''SELECT COUNT(*) 
FROM main_documentlink WHERE main_documentlink.document_id = main_document.id''',
                              'scan_count': '''SELECT COUNT(*) 
FROM main_scan WHERE main_scan.document_id = main_document.id''',
                              'part_count': '''SELECT COUNT(*) 
FROM main_document AS part WHERE part.collection_id = main_document.id''',
                              '_has_transcript': '''EXISTS ( SELECT 1 
FROM main_transcript WHERE main_transcript.document_id = main_document.id )''' })

class Document(LastUpdateMetadata, Administered, URLAccessible, ProjectPermissionsMixin):
    u"""
    Anything that can be taken as evidence for (documentation of) something.

    Documents are best defined by example: letters, newspaper articles, 
    contracts, photographs, database records, whole databases, etc. etc.
    Note that a document may be a collection of other documents.
    """
    import_id = models.CharField(max_length=64, editable=False, 
                                 blank=True, null=True, 
                                 unique=True, db_index=True)
    project = models.ForeignKey('Project', related_name='documents')
    description = fields.XHTMLField()
    collection = models.ForeignKey('self', related_name='parts', blank=True, null=True)
    ordering = models.CharField(max_length=32, editable=False)
    language = models.CharField(max_length=32, default='English')
    topics = generic.GenericRelation('TopicNodeAssignment')
    objects = DocumentManager()
    edtf_date = models.TextField(blank=True, null=True)
    class Meta:
        app_label = 'main'
        ordering = ['ordering','import_id']    
    def as_text(self):
        return utils.xhtml_to_text(self.description)
    @models.permalink
    def get_absolute_url(self):
        return ('document_view', [str(self.project.slug), str(self.id)])
    def get_affiliation(self):
        return self.project
    @property
    def transcript(self):
        try:
            return self._transcript
        except Transcript.DoesNotExist:
            return None
    def get_link_count(self):
        if hasattr(self, 'link_count'):
            return self.link_count
        return self.links.count()
    def has_links(self):
        return self.get_link_count() > 0
    def get_scan_count(self):
        if hasattr(self, 'scan_count'):
            return self.scan_count
        return self.scans.count()
    def has_scans(self):
        return self.get_scan_count() > 0
    def get_part_count(self):
        if hasattr(self, 'part_count'):
            return self.part_count
        return self.parts.count()
    def has_parts(self):
        return self.get_part_count() > 0
    def has_transcript(self):
        if hasattr(self, '_has_transcript'):
            return self._has_transcript
        return self.transcript is not None
    def zotero_link(self):
        try:
            return self._zotero_link
        except:
            return None
    def get_all_representations(self):
        r = []
        if self.has_transcript():
            r.append('Transcript')
        if self.has_scans():
            r.append('Scans')
        if hasattr(self, 'link_count') and self.link_count:
            r.append('External Link')
        return r
    def get_all_related_topics(self):
        topic_ct = ContentType.objects.get(
            app_label='main', model='projecttopiccontainer')

        topic_citations = self.citations.filter(content_type_id=topic_ct.id)
        citation_note_sections = self.citationns_set.all()
        notes = {ns.note for ns in citation_note_sections}

        return {ta.topic for ta in set(chain(
            # Explicitly related topics
            self.topics.all(),

            # The topic of any TopicSummary objects citing this doc
            [cite.content_object for cite in topic_citations],

            # The related topics of the topic gotten previously
            chain(*[cite.content_object.assignments.all()
                   for cite in topic_citations]),

            # Topics related to sections citing to this doc
            chain(*[sec.topics.all() for sec in citation_note_sections]),

            # Topics relate to the note citing this doc
            chain(*[n.topics.all() for n in notes])
        ))}
    def get_metadata(self):
        metadata = {}
        for md in self.metadata.all():
            metadata[md.key] = json.loads(md.value)
        return metadata
    def set_metadata(self, metadata, user):
        changed = False
        for k,v in metadata.iteritems():
            value = json.dumps(v)
            md, created = self.metadata.get_or_create(
                key=k, defaults={ 'value': value, 'creator': user })
            if created:
                changed = True
            elif not md.value == value:
                md.value = value
                md.save()
                changed = True
        return changed
        
    def as_html(self):
        if self.zotero_link():
            data_attributes = ''.join(
                [ ' data-%s="%s"' % (k, escape(v)) 
                  for k, v in self.zotero_link().get_zotero_fields() if v and k not in ['tags', 'extra'] ])
        else:
            data_attributes = ''
        if self.edtf_date:
            data_attributes += ' data-edtf-date="%s"' % self.edtf_date
        data_attributes += ' data-representations="%s"' % (
            self.get_all_representations()) if self.get_all_representations() else ''
        return mark_safe(
            '<div id="document-%s" class="document%s"%s>%s</div>' % (
                self.id,
                (self.has_transcript() or self.has_scans()) 
                 and ' has-scans-or-transcript' or '',
                data_attributes,
                etree.tostring(self.description)))
    def save(self, *args, **kwargs):
        self.ordering = re.sub(r'[^\w\s]', '', utils.xhtml_to_text(self.description))[:32]
        super(Document, self).save(*args, **kwargs)

class TranscriptManager(models.Manager):
    # Include related document in default query.
    def get_query_set(self):
        return super(TranscriptManager, self).get_query_set()\
            .select_related('document')

class Transcript(LastUpdateMetadata, Administered, URLAccessible, ProjectPermissionsMixin):
    u"""
    A text transcript of a document.
    """
    document = models.OneToOneField(Document, related_name='_transcript')
    content = fields.XHTMLField()
    objects = TranscriptManager()
    class Meta:
        app_label = 'main'
    def as_text(self):
        return self.document.as_text()
    def get_affiliation(self):
        return self.document.project
    def get_absolute_url(self):
        # Transcripts don't have their own URLs; use the document URL.
        return '%s#transcript' % self.document.get_absolute_url()
    def get_admin_url(self):
        return reverse('admin:main_transcript_add_or_change',
                       args=(self.document_id,))
    def as_html(self):
        return self.document.as_html()
    def get_footnote_href_ids(self):
        anchors = (self.content.cssselect('a.footnote') 
                   if self.content is not None else [])
        return [int(re.findall('\d+', a.attrib.get('href'))[0]) for a in anchors]
    def get_footnotes(self):
        fn_ids = self.get_footnote_href_ids()
        return sorted(self.footnotes.all(),
                      key=lambda fn: fn_ids.index(fn.id)
                      if fn.id in fn_ids else 9999)

class Footnote(LastUpdateMetadata, Administered, URLAccessible,
               ProjectPermissionsMixin):
    u"""
    A footnote attached to a transcript.
    """
    transcript = models.ForeignKey(Transcript, related_name='footnotes')
    content = fields.XHTMLField()
    class Meta:
        app_label = 'main'
    def get_affiliation(self):
        return self.transcript.document.project
    @models.permalink
    def get_absolute_url(self):
        document = self.transcript.document
        return ('footnote_view', [document.project.slug, document.id, self.id])
    def footnoted_text(self):
        try:
            selector = 'a.footnote[href="%s"]' % self.get_absolute_url()
            results = self.transcript.content.cssselect(selector)
            if len(results) == 1:
                return unicode(results[0].xpath('string()'))
        except NoReverseMatch: # footnote has been deleted
            pass
        return None 
    def as_text(self):
        footnoted_text = self.footnoted_text()
        if footnoted_text is None:
            return utils.xhtml_to_text(self.content)
        else:
            return footnoted_text
    def remove_self_from(self, transcript):
        selector = 'a.footnote[href="%s"]' % self.get_absolute_url()
        results = transcript.content.cssselect(selector)
        if len(results) == 1:
            results[0].drop_tag()
    def delete(self, *args, **kwargs):
        self.remove_self_from(self.transcript)
        self.transcript.save()
        super(Footnote, self).delete(*args, **kwargs)

class Scan(CreationMetadata, ProjectPermissionsMixin):
    u"""
    A scanned image of (part of) a dcument.
    """
    document = models.ForeignKey(Document, related_name='scans')
    image = models.ImageField(upload_to='scans/%Y/%m')
    ordering = models.IntegerField(blank=True, null=True)
    class Meta:
        app_label = 'main'
        ordering = ['ordering'] 
    def __unicode__(self):
        return u'Scan for %s (order: %s)' % (self.document, self.ordering)
    def get_affiliation(self):
        return self.document.project

class DocumentLink(CreationMetadata):
    u"""
    A link to an online version of or catalog entry for a document.
    """
    document = models.ForeignKey(Document, related_name='links')
    url = models.URLField()
    description = models.TextField(blank=True)
    class Meta:
        app_label = 'main'
    def __unicode__(self):
        return self.url

class DocumentMetadata(CreationMetadata):
    u"""
    Aribitrary metadata (key-value pair) for a document.
    """
    document = models.ForeignKey(Document, related_name='metadata')
    key = models.CharField(max_length=32)
    value = models.TextField()
    class Meta:
        app_label = 'main'
        unique_together = ('document', 'key')

class CitationManager(models.Manager):
    def get_for_object(self, obj):
        return self.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id)

class Citation(LastUpdateMetadata, ProjectPermissionsMixin):
    u"""
    A reference to or citation of a document.
    """
    document = models.ForeignKey(Document, related_name='citations')
    ordering = models.IntegerField(blank=True, null=True)
    notes = fields.XHTMLField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()

    objects = CitationManager()

    class Meta:
        app_label = 'main'
        ordering = ['ordering']

    def has_notes(self):
        return self.notes is not None
    def __unicode__(self):
        return u'Citation for %s (order: %s)' % (self.document, self.ordering)
    def get_affiliation(self):
        return self.document.project
