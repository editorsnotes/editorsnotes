# -*- coding: utf-8 -*-

from django.test import TestCase
from editorsnotes.main.tests import create_test_user
from editorsnotes.main import models

class TopicAdminTestCase(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.topics = []
        self.topics.append(models.Topic.objects.create(
            preferred_name=u'Ленинь, Владимир Ильич',
            summary=u'Мужчина; коммунисть.',
            creator=self.user, last_updater=self.user))
        self.topics.append(models.Topic.objects.create(
            preferred_name=u'Goldman, Emma',
            summary=u'Nowhere at home.',
            creator=self.user, last_updater=self.user))
        self.topics.append(models.Topic.objects.create(
            preferred_name=u'Doe, John', 
            summary='A simple man.',
            creator=self.user, last_updater=self.user))
        self.client.login(username='testuser', password='testuser')
        self.blank_form_data = {
            'preferred_name': u'',
            'summary': u'',
            'alias-TOTAL_FORMS': 0,
            'alias-INITIAL_FORMS': 0,
            'alias-MAX_NUM_FORMS': 1000,
            'citation-TOTAL_FORMS': 0,
            'citation-INITIAL_FORMS': 0,
            'citation-MAX_NUM_FORMS': 1000,
            'topicassignment-TOTAL_FORMS': 0,
            'topicassignment-INITIAL_FORMS': 0,
            'topicassignment-MAX_NUM_FORMS': 1000,
        }
    def tearDown(self):
        for t in self.topics:
            t.delete()
    def test_invalid_slugs(self):
        data = self.blank_form_data.copy()
        data.update({
            'preferred_name': u'Doe, John',
            'summary': u'nnnn'
        })
        response = self.client.post('/admin/main/topic/add/', data)
        self.assertFormError(
            response, 'form', 'preferred_name',
            u'Topic with this Preferred name already exists.')

        data = self.blank_form_data.copy()
        data.update({
            'preferred_name': u'Doe,* John',
            'summary': u'pppppppp'
        })
        response = self.client.post('/admin/main/topic/add/', data)
        self.assertFormError(
            response, 'form', 'preferred_name',
            u'Topic with a very similar Preferred name already exists.')

    def test_related_topics(self):
        topic = models.Topic.objects.create(
            preferred_name=u'Троцкий, Лев Давидович',
            summary=u'Также мужчина; также коммунисть.',
            creator=self.user, last_updater=self.user)
        data = self.blank_form_data.copy()

        data.update({
            'preferred_name': topic.preferred_name,
            'summary': topic.summary,
            'citation-TOTAL_FORMS': 1,
            'alias-TOTAL_FORMS': 1,
            'topicassignment-TOTAL_FORMS': 1,
            'topicassignment-0-id': u'',
            'topicassignment-0-topic': self.topics[0].id
        })
        response = self.client.post(topic.get_admin_url(), data)
        self.assertEqual(topic.related_topics.count(), 1)

        data.update({
            'topicassignment-INITIAL_FORMS': 1,
            'topicassignment-TOTAL_FORMS': 2,
            'topicassignment-0-id': topic.related_topics.all()[0].id,
            'topicassignment-0-topic': self.topics[0].id,
            'topicassignment-0-DELETE': True,
            'topicassignment-1-id': u'',
            'topicassignment-1-topics': u''
        })
        response = self.client.post(topic.get_admin_url(), data)
        self.assertEqual(topic.related_topics.count(), 0)
