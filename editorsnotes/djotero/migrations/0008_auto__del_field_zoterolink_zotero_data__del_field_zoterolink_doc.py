# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):
    requires = (
        ('main', '0115_repopulate_zotero_fields'),
    )

    def forwards(self, orm):
        # Deleting field 'ZoteroLink.zotero_data'
        db.delete_column(u'djotero_zoterolink', 'zotero_data')

        # Deleting field 'ZoteroLink.doc'
        db.delete_column(u'djotero_zoterolink', 'doc_id')


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'ZoteroLink.zotero_data'
        raise RuntimeError("Cannot reverse this migration. 'ZoteroLink.zotero_data' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'ZoteroLink.doc'
        raise RuntimeError("Cannot reverse this migration. 'ZoteroLink.doc' and its values cannot be restored.")

    models = {
        u'djotero.cachedarchive': {
            'Meta': {'object_name': 'CachedArchive'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        u'djotero.cachedcreator': {
            'Meta': {'object_name': 'CachedCreator'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        u'djotero.zoterolink': {
            'Meta': {'object_name': 'ZoteroLink'},
            'cached_archive': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djotero.CachedArchive']", 'null': 'True', 'blank': 'True'}),
            'cached_creator': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['djotero.CachedCreator']", 'null': 'True', 'blank': 'True'}),
            'date_information': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_synced': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'zotero_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['djotero']
