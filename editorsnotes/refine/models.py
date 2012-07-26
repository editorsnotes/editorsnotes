from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from editorsnotes.main.models import Topic, Document

class BaseCluster(models.Model):
    creator = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    marked_for_merge = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    @models.permalink
    def get_absolute_url(self):
        return ('%s_view' % self._meta.module_name, [str(self.id)])
    class Meta:
        abstract = True

class TopicCluster(BaseCluster):
    topics = models.ManyToManyField(Topic, related_name='in_cluster')
    @models.permalink
    def get_absolute_url(self):
        return ('merge_topic_cluster_view', [str(self.id)])

class DocumentCluster(BaseCluster):
    documents = models.ManyToManyField(Document, related_name='in_cluster')
    @models.permalink
    def get_absolute_url(self):
        return ('merge_document_cluster_view', [str(self.id)])

class BadClusterPair(models.Model):
    content_type = models.ForeignKey(ContentType)
    obj1 = models.PositiveIntegerField()
    obj2 = models.PositiveIntegerField()

