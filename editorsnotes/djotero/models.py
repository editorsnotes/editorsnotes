from django.db import models
from editorsnotes.main.models import Document

class ZoteroLink(models.Model):
    doc = models.OneToOneField(Document, related_name='zotero_link')
    zotero_url = models.URLField()
    zotero_data = models.TextField(blank=True)
