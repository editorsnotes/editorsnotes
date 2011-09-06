from django.db import models
from editorsnotes.main.models import Topic

# Create your models here.

class TopicCluster(models.Model):
    clustered_topics = models.ManyToManyField(Topic)
