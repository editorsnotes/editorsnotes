# -*- coding: utf-8 -*-
import datetime
import json
import re
from lxml import etree
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.contrib.contenttypes.management import update_contenttypes

update_contenttypes(models.get_app('main'), models.get_models())

################

TIME_FMT = '%Y-%m-%d %H:%M:%S'

tmap = {}
assignmentmap = {}

cts = {}
def content_type_for_model(model, orm):
    app, model_name = model.split('.')
    if not model in cts:
        cts[model] = orm['contenttypes.contenttype'].objects.get(
            app_label=app, model=model_name)
    return cts[model]

users = {}
def user_for_uid(user_id, orm):
    if not user_id in users:
        qs = orm['auth.user'].objects.filter(id=user_id)
        user = qs.get() if qs.exists() else None
        users[user_id] = user
    return users[user_id]

affiliation_memo = {}
def affiliation_for_user(user, orm):
    if not user in affiliation_memo:
        profile = orm['main.userprofile'].objects.get(user_id=user.pk)
        qs = orm['main.project'].objects.select_related()\
                .filter(members=profile)
        affiliation = qs.get() if qs.exists() else None
        affiliation_memo[user] = affiliation
    return affiliation_memo[user]

def revisions_for(model, object_id, orm):
    return orm['reversion.version'].objects\
        .select_related('revision__user')\
        .filter(content_type=content_type_for_model(model, orm),
                object_id=object_id)\
        .order_by('revision__date_created')

fields_defaults = {}
def turn_off_auto_now(model, field_name, orm):
    field, = filter(lambda f: f.name == field_name,
                    orm[model]._meta.fields)
    fields_defaults[(model, field_name)] = {
        'auto_now': field.auto_now,
        'auto_now_add': field.auto_now_add
    }
    field.auto_now = False
    field.auto_now_add = False
    return

def restore_auto_now(orm):
    for model, field_name in fields_defaults:
        field, = filter(lambda f: f.name == field_name,
                        orm[model]._meta.fields)
        settings = fields_defaults[(model, field_name)]
        field.auto_now = settings['auto_now']
        field.auto_now_add = settings['auto_now_add']
    return

################

def create_topic_node(topic, orm):
    topic_node = orm['main.topicnode'].objects.create(
        _preferred_name=topic.preferred_name,
        type=topic.type,
        creator=topic.creator,
        created=topic.created,
        last_updater=topic.last_updater,
        last_updated=topic.last_updated
    )
    revision_comments = u'(Automatically generated in data migration on 5/2/2013) '
    revision_comments += u'TopicNode(pk={})'.format(topic_node.pk)
    revision = orm['reversion.revision'].objects.create(
        user_id=topic.creator_id,
        date_created=topic.created,
        comment=revision_comments
    )
    orm['reversion.version'].objects.create(
        type=0,
        format='json',
        object_repr=u'TopicNode: '.format(topic_node._preferred_name),
        revision_id=revision.id,
        content_type=content_type_for_model('main.topicnode', orm),
        object_id=unicode(topic_node.id),
        object_id_int=topic_node.id,
        serialized_data=json.dumps([{
            u'pk': topic_node.id,
            u'model': u'main.topicnode',
            u'fields': {
                u'_preferred_name': topic_node._preferred_name,
                u'creator': topic_node.creator_id,
                u'created': topic_node.created.strftime(TIME_FMT),
                u'last_updater': topic_node.creator_id,
                u'last_updated': topic_node.created.strftime(TIME_FMT)
            }
        }])
    )
    return topic_node

def update_topic(topic, topic_node, orm):

    topic_versions = revisions_for('main.topic', topic.id, orm)

    # Create new topic names, summaries, and topic assignments for every project
    # that has ever edited this topic.
    project_name_models = {}
    project_summary_models = {}
    project_reltopic_models = {}

    prev_version_summary = None
    prev_reltopics = []

    final_summary_length = len(etree.tostring(topic.summary)) \
            if topic.summary is not None else 0
    final_summary_cites = [
        c.id for c in 
        orm['main.citation'].objects.filter(
            content_type=content_type_for_model('main.topic', orm),
            object_id=topic.id)
    ]

    for version in topic_versions:

        # Get the user & affiliation for each revision. If the user does not
        # exist anymore of the user is not a member of a project, don't worry
        # about it.
        user = user_for_uid(version.revision.user_id, orm)
        project = user and affiliation_for_user(user, orm)
        if project is None or user is None: continue

        new_revision = orm['reversion.revision'].objects.create(
            user_id=version.revision.user_id,
            date_created=version.revision.date_created)
        revision_comments = u'(Automatically generated in data migration on 5/2/2013) '
        revision_comments += u'Project slug={} editing TopicNode pk={} -- '.format(
            project.slug, topic_node.id)

        # New version for the topic node with updated updater info
        orm['reversion.version'].objects.create(
            type=1,
            format='json',
            object_repr=u'TopicNode: {}'.format(topic_node._preferred_name),
            revision_id=new_revision.id,
            content_type=content_type_for_model('main.topicnode', orm),
            object_id=unicode(topic_node.id),
            object_id_int=topic_node.id,
            serialized_data=json.dumps([{
                u'pk': topic_node.id,
                u'model': u'main.topicnode',
                u'fields': {
                    u'_preferred_name': topic_node._preferred_name,
                    u'creator': topic_node.creator_id,
                    u'created': topic_node.created.strftime(TIME_FMT),
                    u'last_updater': version.revision.user_id,
                    u'last_updated': version.revision.date_created.strftime(TIME_FMT)
                }
            }])
        )
        revision_comments += 'Topic node updated'

        # Pull out the serialized data & take the values we need to inspect
        version_data = json.loads(version.serialized_data)
        version_reltopics = version_data[0]['fields'].pop('related_topics')
        version_summary = version_data[0]['fields'].pop('summary')
        version_summary = version_summary and re.sub('&#13;\n', ' ', version_summary)
        if version_summary and version_summary.strip().rstrip() == '<br/>':
            version_summary = None
        if version_summary and topic.summary is not None and (
            len(version_summary) < 20 and 
            float(len(version_summary)) / final_summary_length < .05):
            version_summary = None

        # Create a project name if does not exist yet and add it to the
        # revision. For simplicity's sake (lol), we'll only create a name for
        # the latest name of the topic in question-- the alternative making a
        # new topic name each time the Topic's preferred name changed. That's
        # not very useful, and also it's way too nice out to worry about that.
        if project not in project_name_models:
            project_name_models[project] = _name = orm['main.topicname'].objects.create(
                name=topic_node._preferred_name,
                topic=topic_node,
                project=project,
                creator=user,
                created=version.revision.date_created
            )
            serialized_data = {
                u'pk': _name.id,
                u'model': u'main.topicname',
                u'fields': {
                    u'name': _name.name,
                    u'topic': _name.topic_id,
                    u'project': _name.project_id,
                    u'is_preferred': _name.is_preferred,
                    u'creator': _name.creator_id,
                    u'created': _name.created.strftime(TIME_FMT)
                }
            }
            orm['reversion.version'].objects.create(
                type=0,
                format=u'json',
                object_repr=u'TopicName: {}'.format(_name.name),
                revision_id=new_revision.id,
                content_type=content_type_for_model('main.topicname', orm),
                object_id=unicode(_name.id),
                object_id_int=_name.id,
                serialized_data=json.dumps([serialized_data]))
            revision_comments += ', topic name created'
        
        # Create a summary for this topic, using the same basic method as the
        # names above. This will probably have to be cleaned up by hand later.
        SUMMARY_CREATED = False
        SUMMARY_CHANGED = version_summary and version_summary != prev_version_summary
        SUMMARY_CITES = version.revision.version_set.filter(
            content_type=content_type_for_model('main.citation', orm),
            object_id_int__in=final_summary_cites)
        HAS_SUMMARY_CITES = SUMMARY_CITES.exists()
        CONCERNS_SUMMARY = topic.summary is not None and (HAS_SUMMARY_CITES or SUMMARY_CHANGED)
        if CONCERNS_SUMMARY and project not in project_summary_models:
            project_summary_models[project] = orm['main.topicsummary'](
                project=project,
                creator=user,
                created=version.revision.date_created,
                topic=topic_node,
                content=topic.summary)
            SUMMARY_CREATED = True
        if CONCERNS_SUMMARY:
            summary = project_summary_models[project]
            summary.last_updater = user
            summary.last_updated = version.revision.date_created
            summary.save()
            serialized_data = {
                u'pk': summary.id,
                u'model': u'main.topicsummary',
                u'fields': {
                    u'topic': summary.topic_id,
                    u'project': summary.project_id,
                    u'content': version_summary,
                    u'creator': summary.creator_id,
                    u'created': summary.created.strftime(TIME_FMT),
                    u'last_updater': version.revision.user_id,
                    u'last_updated': version.revision.date_created.strftime(TIME_FMT)
                }
            }
            orm['reversion.version'].objects.create(
                type=0 if SUMMARY_CREATED else 1,
                format=u'json',
                object_repr=u'TopicSummary: {} for {}'.format(
                    project.slug, topic_node._preferred_name),
                revision_id=new_revision.id,
                content_type=content_type_for_model('main.topicsummary', orm),
                object_id=unicode(summary.id),
                object_id_int=summary.id,
                serialized_data=json.dumps([serialized_data]))
            revision_comments += ', topic summary {}ed'.format(
                'creat' if SUMMARY_CREATED else 'updat')
            prev_version_summary = version_summary

        # Work with the summary citations
        citation_versions = version.revision.version_set.filter(
            content_type=content_type_for_model('main.citation', orm),
            object_id_int__in=final_summary_cites)
        for cite_version in citation_versions:
            if not project in project_summary_models: continue
            cite_data = json.loads(cite_version.serialized_data)
            cite_data[0]['fields']['content_type'] = \
                    content_type_for_model('main.topicsummary', orm).id
            cite_data[0]['fields']['object_id'] = \
                    project_summary_models[project].id
            cite_data[0]['fields'].pop('locator', None)
            cite_data[0]['fields'].pop('type', None)
            cite_data[0]['fields'].setdefault('ordering', None)
            if 'source' in cite_data[0]['fields']:
                cite_data[0]['fields']['document'] = cite_data[0]['fields'].pop('source')
            cite_version.serialized_data = json.dumps(cite_data)
            cite_version.revision_id = new_revision.id
            cite_version.save()

            cite_qs = orm['main.citation'].objects.filter(
                content_type=content_type_for_model('main.topicsummary', orm),
                object_id=project_summary_models[project].id)
            existing_cite = orm['main.citation'].objects.get(
                id=cite_version.object_id)
            if not cite_qs.exists():
                cite = orm['main.citation'](
                    content_type=content_type_for_model('main.topicsummary', orm),
                    object_id=project_summary_models[project].id,
                    document_id=existing_cite.document_id,
                    notes=existing_cite.notes,
                    created=version.revision.date_created,
                    creator_id=user.id)
            else:
                cite = cite_qs.get()
            cite.last_updater_id = user.id
            cite.last_updated = version.revision.date_created
            cite.save()
        if citation_versions.exists():
            revision_comments += ', topic summary citations changed'

        # Work with the related_topics
        reltopic_difference = [t for t in version_reltopics
                               if t not in prev_reltopics]
        for topic_id in reltopic_difference:
            prev_reltopics.append(topic)
            reltopic = orm['main.topic'].objects.filter(id=topic_id)
            if not reltopic.exists(): continue
            reltopic = reltopic.get()
            if not reltopic in tmap: continue
            reltopicnode = tmap[reltopic]
            qs = orm['main.topicnodeassignment'].objects.filter(
                content_type_id=content_type_for_model('main.topicnode', orm),
                object_id=reltopicnode.id,
                topic_id=topic_node.id,
                project_id=project.id)
            if qs.exists(): continue
            assignment = orm['main.topicnodeassignment'].objects.create(
                creator_id=version.revision.user_id,
                created=version.revision.date_created,
                topic_id=topic_node.id,
                project_id=project.id,
                content_type=content_type_for_model('main.topicnode', orm),
                object_id=reltopicnode.id
            )
            orm['reversion.version'].objects.create(
                type=0,
                format=u'json',
                object_repr=u'TopicNodeAssignment: {} for {}'.format(
                    project.slug, topic_node._preferred_name),
                revision_id=new_revision.id,
                content_type=content_type_for_model('main.topicnodeassignment', orm),
                object_id=unicode(assignment.id),
                object_id_int=assignment.id,
                serialized_data = json.dumps([{
                    u'model': u'main.topicnodeassignment',
                    u'pk': assignment.id,
                    u'fields': {
                        u'topic': topic_node.id,
                        u'project': project.id,
                        u'content_type': content_type_for_model('main.topicnode', orm).id,
                        u'object_id': reltopicnode.id
                    }
                }])
            )
            revision_comments += u', topic assignment to {} added'.format(
                reltopicnode._preferred_name)

        # Work with aliases
        alias_versions = version.revision.version_set.filter(
            content_type=content_type_for_model('main.alias', orm))
        for alias_version in alias_versions:
            alias = orm['main.alias'].objects.filter(id=alias_version.id)
            if not alias.exists(): continue
            alias = alias.get()
            if not alias.topic in tmap: continue
            _name = orm['main.topicname'].objects.create(
                name=alias.name,
                created=version.revision.date_created,
                creator=version.revision.user_id,
                topic_id=topic_node.id,
                project_id=project.id,
                is_preferred=False)
            serialized_data = {
                u'pk': _name.id,
                u'model': u'main.topicname',
                u'fields': {
                    u'name': _name.name,
                    u'topic': _name.topic_id,
                    u'project': _name.project_id,
                    u'is_preferred': _name.is_preferred,
                    u'creator': _name.creator_id,
                    u'created': _name.created.strftime(TIME_FMT)
                }
            }
            orm['reversion.version'].objects.create(
                type=0,
                format=u'json',
                object_repr=u'TopicName: {}'.format(_name.name),
                revision_id=new_revision.id,
                content_type=content_type_for_model('main.topicname', orm),
                object_id=unicode(_name.id),
                object_id_int=_name.id,
                serialized_data=json.dumps([serialized_data]))
            alias_version.delete()
            revision_comments += u', additional name {} added'.format(_name.name)

        new_revision.comment = revision_comments
        new_revision.save()

        version.revision.delete() # yeah?

class Migration(DataMigration):

    def forwards(self, orm):

        turn_off_auto_now('reversion.revision', 'date_created', orm)
        turn_off_auto_now('main.topicnode', 'created', orm)
        turn_off_auto_now('main.topicnode', 'last_updated', orm)
        turn_off_auto_now('main.topicsummary', 'created', orm)
        turn_off_auto_now('main.topicsummary', 'last_updated', orm)
        turn_off_auto_now('main.citation', 'created', orm)
        turn_off_auto_now('main.citation', 'last_updated', orm)
        turn_off_auto_now('main.topicname', 'created', orm)
        turn_off_auto_now('main.topicassignment', 'created', orm)
        turn_off_auto_now('main.topicnodeassignment', 'created', orm)

        # Create topic nodes for every topic
        for topic in orm['main.topic'].objects.order_by('id'):
            tmap[topic] = create_topic_node(topic, orm)

        # Update all the topics
        for topic in orm['main.topic'].objects.order_by('id').all():
            update_topic(topic, tmap[topic], orm)

        # Update all the topic assignments
        for ta in orm['main.topicassignment'].objects.all():
            user = user_for_uid(ta.creator_id, orm)
            project = user and affiliation_for_user(user, orm)
            if user is None or project is None:
                continue
            new_ta = orm['main.topicnodeassignment'].objects.create(
                topic=tmap[ta.topic],
                project=project,
                content_type_id=ta.content_type_id,
                object_id=ta.object_id,
                creator_id=ta.creator_id,
                created=ta.created
            )
            for version in revisions_for('main.topicassignment', ta.id, orm):
                data = json.loads(version.serialized_data)
                data[0]['pk'] = new_ta.id
                data[0]['model'] = 'main.topicnodeassignment'
                data[0]['fields']['topic'] = new_ta.topic_id
                data[0]['fields']['project'] = new_ta.project_id
                data[0]['fields']['topic_name'] = None

                version.content_type = \
                        content_type_for_model('main.topicnodeassignment', orm)
                version.object_id = unicode(new_ta.id)
                version.object_id_int = new_ta.id
                version.serialized_data = json.dumps(data)
                version.save()
            ta.delete()

        # Update any featured topics to point to the new topic node
        featured_topics = orm['main.featureditem'].objects.filter(
            content_type=content_type_for_model('main.topic', orm))
        for featured_item in featured_topics:
            old_topic = orm['main.topic'].objects.get(id=featured_item.object_id)
            featured_item.content_type = content_type_for_model('main.topicnode', orm)
            featured_item.object_id = tmap[old_topic].id
            featured_item.save()

        # Delete old citations
        for topic in orm['main.topic'].objects.all():
            citations = orm['main.citation'].objects.filter(
                content_type=content_type_for_model('main.topic', orm),
                object_id=topic.id)
            for citation in citations:
                citation.delete()

        restore_auto_now(orm)

    def backwards(self, orm):
        "Write your backwards methods here." # hahaha fuck off NO

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
        'main.alias': {
            'Meta': {'unique_together': "(('topic', 'name'),)", 'object_name': 'Alias'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_alias_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'80'"}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'aliases'", 'to': "orm['main.Topic']"})
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
            'affiliated_projects': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['main.Project']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topic_set'", 'to': u"orm['auth.User']"}),
            'has_accepted_facts': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_candidate_facts': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topic_set'", 'to': u"orm['auth.User']"}),
            'preferred_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'80'"}),
            'related_topics': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_topics_rel_+'", 'blank': 'True', 'to': "orm['main.Topic']"}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': "'80'", 'db_index': 'True'}),
            'summary': ('editorsnotes.main.fields.XHTMLField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'})
        },
        'main.topicassignment': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'topic'),)", 'object_name': 'TopicAssignment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicassignment_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['main.Topic']"})
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
        },
        u'reversion.revision': {
            'Meta': {'object_name': 'Revision'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manager_slug': ('django.db.models.fields.CharField', [], {'default': "u'default'", 'max_length': '200', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
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
