# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Alias', fields ['topic', 'name']
        db.delete_unique(u'main_alias', ['topic_id', 'name'])

        # Removing unique constraint on 'TopicAssignment', fields ['content_type', 'object_id', 'topic']
        db.delete_unique(u'main_topicassignment', ['content_type_id', 'object_id', 'topic_id'])

        # Deleting model 'TopicAssignment'
        db.delete_table(u'main_topicassignment')

        # Deleting model 'Alias'
        db.delete_table(u'main_alias')

        # Deleting field 'Topic.last_updated'
        db.delete_column(u'main_topic', 'last_updated')

        # Deleting field 'Topic.creator'
        db.delete_column(u'main_topic', 'creator_id')

        # Deleting field 'Topic.last_updater'
        db.delete_column(u'main_topic', 'last_updater_id')

        # Deleting field 'Topic.summary'
        db.delete_column(u'main_topic', 'summary')

        # Deleting field 'Topic.has_accepted_facts'
        db.delete_column(u'main_topic', 'has_accepted_facts')

        # Deleting field 'Topic.created'
        db.delete_column(u'main_topic', 'created')

        # Deleting field 'Topic.has_candidate_facts'
        db.delete_column(u'main_topic', 'has_candidate_facts')

        # Deleting field 'Topic.type'
        db.delete_column(u'main_topic', 'type')

        # Adding field 'Topic.merged_into'
        db.add_column(u'main_topic', 'merged_into',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.TopicNode'], null=True, blank=True),
                      keep_default=False)

        # Removing M2M table for field related_topics on 'Topic'
        db.delete_table('main_topic_related_topics')

        # Removing M2M table for field affiliated_projects on 'Topic'
        db.delete_table('main_topic_affiliated_projects')


    def backwards(self, orm):
        # Adding model 'TopicAssignment'
        db.create_table(u'main_topicassignment', (
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_topicassignment_set', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments', to=orm['main.Topic'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['TopicAssignment'])

        # Adding unique constraint on 'TopicAssignment', fields ['content_type', 'object_id', 'topic']
        db.create_unique(u'main_topicassignment', ['content_type_id', 'object_id', 'topic_id'])

        # Adding model 'Alias'
        db.create_table(u'main_alias', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length='80')),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_alias_set', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(related_name='aliases', to=orm['main.Topic'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['Alias'])

        # Adding unique constraint on 'Alias', fields ['topic', 'name']
        db.create_unique(u'main_alias', ['topic_id', 'name'])


        # User chose to not deal with backwards NULL issues for 'Topic.last_updated'
        raise RuntimeError("Cannot reverse this migration. 'Topic.last_updated' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Topic.creator'
        raise RuntimeError("Cannot reverse this migration. 'Topic.creator' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Topic.last_updater'
        raise RuntimeError("Cannot reverse this migration. 'Topic.last_updater' and its values cannot be restored.")
        # Adding field 'Topic.summary'
        db.add_column(u'main_topic', 'summary',
                      self.gf('editorsnotes.main.fields.XHTMLField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Topic.has_accepted_facts'
        db.add_column(u'main_topic', 'has_accepted_facts',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Topic.created'
        raise RuntimeError("Cannot reverse this migration. 'Topic.created' and its values cannot be restored.")
        # Adding field 'Topic.has_candidate_facts'
        db.add_column(u'main_topic', 'has_candidate_facts',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Topic.type'
        db.add_column(u'main_topic', 'type',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=3, blank=True),
                      keep_default=False)

        # Deleting field 'Topic.merged_into'
        db.delete_column(u'main_topic', 'merged_into_id')

        # Adding M2M table for field related_topics on 'Topic'
        db.create_table(u'main_topic_related_topics', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_topic', models.ForeignKey(orm['main.topic'], null=False)),
            ('to_topic', models.ForeignKey(orm['main.topic'], null=False))
        ))
        db.create_unique(u'main_topic_related_topics', ['from_topic_id', 'to_topic_id'])

        # Adding M2M table for field affiliated_projects on 'Topic'
        db.create_table(u'main_topic_affiliated_projects', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('topic', models.ForeignKey(orm['main.topic'], null=False)),
            ('project', models.ForeignKey(orm['main.project'], null=False))
        ))
        db.create_unique(u'main_topic_affiliated_projects', ['topic_id', 'project_id'])


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.citation': {
            'Meta': {'ordering': "['ordering']", 'object_name': 'Citation'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_citation_set'", 'to': u"orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'citations'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_citation_set'", 'to': u"orm['auth.User']"}),
            'notes': ('editorsnotes.main.fields.XHTMLField', [], {'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'main.citationns': {
            'Meta': {'ordering': "['ordering', 'note_section_id']", 'object_name': 'CitationNS', '_ormbases': ['main.NoteSection']},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {'null': 'True', 'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Document']"}),
            u'notesection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.NoteSection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'main.document': {
            'Meta': {'ordering': "['ordering', 'import_id']", 'object_name': 'Document'},
            'affiliated_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['main.Project']", 'null': 'True', 'blank': 'True'}),
            'collection': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parts'", 'null': 'True', 'to': "orm['main.Document']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_document_set'", 'to': u"orm['auth.User']"}),
            'description': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'edtf_date': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'English'", 'max_length': '32'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_document_set'", 'to': u"orm['auth.User']"}),
            'ordering': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'main.documentlink': {
            'Meta': {'object_name': 'DocumentLink'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_documentlink_set'", 'to': u"orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'main.documentmetadata': {
            'Meta': {'unique_together': "(('document', 'key'),)", 'object_name': 'DocumentMetadata'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_documentmetadata_set'", 'to': u"orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metadata'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.featureditem': {
            'Meta': {'object_name': 'FeaturedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_featureditem_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"})
        },
        'main.footnote': {
            'Meta': {'object_name': 'Footnote'},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_footnote_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_footnote_set'", 'to': u"orm['auth.User']"}),
            'transcript': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'footnotes'", 'to': "orm['main.Transcript']"})
        },
        'main.note': {
            'Meta': {'ordering': "['-last_updated']", 'object_name': 'Note'},
            'affiliated_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['main.Project']", 'null': 'True', 'blank': 'True'}),
            'assigned_users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['main.UserProfile']", 'null': 'True', 'blank': 'True'}),
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_note_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_note_set'", 'to': u"orm['auth.User']"}),
            'sections_counter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'80'"})
        },
        'main.notereferencens': {
            'Meta': {'ordering': "['ordering', 'note_section_id']", 'object_name': 'NoteReferenceNS', '_ormbases': ['main.NoteSection']},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {'null': 'True', 'blank': 'True'}),
            'note_reference': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Note']"}),
            u'notesection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.NoteSection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'main.notesection': {
            'Meta': {'ordering': "['ordering', 'note_section_id']", 'unique_together': "(['note', 'note_section_id'],)", 'object_name': 'NoteSection'},
            '_section_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_notesection_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_notesection_set'", 'to': u"orm['auth.User']"}),
            'note': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sections'", 'to': "orm['main.Note']"}),
            'note_section_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ordering': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'main.project': {
            'Meta': {'object_name': 'Project'},
            'description': ('editorsnotes.main.fields.XHTMLField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'80'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'main.projectinvitation': {
            'Meta': {'object_name': 'ProjectInvitation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_projectinvitation_set'", 'to': u"orm['auth.User']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'role': ('django.db.models.fields.CharField', [], {'default': "'researcher'", 'max_length': '10'})
        },
        'main.scan': {
            'Meta': {'ordering': "['ordering']", 'object_name': 'Scan'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_scan_set'", 'to': u"orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scans'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'main.textns': {
            'Meta': {'ordering': "['ordering', 'note_section_id']", 'object_name': 'TextNS', '_ormbases': ['main.NoteSection']},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            u'notesection_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['main.NoteSection']", 'unique': 'True', 'primary_key': 'True'})
        },
        'main.topic': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Topic'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merged_into': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.TopicNode']", 'null': 'True', 'blank': 'True'}),
            'preferred_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'80'"}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'80'", 'db_index': 'True'})
        },
        'main.topicname': {
            'Meta': {'unique_together': "(('project', 'topic', 'is_preferred'),)", 'object_name': 'TopicName'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicname_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_preferred': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'200'"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['main.TopicNode']"})
        },
        'main.topicnode': {
            'Meta': {'object_name': 'TopicNode'},
            '_preferred_name': ('django.db.models.fields.CharField', [], {'max_length': "'200'"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicnode_set'", 'to': u"orm['auth.User']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topicnode_set'", 'to': u"orm['auth.User']"}),
            'merged_into': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.TopicNode']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'})
        },
        'main.topicnodeassignment': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'topic', 'project'),)", 'object_name': 'TopicNodeAssignment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicnodeassignment_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['main.TopicNode']"}),
            'topic_name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.TopicName']", 'null': 'True', 'blank': 'True'})
        },
        'main.topicsummary': {
            'Meta': {'unique_together': "(('project', 'topic'),)", 'object_name': 'TopicSummary'},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicsummary_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topicsummary_set'", 'to': u"orm['auth.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'summaries'", 'to': "orm['main.TopicNode']"})
        },
        'main.transcript': {
            'Meta': {'object_name': 'Transcript'},
            'affiliated_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['main.Project']", 'null': 'True', 'blank': 'True'}),
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_transcript_set'", 'to': u"orm['auth.User']"}),
            'document': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'_transcript'", 'unique': 'True', 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_transcript_set'", 'to': u"orm['auth.User']"})
        },
        'main.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'affiliation': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'members'", 'null': 'True', 'to': "orm['main.Project']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'zotero_key': ('django.db.models.fields.CharField', [], {'max_length': "'24'", 'null': 'True', 'blank': 'True'}),
            'zotero_uid': ('django.db.models.fields.CharField', [], {'max_length': "'6'", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['main']
