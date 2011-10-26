from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from editorsnotes.main.models import CreationMetadata, LastUpdateMetadata, Administered, URLAccessible
from editorsnotes.main.models import Project

class Task(LastUpdateMetadata, Administered, URLAccessible):
    title = models.CharField(max_length='80', unique=True)
    project = models.ForeignKey(Project, related_name='affiliated_project')
    assignees = models.ManyToManyField(User, blank=True)
    description = models.TextField(blank=True)
    def get_involved_users(self):
        pass
    def as_text(self):
        return "Task: %s (%s)" % (self.title, self.project)
    def get_comments(self):
        Comment.objects.filter(task=self)

class Comment(CreationMetadata):
    task = models.ForeignKey(Task, related_name='comments')
    text = models.TextField(blank=True)
    def has_attachments(self):
        pass
    def get_attachments(self):
        pass

class AttachmentAssignment(CreationMetadata):
    comment = models.ForeignKey(Comment, related_name='attachments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
