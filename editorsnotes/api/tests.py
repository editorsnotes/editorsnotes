# -*- coding: utf-8 -*-

import json

from lxml import etree

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase

from reversion.models import Revision

from editorsnotes.main import models as main_models
from editorsnotes.search import get_index

def flush_es_indexes():
    en_index = get_index('main')
    activity_index = get_index('activity')

    if en_index.exists():
        en_index.delete()
    en_index.create()

    if activity_index.exists():
        activity_index.delete()
    activity_index.create()

def delete_es_indexes():
    en_index = get_index('main')
    activity_index = get_index('activity')
    if en_index.exists():
        en_index.delete()
    if activity_index.exists():
        activity_index.delete()

TEST_TOPIC = {
    'preferred_name': u'Patrick Golden',
    'alternate_names': [u'big guy', u'stretch'],
    'type': u'PER',
    'related_topics': [],
    'summary': u'<p>A writer of tests</p>'
}
def create_test_topic(**kwargs):
    data = TEST_TOPIC.copy()
    data.update(kwargs)
    data.pop('alternate_names', None)
    data.pop('related_topics', None)
    node, topic = main_models.Topic.objects.create_along_with_node(**data)
    return topic


TEST_DOCUMENT = {
    'description': u'<div>Draper, Theodore. <em>Roots of American Communism</em></div>',
    'related_topics': [],
    'zotero_data': {
        'itemType': 'book',
        'title': 'Roots of American Communism',
        'creators': [
            {'creatorType': 'author',
             'firstName': 'Theodore',
             'lastName': 'Draper'}
        ]
    }
}
def create_test_document(**kwargs):
    data = TEST_DOCUMENT.copy()
    data['zotero_data'] = json.dumps(data['zotero_data'])
    data.pop('related_topics', None)
    data.update(kwargs)
    return main_models.Document.objects.create(**data)

TEST_NOTE = {
    'title': u'Is testing good?',
    'related_topics': [],
    'content': u'<p>We need to figure out if it\'s worth it to write tests.</p>',
    'status': 'open',
    'sections': []
}
def create_test_note(**kwargs):
    data = TEST_NOTE.copy()
    data.pop('related_topics', None)
    data.update(kwargs)
    return main_models.Note.objects.create(**data)


BAD_PERMISSION_MESSAGE = u'You do not have permission to perform this action.'
NO_AUTHENTICATION_MESSAGE = u'Authentication credentials were not provided.'


class ClearContentTypesTransactionTestCase(TransactionTestCase):
    """
    See https://code.djangoproject.com/ticket/10827
    """
    def _pre_setup(self, *args, **kwargs):
        ContentType.objects.clear_cache()
        super(ClearContentTypesTransactionTestCase, self)._pre_setup(*args, **kwargs)


class TopicAPITestCase(ClearContentTypesTransactionTestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.user = main_models.User.objects.get(username='barry')
        self.project = main_models.Project.objects.get(slug='emma')
        self.client.login(username='barry', password='barry')

    def create_test_topic(self):
        data = TEST_TOPIC
        topic_node, topic = main_models.Topic.objects.create_along_with_node(
            data['preferred_name'], self.project, self.user, data['type'],
            summary=data['summary'])
        return topic

    def test_topic_api_create(self):
        "Creating a topic within your own project is ok"

        flush_es_indexes()

        response = self.client.post(
            reverse('api:topics-list', args=[self.project.slug]),
            json.dumps(TEST_TOPIC),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        new_topic_node_id = response.data.get('topic_node_id')
        topic_obj = main_models.Topic.objects.get(
            topic_node_id=new_topic_node_id, project=self.project)
        self.assertEqual(response.data.get('id'), topic_obj.id)
        self.assertEqual(etree.tostring(topic_obj.summary),
                         response.data.get('summary'))

        # Make sure a revision was created
        self.assertEqual(Revision.objects.count(), 1)

        # Make sure an entry was added to the activity index

        # Make sure a revision was created
        self.assertEqual(Revision.objects.count(), 1)

        # Make sure an entry was added to the activity index
        activity_response = self.client.get(reverse('api:projects-activity',
                                                         args=[self.project.slug]),
                                            HTTP_ACCEPT='application/json')
        self.assertEqual(activity_response.status_code, 200)
        self.assertEqual(len(activity_response.data['activity']), 1)

        activity_data = activity_response.data['activity'][0]

        expected = {
            'user': 'barry',
            'project': 'emma',
            #'time': ???,
            'type': topic_obj._meta.model_name,
            'url': topic_obj.get_absolute_url(),
            'title': topic_obj.as_text(),
            'action': 'added'
        }

        activity_data.pop('time')
        self.assertDictContainsSubset(activity_data, expected)

        # Make sure the activity entry corresponds to a reversion Version
        activity_model = main_models.auth.LogActivity.objects.get()
        version = activity_model.get_version()
        self.assertEqual((activity_model.content_type_id, activity_model.object_id),
                         (version.content_type_id, version.object_id_int))


    def test_topic_api_create_bad_permissions(self):
        "Creating a topic in an outside project is NOT OK"
        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.post(
            reverse('api:topics-list', args=[self.project.slug]),
            json.dumps(TEST_TOPIC),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_topic_api_create_logged_out(self):
        "Creating a topic while logged out is NOT OK"
        self.client.logout()
        response = self.client.post(
            reverse('api:topics-list', args=[self.project.slug]),
            json.dumps(TEST_TOPIC),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)

    def test_topic_api_duplicate_name_fails(self):
        "Creating a topic with an existing name is NOT OK"
        data = TEST_TOPIC.copy()
        topic_obj = create_test_topic(user=self.user, project=self.project)

        # Posting the same data should raise a 400 error
        response = self.client.post(
            reverse('api:topics-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get('preferred_name'),
                         [u'Topic with this preferred name already exists.'])

    def test_topic_api_list(self):
        """
        Creating a topic should add it to the ElasticSearch index, which should
        then be retrievable with the API list view.
        """
        flush_es_indexes()

        topic_obj = create_test_topic(user=self.user, project=self.project)

        response = self.client.get(reverse('api:topics-list',
                                           args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

        topic_data = response.data['results'][0]

        self.assertEqual(topic_obj.topic_node_id, topic_data['topic_node_id'])
        self.assertEqual(topic_obj.id, topic_data['id'])
        self.assertEqual(topic_obj.preferred_name, topic_data['preferred_name'])
        self.assertEqual(topic_data['preferred_name'], TEST_TOPIC['preferred_name'])

    def test_topic_api_list_other_projects(self):
        "Other projects' topic lists should be viewable, too. Even if logged out"
        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.get(reverse('api:topics-list',
                                           args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        response = self.client.get(reverse('api:topics-list',
                                           args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

    def test_topic_api_update(self):
        "Updating a topic in your own project is great"
        data = TEST_TOPIC.copy()
        topic_obj = create_test_topic(user=self.user, project=self.project)

        # Update the topic with new data.
        data['summary'] = u'<p>A writer of great tests.</p>'

        response = self.client.put(
            reverse('api:topics-detail', args=[self.project.slug, topic_obj.topic_node_id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        updated_topic_obj = main_models.Topic.objects.get(
            topic_node_id=response.data['topic_node_id'], project=self.project)
        self.assertEqual(topic_obj, updated_topic_obj)
        self.assertEqual(data['summary'], response.data['summary'])
        self.assertEqual(data['summary'], etree.tostring(updated_topic_obj.summary))

        # Make sure a revision was created upon update
        self.assertEqual(Revision.objects.count(), 1)

        # Make sure an entry was added to the activity index
        activity_response = self.client.get(reverse('api:projects-activity',
                                                         args=[self.project.slug]),
                                            HTTP_ACCEPT='application/json')
        self.assertEqual(activity_response.status_code, 200)
        activity_data = activity_response.data['activity'][0]

        expected = {
            'user': 'barry',
            'project': 'emma',
            #'time': ???,
            'type': updated_topic_obj._meta.model_name,
            'url': updated_topic_obj.get_absolute_url(),
            'title': updated_topic_obj.as_text(),
            'action': 'changed'
        }

        activity_data.pop('time')
        self.assertDictContainsSubset(activity_data, expected)

    def test_topic_api_update_bad_permissions(self):
        "Updating a topic in an outside project is NOT OK"
        data = TEST_TOPIC.copy()
        topic_obj = create_test_topic(user=self.user, project=self.project)

        data['preferred_name'] = u'Patrick Garbage'
        data['summary'] = u'<p>such a piece of garbage LOL</p>'

        self.client.logout()
        self.client.login(username='esther', password='esther')

        response = self.client.put(
            reverse('api:topics-detail', args=[self.project.slug, topic_obj.topic_node_id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_topic_api_update_logged_out(self):
        "Updating a topic when not logged in is NOT OK"
        data = TEST_TOPIC.copy()
        topic_obj = create_test_topic(user=self.user, project=self.project)

        self.client.logout()
        response = self.client.put(
            reverse('api:topics-detail', args=[self.project.slug, topic_obj.topic_node_id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)

    def test_topic_api_delete(self):
        "Deleting a topic in your own project is ok"
        topic_obj = create_test_topic(user=self.user, project=self.project)

        # Delete the topic
        self.assertEqual(main_models.Topic.objects.count(), 1)
        response = self.client.delete(
            reverse('api:topics-detail', args=[self.project.slug, topic_obj.topic_node_id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(main_models.Topic.objects.count(), 0)
        self.assertEqual(main_models.TopicNode.objects.count(), 1)

        # Make sure an entry was added to the activity index
        activity_response = self.client.get(reverse('api:projects-activity',
                                                         args=[self.project.slug]),
                                            HTTP_ACCEPT='application/json')
        self.assertEqual(activity_response.status_code, 200)
        activity_data = activity_response.data['activity'][0]

        expected = {
            'user': 'barry',
            'project': 'emma',
            #'time': ???,
            'type': topic_obj._meta.model_name,
            'url': None,
            'title': topic_obj.as_text(),
            'action': 'deleted'
        }

        activity_data.pop('time')
        self.assertDictContainsSubset(activity_data, expected)

    def test_topic_api_delete_bad_permissions(self):
        "Deleting a topic in an outside project is NOT OK"
        topic_obj = create_test_topic(user=self.user, project=self.project)
        self.client.logout()
        self.client.login(username='esther', password='esther')

        response = self.client.delete(
            reverse('api:topics-detail', args=[self.project.slug, topic_obj.topic_node_id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_topic_api_delete_logged_out(self):
        topic_obj = create_test_topic(user=self.user, project=self.project)
        self.client.logout()
        response = self.client.delete(
            reverse('api:topics-detail', args=[self.project.slug, topic_obj.topic_node_id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)


class DocumentAPITestCase(ClearContentTypesTransactionTestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.user = main_models.User.objects.get(username='barry')
        self.project = main_models.Project.objects.get(slug='emma')
        self.client.login(username='barry', password='barry')

    def create_test_document(self):
        data = TEST_DOCUMENT
        document = main_models.Document.objects.create(
            description=data['description'],
            zotero_data=json.dumps(data['zotero_data']),
            project=self.project, creator=self.user, last_updater=self.user)
        return document

    def test_document_api_create(self):
        "Creating a document in your own project is ok"
        data = TEST_DOCUMENT.copy()
        response = self.client.post(
            reverse('api:documents-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        new_document_id = response.data.get('id')
        new_document = main_models.Document.objects.get(id=new_document_id)
        self.assertEqual(etree.tostring(new_document.description),
                         data['description'])

        # Make sure a revision was created
        self.assertEqual(Revision.objects.count(), 1)

    def test_document_api_create_bad_permissions(self):
        "Creating a document in another project is NOT OK"
        data = TEST_DOCUMENT.copy()
        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.post(
            reverse('api:documents-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_document_api_create_logged_out(self):
        "Creating a document while logged out is NOT OK"
        data = TEST_DOCUMENT.copy()
        self.client.logout()
        response = self.client.post(
            reverse('api:documents-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)

    def test_document_api_duplicate_name_fails(self):
        "Creating a document with a duplicate name is NOT OK"
        document_obj = create_test_document(
            project=self.project, creator=self.user, last_updater=self.user)
        data = TEST_DOCUMENT.copy()
        response = self.client.post(
            reverse('api:documents-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['description'],
                         [u'Document with this description already exists.'])

    def test_document_api_list(self):
        """
        Creating a document should add it to the ElasticSearch index, which
        should then be retrievable with the API list view, which is viewable by
        anyone.
        """
        flush_es_indexes()
        document_obj = create_test_document(
            project=self.project, creator=self.user, last_updater=self.user)
        response = self.client.get(reverse('api:documents-list', args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], document_obj.id)
        self.assertEqual(response.data['results'][0]['description'],
                         etree.tostring(document_obj.description))

        original_response_content = response.content
        orig_links = original_response_content.pop('_links')

        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.get(reverse('api:documents-list',
                                           args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        new_links_1 = response.content.pop('_links')
        self.assertNotEqual(orig_links, new_links_1)

        self.assertEqual(response.content, original_response_content)

        self.client.logout()
        response = self.client.get(reverse('api:documents-list',
                                           args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        new_links_2 = response.content.pop('_links')
        self.assertEqual(new_links_1, new_links_2)
        self.assertNotEqual(orig_links, new_links_2)
        self.assertEqual(response.content, original_response_content)

    def test_document_api_update(self):
        "Updating a document in your own project is ok"
        document_obj = create_test_document(
            project=self.project, creator=self.user, last_updater=self.user)
        data = TEST_DOCUMENT.copy()
        data['description'] = (u'<div>Draper, Theodore. <em>Roots of American '
                               'Communism</em>. New York: Viking Press, 1957.</div>')
        response = self.client.put(
            reverse('api:documents-detail', args=[self.project.slug, document_obj.id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], document_obj.id)

        updated_document = main_models.Document.objects.get(id=document_obj.id)
        self.assertEqual(response.data.get('description'), data['description'])
        self.assertEqual(etree.tostring(updated_document.description), data['description'])

        # Make sure a revision was created upon update
        self.assertEqual(Revision.objects.count(), 1)

    def test_document_api_update_bad_permissions(self):
        "Updating a document in another project is NOT OK"
        document_obj = create_test_document(
            project=self.project, creator=self.user, last_updater=self.user)
        self.client.logout()
        self.client.login(username='esther', password='esther')

        data = TEST_DOCUMENT.copy()
        data['description'] = u'a stupid book!!!!!!!'
        response = self.client.put(
            reverse('api:documents-detail', args=[self.project.slug, document_obj.id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_document_api_update_logged_out(self):
        "Updating a document when logged out is NOT OK"
        document_obj = create_test_document(
            project=self.project, creator=self.user, last_updater=self.user)
        self.client.logout()
        data = TEST_DOCUMENT.copy()
        data['description'] = u'a stupid book!!!!!!!!!!!!!!!!!!!!'
        response = self.client.put(
            reverse('api:documents-detail', args=[self.project.slug, document_obj.id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)

    def test_document_api_delete(self):
        "Deleting a document in your own project is ok"
        document_obj = create_test_document(
            project=self.project, creator=self.user, last_updater=self.user)
        response = self.client.delete(
            reverse('api:documents-detail', args=[self.project.slug, document_obj.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(main_models.Document.objects.filter(id=document_obj.id).count(), 0)

    def test_document_api_delete_bad_permissions(self):
        "Deleting a document in an outside project is NOT OK"
        document_obj = create_test_document(
            project=self.project, creator=self.user, last_updater=self.user)
        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.delete(
            reverse('api:documents-detail', args=[self.project.slug, document_obj.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_document_api_delete_logged_out(self):
        "Deleting a document while logged out is NOT OK"
        document_obj = create_test_document(
            project=self.project, creator=self.user, last_updater=self.user)
        self.client.logout()
        response = self.client.delete(
            reverse('api:documents-detail', args=[self.project.slug, document_obj.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)


class NoteAPITestCase(ClearContentTypesTransactionTestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.user = main_models.User.objects.get(username='barry')
        self.project = main_models.Project.objects.get(slug='emma')
        self.client.login(username='barry', password='barry')

    def create_test_note(self):
        data = TEST_NOTE
        note = main_models.Note.objects.create(
            title=data['title'],
            content=data['content'],
            status='1',
            project=self.project,
            creator=self.user,
            last_updater=self.user)
        return note

    def create_test_note_with_section(self):
        note = self.create_test_note()
        main_models.TextNS.objects.create(
            note=note,
            content='<p>Need to get started on this one</p>',
            creator=self.user,
            last_updater=self.user)
        return note

    def test_note_api_list_links(self):
        """
        Note resources should have hyperlinks to edit the note if the
        authenticated user has the right permissions.
        """
        response = self.client.get(
            reverse('api:notes-list', args=[self.project.slug]),
            HTTP_ACCEPT='application/json')

        add_link = filter(lambda link: link['rel'] == 'add',
                          response.data.get('_links'))
        self.assertEqual(len(add_link), 1)

        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.get(
            reverse('api:notes-list', args=[self.project.slug]),
            HTTP_ACCEPT='application/json')
        add_link = filter(lambda link: link['rel'] == 'add',
                          response.data.get('_links'))
        self.assertEqual(len(add_link), 0)
    def test_note_api_detail_links(self):
        """
        Note resources should have hyperlinks to edit the note if the
        authenticated user has the right permissions.
        """
        note_obj = self.create_test_note()

        response = self.client.get(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
            HTTP_ACCEPT='application/json')

        edit_link = filter(lambda link: link['rel'] == 'edit', response.data.get('_links'))
        delete_link = filter(lambda link: link['rel'] == 'delete', response.data.get('_links'))
        self.assertEqual(len(edit_link), 1)
        self.assertEqual(len(delete_link), 1)

        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.get(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
            HTTP_ACCEPT='application/json')
        edit_link = filter(lambda link: link['rel'] == 'edit', response.data.get('_links'))
        delete_link = filter(lambda link: link['rel'] == 'delete', response.data.get('_links'))
        self.assertEqual(len(edit_link), 0)
        self.assertEqual(len(delete_link), 0)

    def test_note_api_create(self):
        "Creating a note within your own project is ok"
        data = TEST_NOTE.copy()

        related_topics = [
            create_test_topic(preferred_name='Testing',
                              project=self.project,
                              user=self.user),
            create_test_topic(preferred_name='Django',
                              project=self.project,
                              user=self.user)
        ]

        data['related_topics'] = [
            topic.get_absolute_url() for topic in related_topics
        ]

        response = self.client.post(
            reverse('api:notes-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        new_note_id = response.data.get('id')
        new_note_obj = main_models.Note.objects.get(id=new_note_id)

        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['status'], data['status'])
        self.assertEqual(response.data['content'], data['content'])
        self.assertEqual(response.data['title'], new_note_obj.title)
        self.assertEqual(response.data['content'], etree.tostring(new_note_obj.content))

        url_for = lambda topic: response.wsgi_request\
                .build_absolute_uri(topic.get_absolute_url())
        self.assertEqual(response.data['related_topics'], [
            {
                'id': topic.id,
                'topic_node_id': topic.topic_node_id,
                'url': url_for(topic),
                'preferred_name': topic.preferred_name
            }
            for topic in related_topics
        ])

        # Make sure a revision was created upon create
        self.assertEqual(Revision.objects.count(), 1)

    def test_note_api_create_bad_permissions(self):
        "Creating a note in an outside project is NOT OK"
        data = TEST_NOTE.copy()
        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.post(
            reverse('api:notes-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_note_api_create_logged_out(self):
        "Creating a note while logged out is NOT OK"
        data = TEST_NOTE.copy()
        self.client.logout()
        response = self.client.post(
            reverse('api:notes-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)

    def test_note_api_duplicate_title(self):
        "Creating a note with an existing title is NOT OK"
        self.create_test_note()
        data = TEST_NOTE.copy()
        response = self.client.post(
            reverse('api:notes-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['title'],
                         [u'Note with this title already exists.'])

    def test_note_api_list(self):
        """
        Creating a note should add it to the ElasticSearch index, which should
        then be retrievable with the API list, which is viewable by anyone.
        """
        flush_es_indexes()
        note_obj = self.create_test_note()
        response = self.client.get(reverse('api:notes-list',
                                           args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], note_obj.id)
        self.assertEqual(response.data['results'][0]['title'], note_obj.title)

        original_response_content = response.content
        orig_links = original_response_content.pop('_links')

        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.get(reverse('api:notes-list',
                                           args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        new_links_1 = response.content.pop('_links')
        self.assertNotEqual(orig_links, new_links_1)

        self.assertEqual(response.content, original_response_content)

        self.client.logout()
        response = self.client.get(reverse('api:notes-list',
                                           args=[self.project.slug]),
                                   HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        new_links_2 = response.content.pop('_links')
        self.assertEqual(new_links_1, new_links_2)
        self.assertNotEqual(orig_links, new_links_2)

        self.assertEqual(response.content, original_response_content)

    def test_note_api_update(self):
        "Updating a note in your own project is ok"
        note_obj = self.create_test_note()
        data = TEST_NOTE.copy()
        data['title'] = u'Тестовать'

        response = self.client.put(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], note_obj.id)
        self.assertEqual(response.data['title'], data['title'])

        updated_note = main_models.Note.objects.get(id=note_obj.id)
        self.assertEqual(response.data['title'], updated_note.title)

        # Make sure a revision was created upon update
        self.assertEqual(Revision.objects.count(), 1)

    def test_note_api_update_bad_permissions(self):
        "Updating a note in an outside project is NOT OK"
        note_obj = self.create_test_note()
        self.client.logout()
        self.client.login(username='esther', password='esther')
        data = TEST_NOTE.copy()
        data['title'] = u'Нет!!!!!!'
        response = self.client.put(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

        response = self.client.get(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
                    HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        note_obj.is_private = True
        note_obj.save()
        response = self.client.get(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
                    HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_note_api_update_logged_out(self):
        "Updating a note while logged out is NOT OK"
        note_obj = self.create_test_note()
        self.client.logout()
        data = TEST_NOTE.copy()
        data['title'] = u'Нет!!!!!!'
        response = self.client.put(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)

    def test_note_api_delete(self):
        "Deleting a note in your own project is ok"
        note_obj = self.create_test_note()
        response = self.client.delete(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(main_models.Note.objects.filter(id=note_obj.id).count(), 0)

    def test_note_api_delete_bad_permissions(self):
        "Deleting a note in an outside project is NOT OK"
        note_obj = self.create_test_note()
        self.client.logout()
        self.client.login(username='esther', password='esther')
        response = self.client.delete(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], BAD_PERMISSION_MESSAGE)

    def test_note_api_delete_logged_out(self):
        "Deleting a note while logged out is NOT OK"
        note_obj = self.create_test_note()
        self.client.logout()
        response = self.client.delete(
            reverse('api:notes-detail', args=[self.project.slug, note_obj.id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], NO_AUTHENTICATION_MESSAGE)

    def make_section_data(self):
        another_note_obj = main_models.Note.objects.create(
            title='Another note', status='0', project=self.project,
            content='Just another note.',
            creator=self.user, last_updater=self.user)

        document_obj = main_models.Document.objects.create(
            description="New document", project=self.project,
            creator=self.user, last_updater=self.user)

        return [
            {
                'section_type': 'text',
                'content': 'this is the start'
            },
            {
                'section_type': 'citation',
                'document': document_obj.get_absolute_url(),
                'content': 'A fascinating article.'
            },
            {
                'section_type': 'note_reference',
                'note_reference': another_note_obj.get_absolute_url(),
                'content': 'See also this note.'
            }
        ]

    def test_note_api_create_note_sections(self):
        "Create a test note with multiple sections"
        # First create a note with multiple sections
        data = TEST_NOTE.copy()
        data.update({ 'sections': self.make_section_data() })

        response = self.client.post(
            reverse('api:notes-list', args=[self.project.slug]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Revision.objects.count(), 1)
        self.assertEqual(len(response.data['sections']), 3)

        # Update one of the sections
        data.update({ 'sections': response.data['sections'] })
        data['sections'][0]['content'] = 'This is an updated section'

        response = self.client.put(
            reverse('api:notes-detail', args=[self.project.slug,
                                                  response.data['id']]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Revision.objects.count(), 2)
        self.assertEqual(len(response.data['sections']), 3)
        self.assertEqual(response.data['sections'][0]['content'],
                         '<div>This is an updated section</div>')

        # Delete all the sections
        data.update({ 'sections': [] })
        response = self.client.put(
            reverse('api:notes-detail', args=[self.project.slug,
                                                  response.data['id']]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Revision.objects.count(), 3)
        self.assertEqual(len(response.data['sections']), 0)
        self.assertEqual(main_models.NoteSection.objects.count(), 0)
