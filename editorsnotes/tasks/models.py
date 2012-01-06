from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core import urlresolvers
#from editorsnotes.main.models import CreationMetadata, LastUpdateMetadata, Administered, URLAccessible
from editorsnotes.main import utils
from editorsnotes.main.models import Project
from editorsnotes.main.fields import XHTMLField

TASK_STATUS_CHOICES = (
    ('0', 'Closed'),
    ('1', 'Open'),
    ('2', 'Hibernating')
)

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
            'admin:tasks_%s_change' % self._meta.module_name, args=(self.id,))

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

class Task(LastUpdateMetadata, Administered, URLAccessible):
    title = models.CharField(max_length='80', unique=True)
    project = models.ForeignKey(Project, related_name='tasks')
    status = models.CharField(max_length='1', choices=TASK_STATUS_CHOICES, default='1')
    assigned_users = models.ManyToManyField(User, blank=True)
    description = XHTMLField()
    def as_text(self):
        return "Task: %s (%s)" % (self.title, self.project)

class TaskComment(CreationMetadata):
    task = models.ForeignKey(Task, related_name='comments')
    text = models.TextField(blank=True)

class AttachmentAssignment(CreationMetadata):
    comment = models.ForeignKey(TaskComment, related_name='attachments')
    task = models.ForeignKey(Task, related_name='attachments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    def __unicode__(self):
        return '%s attachment (comment %s)' % (self.content_type.name, self.comment.id)
