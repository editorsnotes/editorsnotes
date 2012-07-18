from django.db import models
from django.contrib.auth.models import User
from editorsnotes.main.models import Topic, Document

class BaseCluster(models.Model):
    creator = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    marked_for_merge = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    class Meta:
        abstract = True

class TopicCluster(BaseCluster):
    topics = models.ManyToManyField(Topic, related_name='in_cluster')

class DocumentCluster(BaseCluster):
    documents = models.ManyToManyField(Document, related_name='in_cluster')
