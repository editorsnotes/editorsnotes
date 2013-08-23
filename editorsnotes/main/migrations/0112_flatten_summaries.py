# -*- coding: utf-8 -*-
import datetime
import json
from south.db import db
from south.v2 import DataMigration
from django.db import models
from lxml import etree

class Migration(DataMigration):

    def forwards(self, orm):
        container_ct = orm['contenttypes.contenttype'].objects\
                .get(app_label='main', model='projecttopiccontainer')
        summary_ct = orm['contenttypes.contenttype'].objects\
                .get(app_label='main', model='topicsummary')

        topics = orm['main.projecttopiccontainer'].objects\
                .values_list('id', flat=True)

        base_select = (
            u'SELECT v.id, v.serialized_data, r.id, r.date_created '
            'FROM reversion_version as v '
            'LEFT OUTER JOIN reversion_revision AS r '
            'ON r.id = v.revision_id '
            'WHERE content_type_id = %s AND object_id_int = %s;')

        base_update = (
            u'UPDATE reversion_version SET serialized_data = %s '
            'WHERE id = %s;')

        for topic in orm['main.projecttopiccontainer'].objects.all():
            prev_summary = None
            has_summary = hasattr(topic, 'old_summary') \
                    and topic.old_summary.content is not None

            container_version = db.execute(
                base_select, params=[container_ct.id, topic.id])

            if not container_version:
                continue
            else:
                container_version = container_version[0]

            t_vid, t_data, t_rid, t_created = container_version
            data = json.loads(t_data)

            if not has_summary:
                data[0]['fields']['summary'] = None
                db.execute(base_update, params=[json.dumps(data), t_vid])
                if hasattr(topic, 'old_summary'):
                    db.execute(
                        u'DELETE FROM reversion_version '
                        'WHERE content_type_id = %s and object_id_int = %s;',
                        params=[summary_ct.id, topic.old_summary.id])
                continue

            db.execute(
                u'UPDATE main_projecttopiccontainer '
                'SET summary = %s '
                'WHERE id = %s;',
                params=[etree.tostring(topic.old_summary.content), topic.id])

            summary_versions = db.execute(
                base_select, params=[summary_ct.id, topic.old_summary.id])

            for s_vid, s_data, s_rid, s_vcreated in summary_versions:
                summary_data = json.loads(s_data)
                summary_text = summary_data[0]['fields']['content']
                data[0]['fields']['summary'] = summary_text
                if s_rid == t_rid:
                    db.execute(base_update, params=[json.dumps(data), t_vid])
                    db.execute('DELETE FROM reversion_version WHERE id = %s',
                               params=[s_vid])
                else:
                    data[0]['fields']['last_updated'] = \
                            summary_data[0]['fields']['last_updated']
                    data[0]['fields']['last_updater'] = \
                            summary_data[0]['fields']['last_updater']
                    db.execute(
                        u'UPDATE reversion_version '
                        'SET object_id = %s, object_id_int = %s, '
                            'content_type_id = %s, serialized_data = %s, '
                            'object_repr = %s, type = 1 '
                        'WHERE id = %s;',
                        params = [
                            str(topic.id), topic.id, container_ct.id,
                            json.dumps(data),
                            u'ProjectTopicContainer {} ({})'.format(topic.preferred_name, topic.project.slug),
                            s_vid])

    def backwards(self, orm):
        "Write your backwards methods here."

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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.alternatename': {
            'Meta': {'unique_together': "(('container', 'name'),)", 'object_name': 'AlternateName'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'alternate_names'", 'to': "orm['main.ProjectTopicContainer']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_alternatename_set'", 'to': "orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'main.citation': {
            'Meta': {'ordering': "['ordering']", 'object_name': 'Citation'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_citation_set'", 'to': "orm['main.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'citations'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_citation_set'", 'to': "orm['main.User']"}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_document_set'", 'to': "orm['main.User']"}),
            'description': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'edtf_date': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'English'", 'max_length': '32'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_document_set'", 'to': "orm['main.User']"}),
            'ordering': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'documents'", 'to': "orm['main.Project']"})
        },
        'main.documentlink': {
            'Meta': {'object_name': 'DocumentLink'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_documentlink_set'", 'to': "orm['main.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'main.documentmetadata': {
            'Meta': {'unique_together': "(('document', 'key'),)", 'object_name': 'DocumentMetadata'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_documentmetadata_set'", 'to': "orm['main.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'metadata'", 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'main.featureditem': {
            'Meta': {'object_name': 'FeaturedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_featureditem_set'", 'to': "orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"})
        },
        'main.footnote': {
            'Meta': {'object_name': 'Footnote'},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_footnote_set'", 'to': "orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_footnote_set'", 'to': "orm['main.User']"}),
            'transcript': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'footnotes'", 'to': "orm['main.Transcript']"})
        },
        'main.note': {
            'Meta': {'ordering': "['-last_updated']", 'object_name': 'Note'},
            'assigned_users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['main.User']", 'null': 'True', 'blank': 'True'}),
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_note_set'", 'to': "orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_note_set'", 'to': "orm['main.User']"}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_notesection_set'", 'to': "orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_notesection_set'", 'to': "orm['main.User']"}),
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
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_projectinvitation_set'", 'to': "orm['main.User']"}),
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
        'main.projecttopiccontainer': {
            'Meta': {'object_name': 'ProjectTopicContainer'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_projecttopiccontainer_set'", 'to': "orm['main.User']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_projecttopiccontainer_set'", 'to': "orm['main.User']"}),
            'merged_into': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ProjectTopicContainer']", 'null': 'True', 'blank': 'True'}),
            'preferred_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topic_containers'", 'to': "orm['main.Project']"}),
            'summary': ('editorsnotes.main.fields.XHTMLField', [], {'null': 'True', 'blank': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'project_containers'", 'to': "orm['main.TopicNode']"})
        },
        'main.scan': {
            'Meta': {'ordering': "['ordering']", 'object_name': 'Scan'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_scan_set'", 'to': "orm['main.User']"}),
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
        'main.topicnode': {
            'Meta': {'object_name': 'TopicNode'},
            '_preferred_name': ('django.db.models.fields.CharField', [], {'max_length': "'200'"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicnode_set'", 'to': "orm['main.User']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topicnode_set'", 'to': "orm['main.User']"}),
            'merged_into': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.TopicNode']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'})
        },
        'main.topicnodeassignment': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'container'),)", 'object_name': 'TopicNodeAssignment'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'assignments'", 'null': 'True', 'to': "orm['main.ProjectTopicContainer']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicnodeassignment_set'", 'to': "orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'main.topicsummary': {
            'Meta': {'object_name': 'TopicSummary'},
            'container': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'old_summary'", 'unique': 'True', 'null': 'True', 'to': "orm['main.ProjectTopicContainer']"}),
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicsummary_set'", 'to': "orm['main.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topicsummary_set'", 'to': "orm['main.User']"})
        },
        'main.transcript': {
            'Meta': {'object_name': 'Transcript'},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_transcript_set'", 'to': "orm['main.User']"}),
            'document': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'_transcript'", 'unique': 'True', 'to': "orm['main.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_transcript_set'", 'to': "orm['main.User']"})
        },
        'main.user': {
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
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'zotero_key': ('django.db.models.fields.CharField', [], {'max_length': "'24'", 'null': 'True', 'blank': 'True'}),
            'zotero_uid': ('django.db.models.fields.CharField', [], {'max_length': "'6'", 'null': 'True', 'blank': 'True'})
        },
        u'reversion.revision': {
            'Meta': {'object_name': 'Revision'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manager_slug': ('django.db.models.fields.CharField', [], {'default': "u'default'", 'max_length': '200', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.User']", 'null': 'True', 'blank': 'True'})
        },
        u'reversion.version': {
            'Meta': {'object_name': 'Version'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'format': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.TextField', [], {}),
            'object_id_int': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'object_repr': ('django.db.models.fields.TextField', [], {}),
            'revision': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['reversion.Revision']"}),
            'serialized_data': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['reversion', 'main']
    symmetrical = True
