from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from editorsnotes.main.models import CreationMetadata, LastUpdateMetadata, Administered, URLAccessible
from editorsnotes.main.models import Project

TASK_STATUS_CHOICES = (
    ('0', 'Closed'),
    ('1', 'Open'),
    ('2', 'Hibernating')
)

class Task(LastUpdateMetadata, Administered, URLAccessible):
    title = models.CharField(max_length='80', unique=True)
    project = models.ForeignKey(Project, related_name='tasks')
    status = models.CharField(max_length='1', choices=TASK_STATUS_CHOICES, default='1')
    assigned_users = models.ManyToManyField(User, blank=True)
    description = models.TextField(blank=True)
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
