from django.db import models
from editorsnotes.main.models import Document
import utils
import json

class ZoteroLink(models.Model):
    doc = models.OneToOneField(Document, related_name='_zotero_link')
    zotero_url = models.URLField()
    zotero_data = models.TextField(blank=True)
    date_information = models.TextField(blank=True)
    def __str__(self):
        return 'Zotero data: %s' % self.doc.__str__()
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
