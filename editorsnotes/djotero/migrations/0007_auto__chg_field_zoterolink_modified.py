# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'ZoteroLink.modified'
        db.alter_column('djotero_zoterolink', 'modified', self.gf('django.db.models.fields.DateTimeField')())


    def backwards(self, orm):
        
        # Changing field 'ZoteroLink.modified'
        db.alter_column('djotero_zoterolink', 'modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'djotero.cachedarchive': {
            'Meta': {'object_name': 'CachedArchive'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'djotero.cachedcreator': {
            'Meta': {'object_name': 'CachedCreator'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'djotero.zoterolink': {
            'Meta': {'object_name': 'ZoteroLink'},
            'cached_archive': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['djotero.CachedArchive']", 'null': 'True', 'blank': 'True'}),
            'cached_creator': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['djotero.CachedCreator']", 'null': 'True', 'blank': 'True'}),
            'date_information': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'doc': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'_zotero_link'", 'unique': 'True', 'to': "orm['main.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_synced': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {}),
            'zotero_data': ('django.db.models.fields.TextField', [], {}),
            'zotero_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'main.citation': {
            'Meta': {'ordering': "['ordering']", 'object_name': 'Citation'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_citation_set'", 'to': "orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'citations'", 'to': "orm['main.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('editorsnotes.main.fields.XHTMLField', [], {'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'main.document': {
            'Meta': {'ordering': "['ordering', 'import_id']", 'object_name': 'Document'},
            'collection': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parts'", 'null': 'True', 'to': "orm['main.Document']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_document_set'", 'to': "orm['auth.User']"}),
            'description': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'English'", 'max_length': '32'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_document_set'", 'to': "orm['auth.User']"}),
            'ordering': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'main.topic': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Topic'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topic_set'", 'to': "orm['auth.User']"}),
            'has_accepted_facts': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_candidate_facts': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topic_set'", 'to': "orm['auth.User']"}),
            'preferred_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'80'"}),
            'related_topics': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_topics_rel_+'", 'blank': 'True', 'to': "orm['main.Topic']"}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'80'", 'db_index': 'True'}),
            'summary': ('editorsnotes.main.fields.XHTMLField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'})
        },
        'main.topicassignment': {
            'Meta': {'object_name': 'TopicAssignment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicassignment_set'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['main.Topic']"})
        }
    }

    complete_apps = ['djotero']
