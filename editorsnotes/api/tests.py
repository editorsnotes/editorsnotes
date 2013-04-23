# -*- coding: utf-8 -*-

import json
from django.core.urlresolvers import reverse
from django.test import TestCase
from lxml import etree
from editorsnotes.main.tests import create_test_user
from editorsnotes.main import models

class TopicAPITestCase(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.client.login(username='testuser', password='testuser')

    def test_simple_topic_CRUD(self):
        """Simple topic create, read, update, delete."""
        data = {
            'preferred_name': u'Patrick Golden',
            'summary': u'<p>A writer of tests</p>'
        }

        # Create the topic
        response = self.client.post(
            reverse('api-topics-list'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        new_topic_id = response.data.get('id')
        new_topic = models.Topic.objects.get(id=new_topic_id)
        self.assertEqual(etree.tostring(new_topic.summary),
                         response.data.get('summary'))

        # Posting the same data should raise a 400 error
        response = self.client.post(
            reverse('api-topics-list'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get('preferred_name'),
                         [u'Topic with this Preferred name already exists.'])

        # Update the topic with new data.
        data['summary'] = u'<p>A writer of great tests.</p>'

        response = self.client.put(
            reverse('api-topics-detail', args=[new_topic_id]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        new_topic = models.Topic.objects.get(id=new_topic_id)
        self.assertEqual(data['summary'], etree.tostring(new_topic.summary))

        # Delete the topic
        self.assertEqual(models.Topic.objects.count(), 1)
        response = self.client.delete(
            reverse('api-topics-detail', args=[new_topic_id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(models.Topic.objects.filter(id=new_topic_id).count(), 0)

class DocumentAPITestCase(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.client.login(username='testuser', password='testuser')
    def test_simple_document_CRUD(self):
        """Simple document create, read, update, delete."""
        data = {
            'description': u'<div>Draper, Theodore. <em>Roots of American Communism</em></div>'
        }

        response = self.client.post(
            reverse('api-documents-list'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        new_document_id = response.data.get('id')
        new_document = models.Document.objects.get(id=new_document_id)
        self.assertEqual(etree.tostring(new_document.description),
                         data['description'])

        new_data = data.copy()
        new_data['description'] = \
            u'<div>Draper, Theodore. <em>Roots of American Communism</em>. New York: Viking Press, 1957.</div>'
        response = self.client.put(
            reverse('api-documents-detail', args=[new_document_id]),
            json.dumps(new_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        new_document = models.Document.objects.get(id=new_document_id)
        self.assertEqual(response.data.get('description'),
                         new_data['description'])
        self.assertEqual(etree.tostring(new_document.description),
                         new_data['description'])

        response = self.client.delete(
            reverse('api-documents-detail',args=[new_document_id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(models.Document.objects.filter(id=new_document_id).count(), 0)


class NoteAPITestCase(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.client.login(username='testuser', password='testuser')
    def test_simple_note_CRUD(self):
        """Simple note create, read, update, delete."""
        data = {
            'title': u'Is testing good?',
            'content': u'<p>We need to figure out if it\'s worth it to write tests.</p>',
            'status': '2'
        }

        response = self.client.post(
            reverse('api-notes-list'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

        new_note_id = response.data.get('id')
        new_note = models.Note.objects.get(id=new_note_id)

        self.assertEqual(etree.tostring(new_note.content), data['content'])
        self.assertEqual(etree.tostring(new_note.content), response.data.get('content'))

        self.assertEqual(new_note.title, response.data.get('title'))
        self.assertEqual(new_note.title, data['title'])

        self.assertEqual(new_note.status, response.data.get('status'))
        self.assertEqual(new_note.status, data['status'])

        # Attempting to make a note with the same title should return a 400 err
        response = self.client.post(
            reverse('api-notes-list'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

        # Update the status of this note
        new_data = data.copy()
        new_data['status'] = '1'
        response = self.client.put(
            reverse('api-notes-detail', args=[new_note_id]),
            json.dumps(new_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        new_note = models.Note.objects.get(id=new_note_id)
        self.assertEqual(new_note.status, new_data['status'])

        # Add a citation
        doc_response = self.client.post(
            reverse('api-documents-list'),
            json.dumps({
                'description': \
                    u'“Testing in Django.” Django documentation,'
                    'Accessed 17 April 2013.'
                    'https://docs.djangoproject.com/en/dev/topics/testing/.'
            }),
            content_type='application/json'
        )
        self.assertEqual(doc_response.status_code, 201)
        cited_doc_id = doc_response.data.get('id')

        note_section_response = self.client.post(
            reverse('api-notes-detail', args=[new_note_id]),
            json.dumps({
                'section_type': 'citation',
                'document': reverse('api-documents-detail', args=[cited_doc_id]),
                'content': u'<div>A great introduction to testing, including its benefits.</div>'
            }),
            content_type='application/json'
        )
        self.assertEqual(note_section_response.status_code, 201)
        self.assertEqual(new_note.sections.count(), 1)
        citation_section_id = note_section_response.data.get('section_id')

        # Add a text section
        text_section_response = self.client.post(
            reverse('api-notes-detail', args=[new_note_id]),
            json.dumps({
                'section_type': 'text',
                'content': u'<strong>I\'m still conflicted. What\'s the point of anything, really.</strong>'
            }),
            content_type='application/json'
        )
        self.assertEqual(text_section_response.status_code, 201)
        self.assertEqual(new_note.sections.count(), 2)

        # Edit that text section
        text_section_id = text_section_response.data.get('section_id')
        text_section_response_update = self.client.put(
            reverse('api-notes-section-detail', args=[new_note_id, text_section_id]),
            json.dumps({
                'section_type': 'text',
                'content': u'<div style="color: red;">I\'m beginning to see the Light.</div>'
            }),
            content_type='application/json'
        )
        self.assertEqual(text_section_response_update.status_code, 200)

        # Make sure this is all in order
        response = self.client.get(
            reverse('api-notes-detail', args=[new_note_id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('section_ordering'),
                         [citation_section_id, text_section_id])

        # Delete the note
        response = self.client.delete(
            reverse('api-notes-detail', args=[new_note_id]),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        
        # Make sure everything was deleted
        self.assertEqual(0, models.Note.objects.filter(id=new_note_id).count())
        self.assertEqual(0, models.NoteSection.objects.filter(note_id=new_note_id).count())
