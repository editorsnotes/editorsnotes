from django.db import models
from django.dispatch import receiver
from editorsnotes.main.models import Document
import utils
import json

class ZoteroLink(models.Model):
    doc = models.OneToOneField(Document, related_name='_zotero_link')
    zotero_url = models.URLField(blank=True)
    zotero_data = models.TextField()
    date_information = models.TextField(blank=True)
    cached_archive = models.ForeignKey('CachedArchive', blank=True, null=True)
    cached_creator = models.ManyToManyField('CachedCreator', blank=True, null=True)
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

@receiver(models.signals.post_save, sender=ZoteroLink)
def cache_archive(sender, **kwargs):
    zotero_item = kwargs['instance']
    item_data = json.loads(zotero_item.zotero_data)
    if item_data.has_key('archive'):
        archive_query = CachedArchive.objects.get_or_create(name=item_data['archive'])
        archive = archive_query[0]
        if zotero_item not in archive.zoterolink_set.all():
            archive.zoterolink_set.add(zotero_item)
            archive.save()
