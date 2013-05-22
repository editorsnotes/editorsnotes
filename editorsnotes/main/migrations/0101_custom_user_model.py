# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):
    needed_by = (
        ('reversion', '0001_initial'),
        ('authtoken', '0001_initial'),
    )

    def forwards(self, orm):
        "Write your forwards methods here."
        db.rename_table('auth_user', 'main_user')
        db.rename_table('auth_user_groups', 'main_user_groups')
        db.rename_table('auth_user_user_permissions', 'main_user_user_permissions')

        # Changing field 'DocumentLink.creator'
        db.alter_column(u'main_documentlink', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Transcript.creator'
        db.alter_column(u'main_transcript', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Transcript.last_updater'
        db.alter_column(u'main_transcript', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Scan.creator'
        db.alter_column(u'main_scan', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'DocumentMetadata.creator'
        db.alter_column(u'main_documentmetadata', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'ProjectInvitation.creator'
        db.alter_column(u'main_projectinvitation', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'NoteSection.creator'
        db.alter_column(u'main_notesection', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'NoteSection.last_updater'
        db.alter_column(u'main_notesection', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'TopicSummary.creator'
        db.alter_column(u'main_topicsummary', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'TopicSummary.last_updater'
        db.alter_column(u'main_topicsummary', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'TopicNode.creator'
        db.alter_column(u'main_topicnode', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'TopicNode.last_updater'
        db.alter_column(u'main_topicnode', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'UserProfile.user'
        db.alter_column(u'main_userprofile', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User'], unique=True))

        # Changing field 'Footnote.creator'
        db.alter_column(u'main_footnote', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Footnote.last_updater'
        db.alter_column(u'main_footnote', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Note.last_updater'
        db.alter_column(u'main_note', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Note.creator'
        db.alter_column(u'main_note', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Citation.creator'
        db.alter_column(u'main_citation', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Citation.last_updater'
        db.alter_column(u'main_citation', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'FeaturedItem.creator'
        db.alter_column(u'main_featureditem', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'TopicNodeAssignment.creator'
        db.alter_column(u'main_topicnodeassignment', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Document.creator'
        db.alter_column(u'main_document', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'Document.last_updater'
        db.alter_column(u'main_document', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))

        # Changing field 'TopicName.creator'
        db.alter_column(u'main_topicname', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.User']))


    def backwards(self, orm):
        "Write your backwards methods here."
        db.rename_table('main_user', 'auth_user')
        db.rename_table('main_user_groups', 'auth_user_groups')
        db.rename_table('main_user_user_permissions', 'auth_user_user_permissions')

        # Changing field 'DocumentLink.creator'
        db.alter_column(u'main_documentlink', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Transcript.creator'
        db.alter_column(u'main_transcript', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Transcript.last_updater'
        db.alter_column(u'main_transcript', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Scan.creator'
        db.alter_column(u'main_scan', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'DocumentMetadata.creator'
        db.alter_column(u'main_documentmetadata', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'ProjectInvitation.creator'
        db.alter_column(u'main_projectinvitation', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'NoteSection.creator'
        db.alter_column(u'main_notesection', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'NoteSection.last_updater'
        db.alter_column(u'main_notesection', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'TopicSummary.creator'
        db.alter_column(u'main_topicsummary', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'TopicSummary.last_updater'
        db.alter_column(u'main_topicsummary', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'TopicNode.creator'
        db.alter_column(u'main_topicnode', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'TopicNode.last_updater'
        db.alter_column(u'main_topicnode', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'UserProfile.user'
        db.alter_column(u'main_userprofile', 'user_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True))

        # Changing field 'Footnote.creator'
        db.alter_column(u'main_footnote', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Footnote.last_updater'
        db.alter_column(u'main_footnote', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Note.last_updater'
        db.alter_column(u'main_note', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Note.creator'
        db.alter_column(u'main_note', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Citation.creator'
        db.alter_column(u'main_citation', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Citation.last_updater'
        db.alter_column(u'main_citation', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'FeaturedItem.creator'
        db.alter_column(u'main_featureditem', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'TopicNodeAssignment.creator'
        db.alter_column(u'main_topicnodeassignment', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Document.creator'
        db.alter_column(u'main_document', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'Document.last_updater'
        db.alter_column(u'main_document', 'last_updater_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

        # Changing field 'TopicName.creator'
        db.alter_column(u'main_topicname', 'creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User']))

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
        u'main.user': {
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_citation_set'", 'to': u"orm['main.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'citations'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_citation_set'", 'to': u"orm['main.User']"}),
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
            'collection': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parts'", 'null': 'True', 'to': "orm['main.Document']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_document_set'", 'to': u"orm['main.User']"}),
            'description': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'edtf_date': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'English'", 'max_length': '32'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_document_set'", 'to': u"orm['main.User']"}),
            'ordering': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documents'", 'to': "orm['main.Project']"})
        },
        'main.documentlink': {
            'Meta': {'object_name': 'DocumentLink'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_documentlink_set'", 'to': u"orm['main.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'main.documentmetadata': {
            'Meta': {'unique_together': "(('document', 'key'),)", 'object_name': 'DocumentMetadata'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_documentmetadata_set'", 'to': u"orm['main.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metadata'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.featureditem': {
            'Meta': {'object_name': 'FeaturedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_featureditem_set'", 'to': u"orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"})
        },
        'main.footnote': {
            'Meta': {'object_name': 'Footnote'},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_footnote_set'", 'to': u"orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_footnote_set'", 'to': u"orm['main.User']"}),
            'transcript': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'footnotes'", 'to': "orm['main.Transcript']"})
        },
        'main.note': {
            'Meta': {'ordering': "['-last_updated']", 'object_name': 'Note'},
            'assigned_users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['main.UserProfile']", 'null': 'True', 'blank': 'True'}),
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_note_set'", 'to': u"orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_note_set'", 'to': u"orm['main.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notes'", 'to': "orm['main.Project']"}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_notesection_set'", 'to': u"orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_notesection_set'", 'to': u"orm['main.User']"}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_projectinvitation_set'", 'to': u"orm['main.User']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'main.projectrole': {
            'Meta': {'unique_together': "(('project', 'role'),)", 'object_name': 'ProjectRole'},
            'group': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.Group']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_super_role': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'roles'", 'to': "orm['main.Project']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        'main.scan': {
            'Meta': {'ordering': "['ordering']", 'object_name': 'Scan'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_scan_set'", 'to': u"orm['main.User']"}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicname_set'", 'to': u"orm['main.User']"}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicnode_set'", 'to': u"orm['main.User']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topicnode_set'", 'to': u"orm['main.User']"}),
            'merged_into': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.TopicNode']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'})
        },
        'main.topicnodeassignment': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'topic', 'project'),)", 'object_name': 'TopicNodeAssignment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicnodeassignment_set'", 'to': u"orm['main.User']"}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicsummary_set'", 'to': u"orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topicsummary_set'", 'to': u"orm['main.User']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'summaries'", 'to': "orm['main.TopicNode']"})
        },
        'main.transcript': {
            'Meta': {'object_name': 'Transcript'},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_transcript_set'", 'to': u"orm['main.User']"}),
            'document': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'_transcript'", 'unique': 'True', 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_transcript_set'", 'to': u"orm['main.User']"})
        },
        'main.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.User']", 'unique': 'True'}),
            'zotero_key': ('django.db.models.fields.CharField', [], {'max_length': "'24'", 'null': 'True', 'blank': 'True'}),
            'zotero_uid': ('django.db.models.fields.CharField', [], {'max_length': "'6'", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['main']
    symmetrical = True
