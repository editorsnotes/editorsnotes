from django.db import models
from django.dispatch import receiver
from editorsnotes.main.models import Document
import utils
import json
import datetime

class ZoteroLink(models.Model):
    doc = models.OneToOneField(Document, related_name='_zotero_link')
    zotero_url = models.URLField(blank=True)
    zotero_data = models.TextField()
    date_information = models.TextField(blank=True)
    cached_archive = models.ForeignKey('CachedArchive', blank=True, null=True)
    cached_creator = models.ManyToManyField('CachedCreator', blank=True, null=True)
    modified = models.DateTimeField(editable=False)
    last_synced = models.DateTimeField(blank=True, null=True)
    def save(self, update_modified=True, *args, **kwargs):
        if update_modified:
            self.modified = datetime.datetime.now()
        super(ZoteroLink, self).save(*args, **kwargs)
        item_data = json.loads(self.zotero_data)
        prev_archive = self.cached_archive
        if item_data.has_key('archive'):
            # Cache name of archive if present
            archive_query = CachedArchive.objects.get_or_create(name=item_data['archive'])
            archive = archive_query[0]
            if self not in archive.zoterolink_set.all():
                archive.zoterolink_set.add(self)
            if prev_archive and prev_archive is not archive:
                # Delete old archive if no other documents refer to it
                if len(prev_archive.zoterolink_set.all()) < 1:
                    prev_archive.delete()
            archive.save()
    def get_zotero_fields(self):
        z = json.loads(self.zotero_data)
        z['itemType'] = utils.type_map['readable'][z['itemType']]
        if self.date_information:
            date_parts = json.loads(self.date_information)
            for part in date_parts:
                z[part] = date_parts[part]
        if z['creators']:
            names = utils.resolve_names(z, 'facets')
            z.pop('creators')
            output = z.items()
            for name in names:
                for creator_type, creator_value in name.items():
                    output.append((creator_type, creator_value))
        else:
            output = z.items()
        return output

class CachedArchive(models.Model):
    name = models.TextField()

class CachedCreator(models.Model):
    name = models.TextField()
