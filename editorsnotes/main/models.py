# -*- coding: utf-8 -*-

import re
import utils
import fields
import json
from copy import deepcopy
from lxml import etree
from unaccent import unaccent
from django.db import models
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core import urlresolvers
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import NoReverseMatch
from django.utils.html import conditional_escape, escape
from django.utils.safestring import mark_safe
from io import StringIO
import reversion

# -------------------------------------------------------------------------------
# Abstract base classes and interfaces.
# -------------------------------------------------------------------------------

class CreationMetadata(models.Model):
    creator = models.ForeignKey(User, editable=False, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True
        get_latest_by = 'created'

class LastUpdateMetadata(CreationMetadata):
    last_updater = models.ForeignKey(User, editable=False, related_name='last_to_update_%(class)s_set')
    last_updated = models.DateTimeField(auto_now=True)    
    class Meta:
        abstract = True

class Administered():
    def get_admin_url(self):
        return urlresolvers.reverse(
            'admin:main_%s_change' % self._meta.module_name, args=(self.id,))

class URLAccessible():
    @models.permalink
    def get_absolute_url(self):
        return ('%s_view' % self._meta.module_name, [str(self.id)])
    def __unicode__(self):
        return utils.truncate(self.as_text())
    def as_text(self):
        raise Exception('Must implement %s.as_text()' % self._meta.module_name)
    def as_html(self):
        return '<span class="%s">%s</span>' % (
            self._meta.module_name, conditional_escape(self.as_text()))

class PermissionError(StandardError):
    pass

# Adapted from http://djangosnippets.org/snippets/1502/
class PermissionsMixin(object):
    def attempt(self, action, user, msg=None):
        return PermissionsMixin._attempt(self, action, user, msg)

    @staticmethod
    def _attempt(obj, action, user, msg):
        if not (isinstance(action, basestring) and isinstance(user, User)):
            raise TypeError
        if getattr(obj, 'allow_%s_for' % action)(user):
            return True
        else:
            if msg is None:
                msg = u'%s doesn\'t have permission to %s %s' % (
                    user.username, action.lower(), repr(obj) )
            raise PermissionError(msg)

class ProjectSpecific(models.Model, PermissionsMixin):
    affiliated_projects = models.ManyToManyField('Project', blank=True,
                                                 null=True)

    def get_all_updaters(self):
        all_updaters = set()
        for version in reversion.get_for_object(self):
            uid = json.loads(
                version.serialized_data)[0]['fields'].get('last_updater')
            if uid:
                all_updaters.add(uid)
        return [UserProfile.objects.get(user__id=u) for u in all_updaters]
    def get_project_affiliation(self):
        projects = {u.affiliation for u in self.get_all_updaters() if u.affiliation}
        return list(projects)
    def save(self, *args, **kwargs):
        super(ProjectSpecific, self).save(*args, **kwargs)
        last_updating_project = self.last_updater.get_profile().affiliation
        if last_updating_project:
            self.affiliated_projects.add(last_updating_project)

    # Custom Project permissions
    def allow_delete_for(self, user):
        object_affiliation = self.affiliated_projects.all()
        # Make sure no other projects are using this object before deleting
        other_contributing_projects = set.difference(
            set(object_affiliation), set([user.get_profile().affiliation]))
        if len(other_contributing_projects) and not user.is_superuser:
            msg = 'Cannot delete %s because it is in use by %s' % (
                self, ', '.join([p.name for p in other_contributing_projects]))
            raise PermissionError(msg)
        else:
            return True
    def allow_change_for(self, user):
        object_affiliation = self.affiliated_projects.all()
        can_change = False
        while not can_change:
            for p in object_affiliation:
                can_change = user.has_perm('%s.change_%s' % (
                    p.slug, self._meta.module_name))
        return can_change
    def allow_view_for(self, user):
        object_affiliation = self.affiliated_projects.all()
        can_view = False
        while not can_view:
            for p in object_affiliation:
                can_view = user.has_perm('%s.view_%s' % (
                    p.slug, self._meta.module_name))
        return can_view

    class Meta:
        abstract = True

# -------------------------------------------------------------------------------
# Primary models. These have their own URLs and administration interfaces.
# -------------------------------------------------------------------------------

class DocumentManager(models.Manager):
    # Include whether or not documents have scans/transcripts in default query.
    def get_query_set(self):
        return super(DocumentManager, self).get_query_set()\
            .select_related('_transcript')\
            .extra(select = { 'link_count': '''SELECT COUNT(*) 
FROM main_documentlink WHERE main_documentlink.document_id = main_document.id''',
                              'scan_count': '''SELECT COUNT(*) 
FROM main_scan WHERE main_scan.document_id = main_document.id''',
                              'part_count': '''SELECT COUNT(*) 
FROM main_document AS part WHERE part.collection_id = main_document.id''',
                              '_has_transcript': '''EXISTS ( SELECT 1 
FROM main_transcript WHERE main_transcript.document_id = main_document.id )''' })

class Document(LastUpdateMetadata, Administered, URLAccessible, ProjectSpecific):
    u"""
    Anything that can be taken as evidence for (documentation of) something.

    Documents are best defined by example: letters, newspaper articles, 
    contracts, photographs, database records, whole databases, etc. etc.
    Note that a document may be a collection of other documents.
    """
    import_id = models.CharField(max_length=64, editable=False, 
                                 blank=True, null=True, 
                                 unique=True, db_index=True)
    description = fields.XHTMLField()
    collection = models.ForeignKey('self', related_name='parts', blank=True, null=True)
    ordering = models.CharField(max_length=32, editable=False)
    language = models.CharField(max_length=32, default='English')
    topics = generic.GenericRelation('TopicAssignment')
    objects = DocumentManager()
    edtf_date = models.TextField(blank=True, null=True)
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
    def get_all_related_topics(self):
        topics = []
        topics += [ta.topic for ta in self.topics.all()]
        topics += [c.content_object for c in self.citations.filter(
            content_type=ContentType.objects.get_for_model(Topic))]
        return topics
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
        
    def as_text(self):
        return utils.xhtml_to_text(self.description)
    def as_html(self):
        if self.zotero_link():
            data_attributes = ''.join(
                [ ' data-%s="%s"' % (k, escape(v)) 
                  for k, v in self.zotero_link().get_zotero_fields() if v != "" and k not in ['tags', 'extra'] ])
        else:
            data_attributes = ''
        if self.edtf_date:
            data_attributes += ' data-edtf-date="%s"' % self.edtf_date
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
    class Meta:
        ordering = ['ordering','import_id']    
    # --------------------------------------------------------------------------------
    # The following is a workaround for this Django bug: 
    # http://code.djangoproject.com/ticket/13839
    # --------------------------------------------------------------------------------
    def _collect_sub_objects(self, seen_objs, parent=None, nullable=False):
        """
        Recursively populates seen_objs with all objects related to this
        object.

        When done, seen_objs.items() will be in the format:
            [(model_class, {pk_val: obj, pk_val: obj, ...}),
             (model_class, {pk_val: obj, pk_val: obj, ...}), ...]
        """
        pk_val = self._get_pk_val()
        if seen_objs.add(self.__class__, pk_val, self,
                         type(parent), parent, nullable):
            return

        for related in self._meta.get_all_related_objects():
            rel_opts_name = related.get_accessor_name()
            if not related.field.rel.multiple:
                try:
                    sub_obj = getattr(self, rel_opts_name)
                except ObjectDoesNotExist:
                    pass
                else:
                    if sub_obj is not None:
                        sub_obj._collect_sub_objects(seen_objs, self, related.field.null)
            else:
                # To make sure we can access all elements, we can't use the
                # normal manager on the related object. So we work directly
                # with the descriptor object.
                for cls in self.__class__.mro():
                    if rel_opts_name in cls.__dict__:
                        rel_descriptor = cls.__dict__[rel_opts_name]
                        break
                else:
                    # in the case of a hidden fkey just skip it, it'll get
                    # processed as an m2m
                    if not related.field.rel.is_hidden():
                        raise AssertionError("Should never get here.")
                    else:
                        continue
                delete_qs = rel_descriptor.delete_manager(self).all()
                for sub_obj in delete_qs:
                    sub_obj._collect_sub_objects(seen_objs, self, related.field.null)

        for related in self._meta.get_all_related_many_to_many_objects():
            if related.field.rel.through:
                db = router.db_for_write(related.field.rel.through.__class__, instance=self)
                opts = related.field.rel.through._meta
                reverse_field_name = related.field.m2m_reverse_field_name()
                nullable = opts.get_field(reverse_field_name).null
                filters = {reverse_field_name: self}
                for sub_obj in related.field.rel.through._base_manager.using(db).filter(**filters):
                    sub_obj._collect_sub_objects(seen_objs, self, nullable)

        for f in self._meta.many_to_many:
            if f.rel.through:
                db = router.db_for_write(f.rel.through.__class__, instance=self)
                opts = f.rel.through._meta
                field_name = f.m2m_field_name()
                nullable = opts.get_field(field_name).null
                filters = {field_name: self}
                for sub_obj in f.rel.through._base_manager.using(db).filter(**filters):
                    sub_obj._collect_sub_objects(seen_objs, self, nullable)
            else:
                # m2m-ish but with no through table? GenericRelation: cascade delete
                for sub_obj in f.value_from_object(self).all():
                    # Generic relations not enforced by db constraints, thus we can set
                    # nullable=True, order does not matter
                    sub_obj._collect_sub_objects(seen_objs, self, True)

        # Handle any ancestors (for the model-inheritance case). We do this by
        # traversing to the most remote parent classes -- those with no parents
        # themselves -- and then adding those instances to the collection. That
        # will include all the child instances down to "self".
        parent_stack = [p for p in self._meta.parents.values() if p is not None]
        while parent_stack:
            link = parent_stack.pop()
            parent_obj = getattr(self, link.name)
            if parent_obj._meta.parents:
                parent_stack.extend(parent_obj._meta.parents.values())
                continue
            # At this point, parent_obj is base class (no ancestor models). So
            # delete it and all its descendents.
            parent_obj._collect_sub_objects(seen_objs)
    # --------------------------------------------------------------------------------
    # End workaround
    # --------------------------------------------------------------------------------

class TranscriptManager(models.Manager):
    # Include related document in default query.
    def get_query_set(self):
        return super(TranscriptManager, self).get_query_set()\
            .select_related('document')

class Transcript(LastUpdateMetadata, Administered, URLAccessible):
    u"""
    A text transcript of a document.
    """
    document = models.OneToOneField(Document, related_name='_transcript')
    content = fields.XHTMLField()
    objects = TranscriptManager()
    def get_absolute_url(self):
        # Transcripts don't have their own URLs; use the document URL.
        return '%s#transcript' % self.document.get_absolute_url()
    def as_text(self):
        return self.document.as_text()
    def as_html(self):
        return self.document.as_html()

class Footnote(LastUpdateMetadata, Administered, URLAccessible):
    u"""
    A footnote attached to a transcript.
    """
    transcript = models.ForeignKey(Transcript, related_name='footnotes')
    content = fields.XHTMLField()
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

class Topic(LastUpdateMetadata, Administered, URLAccessible, ProjectSpecific):
    """ 
    A controlled topic such as a person name, an organization name, a
    place name, an event name, a publication name, or the name of a
    topic or theme.
    """
    TYPE_CHOICES = (
        ('EVT', 'Event'),
        ('ORG', 'Organization'),
        ('PER', 'Person'),
        ('PUB', 'Publication'))
    preferred_name = models.CharField(max_length='80', unique=True)
    slug = models.CharField(max_length='80', unique=True, editable=False, db_index=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, blank=True)
    related_topics = models.ManyToManyField('self', blank=True)
    summary = fields.XHTMLField(verbose_name='article', blank=True, null=True)
    summary_citations = generic.GenericRelation('Citation')
    has_candidate_facts = models.BooleanField(default=False)
    has_accepted_facts = models.BooleanField(default=False)
    def __init__(self, *args, **kwargs):
        super(Topic, self).__init__(*args, **kwargs)
        if 'preferred_name' in kwargs:
            self.slug = Topic.make_slug(kwargs['preferred_name'])
    @staticmethod
    def make_slug(preferred_name):
        return '-'.join(
            [ x for x in re.split('\W+', unaccent(unicode(preferred_name)))
              if len(x) > 0 ]).lower()
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
        return ('topic_view', [str(self.slug)])
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
        if model:
            return [ ta.content_object for ta in self.assignments.filter(
                    content_type=ContentType.objects.get_for_model(model)) ]
        else:
            return sorted([ta.content_object for ta in self.assignments.all()],
                          key=lambda o: o.__repr__())
    class Meta:
        ordering = ['slug']

class Note(LastUpdateMetadata, Administered, URLAccessible, ProjectSpecific):
    u""" 
    Text written by an editor or curator. The text is stored as XHTML,
    so it may have hyperlinks and all the other features that XHTML
    enables.
    """
    title = models.CharField(max_length='80', unique=True)
    content = fields.XHTMLField()
    topics = generic.GenericRelation('TopicAssignment')
    citations = generic.GenericRelation('Citation')
    def has_topic(self, topic):
        return topic.id in self.topics.values_list('topic_id', flat=True)
    def as_text(self):
        return self.title
    class Meta:
        ordering = ['-last_updated']  

class NoteSection(LastUpdateMetadata):
    u"""
    A section of a note, consisting of a text field and, optionally, a reference
    to a document and topic assignments.
    """
    note = models.ForeignKey(Note, related_name='sections')
    document = models.ForeignKey(Document, blank=True, null=True)
    content = fields.XHTMLField(blank=True, null=True)
    def has_content(self):
        return self.content is not None

class Project(models.Model, URLAccessible, PermissionsMixin):
    name = models.CharField(max_length='80')
    slug = models.SlugField(help_text='Used for project-specific URLs and groups')
    image = models.ImageField(upload_to='project_images', blank=True, null=True)
    description = fields.XHTMLField(blank=True, null=True)
    @models.permalink
    def get_absolute_url(self):
        return ('project_view', [self.slug])
    def as_text(self):
        return self.name
    def allow_view_for(self, user):
        if user.has_perm('main.%s.view_project' % self.slug) or user.is_superuser:
            return True
        else:
            return False
    def allow_change_for(self, user):
        if user.has_perm('main.%s.change_project' % self.slug) or user.is_superuser:
            return True
        else:
            return False
    def get_or_create_project_roles(self):
        base_project_permissions = (
            (Note, ('change',)),
            (Project, ('view',)),
        )
        editor_project_permissions = (
            (Project, ('change',)),
        )

        slug = self.slug
        editors, created = Group.objects.get_or_create(
            name='%s_editors' % slug)
        researchers, created = Group.objects.get_or_create(
            name='%s_researchers' % slug)

        for model, actions in base_project_permissions:
            ct = ContentType.objects.get_for_model(model)
            for action in actions:
                perm, created = Permission.objects.get_or_create(
                    content_type=ct,
                    codename='%s.%s_%s' % (
                        slug, action, model._meta.module_name),
                    name='Can %s %s %s' % (
                        action, slug, model._meta.verbose_name_plural.lower())
                )
                editors.permissions.add(perm)
                researchers.permissions.add(perm)
        for model, actions in editor_project_permissions:
            ct = ContentType.objects.get_for_model(model)
            for action in actions:
                perm, created = Permission.objects.get_or_create(
                    content_type=ct,
                    codename='%s.%s_%s' % (
                        slug, action, model._meta.module_name),
                    name='Can %s %s %s' % (
                        action, slug, model._meta.verbose_name_plural.lower())
                )
                editors.permissions.add(perm)
    def save(self):
        super(Project, self).save()
        self.get_or_create_project_roles()
        
class UserProfile(models.Model, URLAccessible):
    user = models.ForeignKey(User, unique=True)
    affiliation = models.ForeignKey('Project', blank=True, null=True)
    zotero_key = models.CharField(max_length='24', blank=True, null=True)
    zotero_uid = models.CharField(max_length='6', blank=True, null=True)
    def _get_display_name(self):
        "Returns the full name if available, or the username if not."
        display_name = self.user.username
        if self.user.first_name:
            display_name = self.user.first_name
            if self.user.last_name:
                display_name = '%s %s' % (self.user.first_name, self.user.last_name)
        return display_name
    display_name = property(_get_display_name)
    @models.permalink
    def get_absolute_url(self):
        return ('user_view', [str(self.user.username)])
    def as_text(self):
        return self.display_name
    @staticmethod
    def get_for(user):
        try:
            return user.get_profile()
        except UserProfile.DoesNotExist:
            return UserProfile.objects.create(user=user)
    @staticmethod
    def get_activity_for(user, max_count=50):
        object_urls = set()
        checked_object_ids = { 
            'topic': [], 'note': [], 'document': [], 'transcript': [] }
        activity = []
        for entry in LogEntry.objects\
                .select_related('content_type__name')\
                .filter(content_type__app_label='main',  
                        content_type__model__in=checked_object_ids.keys(), 
                        user=user):
            if entry.object_id in checked_object_ids[entry.content_type.name]:
                continue
            checked_object_ids[entry.content_type.name].append(entry.object_id)
            if entry.is_deletion():
                continue
            try:
                obj = entry.get_edited_object()
            except ObjectDoesNotExist:
                continue
            object_url = obj.get_absolute_url().split('#')[0]
            if object_url in object_urls:
                continue
            object_urls.add(object_url)
            activity.append({ 'what': obj, 'when': entry.action_time })
            if len(activity) == max_count:
                break
        return activity, checked_object_ids
    def get_project_role(self, project):
        try:
            role = Group.objects.get(
                user=self.user,
                name__startswith=project.slug)
            return role.name[role.name.index('_') + 1:-1]
        except Group.DoesNotExist:
            return None
    def save(self):
        if self.affiliation:
            project_groups = self.user.groups.filter(
                user = self.user,
                name__startswith=self.affiliation.slug)
            if len(project_groups) > 1:
                raise Exception("Only one project role allowed")
        super(UserProfile, self).save()
        if self.affiliation and not self.get_project_role(self.affiliation):
            if self.user.groups.filter(name='Editors'):
                g = Group.objects.get(name='%s_editors' % self.affiliation.slug)
            else:
                g = Group.objects.get(name='%s_researchers' % self.affiliation.slug)
            self.user.groups.add(g)

# -------------------------------------------------------------------------------
# Support models.
# -------------------------------------------------------------------------------

class Alias(CreationMetadata):
    u"""
    An alternate name for a topic.
    """
    topic = models.ForeignKey(Topic, related_name='aliases')
    name = models.CharField(max_length='80')
    def __unicode__(self):
        return self.name
    class Meta(CreationMetadata.Meta):
        unique_together = ('topic', 'name')
        verbose_name_plural = 'aliases'

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
    def __unicode__(self):
        return self.topic.preferred_name

class Scan(CreationMetadata):
    u"""
    A scanned image of (part of) a dcument.
    """
    document = models.ForeignKey(Document, related_name='scans')
    image = models.ImageField(upload_to='scans/%Y/%m')
    ordering = models.IntegerField(blank=True, null=True)
    def __unicode__(self):
        return u'Scan for %s (order: %s)' % (self.document, self.ordering)
    class Meta:
        ordering = ['ordering'] 

class Citation(CreationMetadata):
    u"""
    A reference to or citation of a document.
    """
    document = models.ForeignKey(Document, related_name='citations')
    ordering = models.IntegerField(blank=True, null=True)
    notes = fields.XHTMLField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    def has_notes(self):
        return self.notes is not None
    def __unicode__(self):
        return u'Citation for %s (order: %s)' % (self.document, self.ordering)
    class Meta:
        ordering = ['ordering']

class DocumentLink(CreationMetadata):
    u"""
    A link to an online version of or catalog entry for a document.
    """
    document = models.ForeignKey(Document, related_name='links')
    url = models.URLField(verify_exists=True)
    description = models.TextField(blank=True)
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
        unique_together = ('document', 'key')
