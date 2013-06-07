# -*- coding: utf-8 -*-
import datetime
import json
import hashlib
import re
from lxml import etree
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.contrib.contenttypes.management import update_contenttypes

update_contenttypes(models.get_app('main'), models.get_models())

TIME_FMT = '%Y-%m-%d %H:%M:%S'

tmap = {}
tmap_id = {}
container_creation = {}
assignmentmap = {}
stale_revisions = set()

##########################################
# Helper statements with no side effects #
##########################################
cts = {}
def ct_for_model(model, app_label='main'):
    if model not in cts:
        ct_select = db.execute(
            u'SELECT id FROM django_content_type '
            'WHERE app_label = %s AND model = %s;',
            params=[app_label, model])
        ct_id, = ct_select[0]
        cts[model] = ct_id
    return cts[model]

pid_memo = {}
def pid_for_uid(uid):
    if uid not in pid_memo:
        affiliation_select = db.execute(
            u'SELECT affiliation_id FROM main_userprofile WHERE user_id = %s;',
            params=[uid])
        pid = affiliation_select[0][0] if len(affiliation_select[0]) else None
        pid_memo[uid] = affiliation_select[0][0]
    return pid_memo[uid]

pslug_memo = {}
def pslug_for_pid(pid, orm):
    if pid not in pslug_memo:
        pslug_memo[pid] = orm['main.project'].objects.get(id=pid).slug
    return pslug_memo[pid]

def versions_for(model, object_id, orm):
    return orm['reversion.version'].objects\
        .select_related('revision__user')\
        .filter(content_type_id=ct_for_model(model), object_id=object_id)\
        .order_by('revision__date_created')

def clean_version_summary_str(string):
    if not string:
        return ''
    cleaned = re.sub('&#13;\n', ' ', string)
    cleaned = cleaned.strip().rstrip()
    if cleaned == '<br/>':
        cleaned = ''
    return cleaned

########################################
# Helper statements that change the db #
########################################

def fix_null_creator_revisions(orm):
    """
    Update the user_id for revisions without one if we can detect what it should
    be.
    """
    null_creator_revisions = orm['reversion.revision'].objects\
            .select_related('version')\
            .filter(user=None)
    for revision in null_creator_revisions:
        found_user_id = None
        last_updater_versions = revision.version_set\
                .filter(serialized_data__contains='last_updater')
        for version in last_updater_versions:
            data = json.loads(version.serialized_data)[0]
            found_user_id = data['fields'].get('last_updater', None)
            if found_user_id is not None:
                break
        if found_user_id is None:
            creator_versions = revision.version_set.filter(
                serialized_data__contains='creator')
            for version in creator_versions:
                data = json.loads(version.serialized_data)[0]
                found_user_id = data['fields'].get('creator', None)
                if found_user_id is not None:
                    break
        if found_user_id is not None:
            db.execute(
                u'UPDATE reversion_revision SET user_id = %s WHERE id = %s;',
                params=[found_user_id, revision.id])

def create_new_revision(user_id, timestamp, comment):
    revision_insert = db.execute(
        u'INSERT INTO reversion_revision VALUES '
        '(DEFAULT, %s, %s, %s, %s) '
        'RETURNING id;',
        params=[timestamp, user_id, comment, 'default'])
    revision_id, = revision_insert[0]
    return revision_id

def create_topic_node(topic):
    topic_node_insert = db.execute(
        u'INSERT INTO main_topicnode VALUES '
        '(DEFAULT, %s, %s, %s, %s, %s, %s, FALSE) '
        'RETURNING id;' ,
         params=[topic.creator_id, topic.created,
                 topic.last_updater_id, topic.last_updated,
                 topic.preferred_name, topic.type]
    )
    topic_node_id, = topic_node_insert[0]
    return topic_node_id

def get_or_create_project_container(topic, project_id, user_id, timestamp):
    topic_node_id = tmap[topic]
    container_select = db.execute(
        u'SELECT id, last_updated '
        'FROM main_projecttopiccontainer '
        'WHERE topic_id = %s AND project_id = %s;',
        params=[topic_node_id, project_id])
    if len(container_select) == 0:
        created = True
        container_insert = db.execute(
            u'INSERT INTO main_projecttopiccontainer '
            'VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, False) '
            'RETURNING id;',
            params=[user_id, timestamp, user_id, timestamp, project_id, topic_node_id])
        container_id, = container_insert[0]
        container_creation[(container_id, project_id)] = (user_id, timestamp)
        name_insert = db.execute(
            u'INSERT INTO main_topicname '
            'VALUES (DEFAULT, %s, %s, %s, %s, True) '
            'RETURNING id;',
            params=[user_id, timestamp, topic.preferred_name, container_id])
        created_topic_name_id, = name_insert[0]
    else:
        created = False
        created_topic_name_id = None
        container_id, last_updated = container_select[0]
        if timestamp > last_updated:
            db.execute(
                u'UPDATE main_projecttopiccontainer '
                'SET last_updated = %s, last_updater_id = %s '
                'WHERE id = %s',
                params=[timestamp, user_id, container_id])
    return container_id, created_topic_name_id

summaries = {}
def update_project_topic_summary(topic, container_id, summary_text, user_id,
                                 timestamp, force=False):
    """
    Returns topic summary id if anything was changed, otherwise None
    """
    created = False
    edited = False
    if container_id not in summaries:
        if force is False and not summary_text:
            return None, False, False
        else:
            created = True
            edited = True
            topic_summary_insert = db.execute(
                u'INSERT INTO main_topicsummary '
                'VALUES (DEFAULT, %s, %s, %s, %s, %s, %s) '
                'RETURNING id;',
                params=[user_id, timestamp, user_id, timestamp, container_id,
                        etree.tostring(topic.summary) if topic.summary is not None else '<br/>'])
            topic_summary_id, = topic_summary_insert[0]
    else:
        digest = hashlib.md5(summary_text).hexdigest()
        topic_summary_id = db.execute(
            u'SELECT id FROM main_topicsummary WHERE container_id = %s',
            params=[container_id])[0][0]
        if summaries[container_id] != digest:
            edited = True
            topic_summary_update = db.execute(
                u'UPDATE main_topicsummary '
                'SET last_updater_id = %s, last_updated = %s '
                'WHERE id = %s '
                'RETURNING id;',
                params=[user_id, timestamp, topic_summary_id])
            topic_summary_id, = topic_summary_update[0]

    summaries[container_id] = hashlib.md5(summary_text).hexdigest()
    return topic_summary_id, created, edited

def create_version(revision_id, object_id, model, fields, object_repr,
                   typ=1, fmt='json'):
    data = [{
        u'pk': int(object_id),
        u'model': 'main.{}'.format(model),
        u'fields': fields
    }]
    db.execute(
        u'INSERT INTO reversion_version '
        'VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s) ',
        params=[revision_id, str(object_id), ct_for_model(model),
                fmt, json.dumps(data), object_repr, typ, int(object_id)])
    return


############################

def update_topic(topic, orm):
    """
    Make database changes for a topic based on its information as well as the
    information contained in any of its stored versions.
    """
    topic_versions = versions_for('topic', topic.id, orm)

    # Get the topic node ID-- all topic nodes are created before this function
    # is ever called.
    topic_node_id = tmap[topic]

    # Store whether this topic has any citations. We will use that knowledge
    # later to decide whether to create new citations for TopicSummary objects.
    topic_cites_select = db.execute(
        u'SELECT id FROM main_citation '
        'WHERE content_type_id = %s AND object_id = %s;',
        params=[ct_for_model('topic'), topic.id])
    final_topic_cites = map(lambda rec: rec[0], topic_cites_select)

    # Do the same for topic assignments.
    reltopics_select = db.execute(
        u'SELECT id FROM main_topicassignment '
        'WHERE topic_id = %s;',
        params=[topic.id])
    final_reltopics = map(lambda rec: rec[0], reltopics_select)

    topicreltopics_select = db.execute(
        u'SELECT to_topic_id from main_topic_related_topics '
        'WHERE from_topic_id = %s;',
        params=[topic.id])
    final_topicreltopics = map(lambda rec: rec[0], topicreltopics_select)
    existing_topicreltopics = set()

    aliases_select = db.execute(
        u'SELECT id FROM main_alias '
        'WHERE topic_id = %s;',
        params=[topic.id])
    final_aliases = map(lambda rec: rec[0], aliases_select)
    existing_aliases = set()

    # We didn't create versions for topics that we batch imported, so we need to
    # handle them separately.
    if not topic_versions or topic.created < topic_versions[0].revision.date_created:
        project_id = pid_for_uid(topic.creator_id)
        container_id, topic_name_id = get_or_create_project_container(
            topic, project_id, topic.creator_id, topic.created)
        container_created = topic_name_id is not None

        revision_comment = (
            u'[Generated in data migration on {}] '
            'TopicContainer created for topic {} by project {}.'.format(
                datetime.datetime.now(), topic.preferred_name,
                pslug_for_pid(project_id, orm)))
        new_revision_id = create_new_revision(
            topic.creator_id, topic.created, revision_comment)

        container_creator, container_created_time = \
                container_creation[(container_id, project_id)]
        data = {}
        data['creator'] = data['last_updater'] = container_creator
        data['created'] = data['last_updated'] = container_created_time.strftime(TIME_FMT)
        data['topic'] = topic_node_id
        data['project'] = project_id
        data['preferred_name'] = topic.preferred_name
        create_version(
            new_revision_id, container_id, 'projecttopiccontainer', data,
            u'ProjectTopicContainer <project={}> <topic_id={}>'.format(
                project_id, topic_node_id), typ=0)

    # For items that do have version data, work from that.
    for version in topic_versions:

        version_dt = version.revision.date_created
        user_id = version.revision.user_id
        version_data = json.loads(version.serialized_data)

        # Get or create a project container for this topic. This will create a
        # TopicName if it does not exist for this project as well.
        project_id = pid_for_uid(user_id)
        container_id, topic_name_id = get_or_create_project_container(
            topic, project_id, user_id, version_dt)
        container_created = bool(topic_name_id)

        revision_comment = u'[Generated in data migration on {}]'.format(datetime.datetime.now())
        new_revision_id = create_new_revision(user_id, version_dt, revision_comment)

        if container_created:
            container_creator, container_created_time = \
                    container_creation[(container_id, project_id)]
            data = {}
            data['creator'] = data['last_updater'] = container_creator
            data['created'] = data['last_updated'] = container_created_time.strftime(TIME_FMT)
            data['topic'] = topic_node_id
            data['project'] = project_id
            data['preferred_name'] = topic.preferred_name
            create_version(
                new_revision_id, container_id, 'projecttopiccontainer', data,
                u'ProjectTopicContainer {} ({})'.format(
                    topic.preferred_name, pslug_for_pid(project_id, orm)), typ=0)

            revision_comment += u'Added project topic container "{} ({})". '.format(
                topic.preferred_name, pslug_for_pid(project_id, orm))

        summary_created = False
        summary_edited = False
        summary_id = None
        version_summary = clean_version_summary_str(
            version_data[0]['fields'].pop('summary', ''))

        if topic.summary is not None:
            summary_id, summary_created, summary_edited = update_project_topic_summary(
                topic, container_id, version_summary, user_id, version_dt)

        version_citations = version.revision.version_set.filter(
            content_type_id=ct_for_model('citation'),
            object_id_int__in=final_topic_cites)

        if version_citations.exists():
            if summary_id is None:
                summary_id, summary_created, summary_edited = update_project_topic_summary(
                    topic, container_id, version_summary, user_id, version_dt,
                    force=True)
            for citation in version_citations:
                db.execute(
                    u'UPDATE main_citation '
                    'SET content_type_id = %s, object_id = %s '
                    'WHERE id = %s;',
                    params=[ct_for_model('topicsummary'), summary_id,
                            citation.object_id])
                data = json.loads(citation.serialized_data)
                data[0]['fields']['content_type'] = ct_for_model('topicsummary')
                data[0]['fields']['object_id'] = summary_id
                citation.serialized_data = json.dumps(data)
                citation.revision_id = new_revision_id
                citation.save()
        if summary_edited or summary_created:
            create_version(
                new_revision_id, container_id, 'topicsummary', data,
                u'Summary for {} by {}.'.format(topic.preferred_name,
                                               pslug_for_pid(project_id, orm)),
                typ=0 if summary_created else 1)
            revision_comment += u'{}ed summary "Summary for {} by {}'.format(
                'Add' if summary_created else 'Edit',
                topic.preferred_name, pslug_for_pid(project_id, orm))

        reltopics_changed = False
        version_assignments = version.revision.version_set.filter(
            content_type_id=ct_for_model('topicassignment'),
            object_id_int__in=final_reltopics)

        if version_assignments.exists():
            for assignment in version_assignments:
                assignment_created = False

                data = json.loads(assignment.serialized_data)
                creator_id = data[0]['fields']['creator']
                created = datetime.datetime.strptime(
                    data[0]['fields']['created'], TIME_FMT)
                ct_id = data[0]['fields']['content_type']
                object_id = data[0]['fields']['object_id']

                assignment_select = db.execute(
                    u'SELECT id FROM main_topicnodeassignment '
                    'WHERE container_id = %s AND content_type_id = %s AND object_id = %s;',
                    params=[container_id, ct_id, object_id])
                if not len(assignment_select):
                    assignment_created = True
                    assignment_insert = db.execute(
                        u'INSERT INTO main_topicnodeassignment '
                        'VALUES (DEFAULT, %s, %s, %s, %s, %s, %s) '
                        'RETURNING id;',
                        params=[creator_id, created, container_id, None,
                                data[0]['fields']['content_type'],
                                data[0]['fields']['object_id']])
                    assignment_id, = assignment_insert[0]
                    fields = {
                        'creator': creator_id,
                        'created': created.strftime(TIME_FMT),
                        'container': container_id,
                        'topicname': None,
                        'content_type': data[0]['fields']['content_type'],
                        'object_id': data[0]['fields']['object_id']
                    }
                    create_version(
                        new_revision_id, assignment_id, 'topicnodeassignment', fields,
                        u'TopicNodeAssignment for topic {}'.format(topic.preferred_name),
                        typ= 0)
                    revision_comment += u'Add topic assignment for {}. '.format(
                        topic.preferred_name)
                else:
                    assignment_id, = assignment_select[0]

                assignment.revision_id = new_revision_id
                assignment.save()
        new_reltopics = [tid for tid in version_data[0]['fields'].pop('related_topics', [])
                         if tid in final_topicreltopics]
        new_reltopics = set(new_reltopics) - existing_topicreltopics
        for assignment in new_reltopics:
            assignment_insert = db.execute(
                u'INSERT INTO main_topicnodeassignment '
                'VALUES (DEFAULT, %s, %s, %s, %s, %s, %s) '
                'RETURNING id;',
                params=[user_id, version_dt, container_id, None,
                        ct_for_model('topicnode'), tmap_id[assignment]])
            assignment_id, = assignment_insert[0]
            existing_topicreltopics.add(assignment)
            fields = {
                'creator': user_id,
                'created': version_dt.strftime(TIME_FMT),
                'container': container_id,
                'topicname': None,
                'content_type': ct_for_model('topicnode'),
                'object_id': tmap_id[assignment]
            }
            create_version(
                new_revision_id, assignment_id, 'topicnodeassignment', fields,
                u'TopicNodeAssignment for topic {}'.format(topic.preferred_name),
                typ= 0)
            revision_comment += u'Add topic assignment for {}. '.format(
                topic.preferred_name)
        alias_versions = version.revision.version_set.filter(
            content_type_id=ct_for_model('alias'))
        for alias_version in alias_versions:
            alias = orm['main.alias'].objects.filter(id=alias_version.id)
            if not alias.exists():
                alias_version.delete()
                continue
            alias = alias.get()
            if not alias.id in final_aliases:
                alias_version.delete()
                continue
            if alias.id in existing_aliases:
                alias_version.delete()
                continue
            if project_id != pid_for_uid(alias.creator_id):
                continue
            alias_topic_name_insert = db.execute(
                u'INSERT INTO main_topicname '
                'VALUES (DEFAULT, %s, %s, %s, %s, False) '
                'RETURNING id;',
                params=[alias.creator_id, alias.created, alias.name,
                        container_id])
            alias_topic_name_id, = alias_topic_name_insert[0]
            fields = {
                'creator': alias.creator_id,
                'created': alias.created.strftime(TIME_FMT),
                'name': alias.name,
                'container': container_id,
                'is_preferred': False,
            }
            create_version(
                new_revision_id, alias_topic_name_id, 'topicname',
                fields, u'TopicName "{}"'.format(alias.name), typ=0)
            revision_comment += u'Added topic name "{}"'.format(alias.name)
            existing_aliases.add(alias.id)

        db.execute(
            'UPDATE reversion_revision '
            'SET comment = %s '
            'WHERE id = %s;',
            params=[revision_comment, new_revision_id])

        stale_revisions.add(version.revision_id)
        version.delete()
    return

class Migration(DataMigration):

    def forwards(self, orm):
        # 1. Create new topic nodes for every topic
        # 2. Connect projects to every edit they made
        # 3. Update reversions

        fix_null_creator_revisions(orm)

        # Create topic nodes for every topic
        for topic in orm['main.topic'].objects.order_by('id'):
            tmap[topic] = create_topic_node(topic)
            tmap_id[topic.id] = tmap[topic]

        # Update all the topics
        for topic in orm['main.topic'].objects.order_by('id').all():
            update_topic(topic, orm)

        for ta in orm['main.topicassignment'].objects.all():
            project = pid_for_uid(ta.creator_id)
            container_id, created_topic_name_id = get_or_create_project_container(
                ta.topic, project, ta.creator_id,  ta.created)
            topic_node_assignment_insert = db.execute(
                u'INSERT INTO main_topicnodeassignment '
                'VALUES (DEFAULT, %s, %s, %s, %s, %s, %s) '
                'RETURNING id;',
                params=[ta.creator_id, ta.created, container_id, None,
                        ta.content_type_id, ta.object_id])
            topic_node_assignment_id, = topic_node_assignment_insert[0]

            ta_versions = versions_for('topicassignment', ta.id, orm)
            for version in ta_versions:
                if not project == pid_for_uid(version.revision.user_id):
                    version.delete()
                version.object_id = str(topic_node_assignment_id)
                version.object_id_int = int(topic_node_assignment_id)
                version.content_type_id = ct_for_model('topicnodeassignment')
                data = json.loads(version.serialized_data)
                data[0]['fields'].pop('topic', None)
                data[0]['container'] = container_id
                version.serialized_data = json.dumps(data)
                version.save()

        for stale_revision_id in stale_revisions:
            db.execute(
                u'DELETE FROM reversion_version WHERE revision_id = %s;',
                params=[stale_revision_id])
            db.execute(
                u'DELETE FROM reversion_revision WHERE id = %s;',
                params=[stale_revision_id])

        featured_topics = orm['main.featureditem'].objects.filter(
            content_type_id=ct_for_model('topic'))
        for featured_item in featured_topics:
            old_topic = orm['main.topic'].objects.get(id=featured_item.object_id)
            featured_item.content_type_id = ct_for_model('topicnode')
            featured_item.object_id = tmap[old_topic]
            featured_item.save()

        return

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
        'main.projecttopiccontainer': {
            'Meta': {'object_name': 'ProjectTopicContainer'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_projecttopiccontainer_set'", 'to': "orm['auth.User']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_projecttopiccontainer_set'", 'to': "orm['auth.User']"}),
            'merged_into': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.ProjectTopicContainer']", 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Project']"}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.TopicNode']"})
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
            'Meta': {'unique_together': "(('container', 'name'),)", 'object_name': 'TopicName'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicname_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_preferred': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': "'200'"}),
            'container': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'names'", 'null': 'True', 'to': "orm['main.ProjectTopicContainer']"})
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
            'Meta': {'unique_together': "(('content_type', 'object_id', 'container'),)", 'object_name': 'TopicNodeAssignment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicnodeassignment_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'container': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'assignments'", 'null': 'True', 'to': "orm['main.ProjectTopicContainer']"}),
            'topic_name': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.TopicName']", 'null': 'True', 'blank': 'True'})
        },
        'main.topicsummary': {
            'Meta': {'object_name': 'TopicSummary'},
            'content': ('editorsnotes.main.fields.XHTMLField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_topicsummary_set'", 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'last_updater': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_to_update_topicsummary_set'", 'to': u"orm['auth.User']"}),
            'container': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'blank': 'True', 'related_name': "'summary'", 'null': 'True', 'to': "orm['main.ProjectTopicContainer']"})
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
