# -*- coding: utf-8 -*-

import unittest

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from lxml import etree

import models as main_models
import utils
from views import create_invited_user

class UtilsTestCase(unittest.TestCase):
    def test_truncate(self):
        self.assertEquals(utils.truncate(u'xxxxxxxxxx', 4), u'xx... xx')
    def test_native_to_utc(self):
        from datetime import datetime
        naive_datetime = datetime(2011, 2, 10, 16, 42, 54, 421353)
        self.assertEquals( # assuming settings.TIME_ZONE is Pacific Time
            'datetime.datetime(2011, 2, 11, 0, 42, 54, 421353, tzinfo=<UTC>)',
            repr(utils.naive_to_utc(naive_datetime)))
        self.assertEquals(
            'datetime.datetime(2011, 2, 10, 16, 42, 54, 421353, tzinfo=<UTC>)',
            repr(utils.naive_to_utc(naive_datetime, 'UTC')))
        aware_datetime = utils.naive_to_utc(naive_datetime)
        self.assertRaises(TypeError, utils.naive_to_utc, aware_datetime)
    def test_alpha_columns(self):
        import string
        import random
        class Item:
            def __init__(self, key):
                self.key = key
        items = [ Item(letter) for letter in string.lowercase ]
        random.shuffle(items)
        columns = utils.alpha_columns(items, 'key', itemkey='thing')
        self.assertEquals(3, len(columns))
        self.assertEquals(9, len(columns[0]))
        self.assertEquals(9, len(columns[1]))
        self.assertEquals(8, len(columns[2]))
        self.assertEquals('A', columns[0][0]['first_letter'])
        self.assertEquals('a', columns[0][0]['thing'].key)
        self.assertEquals('J', columns[1][0]['first_letter'])
        self.assertEquals('S', columns[2][0]['first_letter'])
        self.assertEquals('Z', columns[2][7]['first_letter'])

def create_test_user():
    user = User(username='testuser', is_staff=True, is_superuser=True)
    user.set_password('testuser')
    user.save()
    return user

class TopicTestCase(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.topics = []
        self.topics.append(main_models.Topic.objects.create(
                preferred_name=u'Foote, Edward B. (Edward Bliss) 1829-1906', 
                summary='Foote was the man.',
                creator=self.user, last_updater=self.user))
        self.topics.append(main_models.Topic.objects.create(
                preferred_name=u'Räggler å paschaser på våra mål tå en bonne', 
                summary='Weird language!',
                creator=self.user, last_updater=self.user))
        self.topics.append(main_models.Topic.objects.create(
                preferred_name=u'Not unicode', 
                summary='Another test topic.',
                creator=self.user, last_updater=self.user))
    def tearDown(self):
        for t in self.topics:
            t.delete()
    def testSlugGeneration(self):
        self.assertEquals(self.topics[0].slug,
                          u'Foote,_Edward_B_Edward_Bliss_1829-1906')
        self.assertEquals(self.topics[1].slug,
                          u'Räggler_å_paschaser_på_våra_mål_tå_en_bonne')
        self.assertEquals(self.topics[2].slug,
                          u'Not_unicode')
    def testRelatedTopics(self):
        self.topics[0].related_topics.add(self.topics[1])
        self.topics[0].related_topics.add(self.topics[2])
        self.topics[0].save()
        for t in self.topics[1:]:
            related = t.related_topics.all()
            self.assertEquals(len(related), 1)
            self.assertEquals(related[0], self.topics[0])

class NoteTestCase(TestCase):
    def setUp(self):
        self.user = create_test_user()
    def testStripStyleElementsFromContent(self):
        note = main_models.Note.objects.create(
            content=u'<style>garbage</style><h1>hey</h1><p>this is a <em>note</em></p>', 
            creator=self.user, last_updater=self.user)
        self.assertEquals(
            etree.tostring(note.content),
            '<div><h1>hey</h1><p>this is a <em>note</em></p></div>')
        note.delete()
    def testAddCitations(self):
        note = main_models.Note.objects.create(
            content=u'<h1>hey</h1><p>this is a <em>note</em></p>', 
            creator=self.user, last_updater=self.user)
        document = main_models.Document.objects.create(
            description='Ryan Shaw, <em>My Big Book of Cool Stuff</em>, 2010.', 
            creator=self.user, last_updater=self.user)
        note.citations.create(
            document=document, creator=self.user, last_updater=self.user)
        self.assertEquals(1, len(note.citations.all()))
        self.assertEquals(document, note.citations.all()[0].document)
        note.delete()
        document.delete()
    def testAssignTopics(self):
        note = main_models.Note.objects.create(
            content=u'<h1>hey</h1><p>this is a <em>note</em></p>', 
            creator=self.user, last_updater=self.user)
        topic = main_models.Topic.objects.create(
            preferred_name=u'Example', 
            summary='An example topic',
            creator=self.user, last_updater=self.user)
        self.assertFalse(note.has_topic(topic))
        main_models.TopicAssignment.objects.create(
            content_object=note, topic=topic, creator=self.user)
        self.assertTrue(note.has_topic(topic))
        self.assertEquals(1, len(note.topics.all()))
        self.assertEquals(1, len(topic.assignments.all()))
        self.assertEquals(topic, note.topics.all()[0].topic)
        note.delete()
        topic.delete()

class NoteTransactionTestCase(TransactionTestCase):
    def setUp(self):
        self.user = create_test_user()
    def testAssignTopicTwice(self):
        note = main_models.Note.objects.create(
            content=u'<h1>hey</h1><p>this is a <em>note</em></p>', 
            creator=self.user, last_updater=self.user)
        topic = main_models.Topic.objects.create(
            preferred_name=u'Example', 
            summary='An example topic',
            creator=self.user, last_updater=self.user)
        main_models.TopicAssignment.objects.create(
            content_object=note, topic=topic, creator=self.user)
        self.assertRaises(IntegrityError,
                          main_models.TopicAssignment.objects.create,
                          content_object=note, topic=topic, creator=self.user)
        transaction.rollback()
        note.delete()
        topic.delete()

class NewUserTestCase(TestCase):
    def setUp(self):
        self.user = create_test_user()
    def test_create_new_user(self):
        new_user_email = 'fakeperson@example.com'

        test_project = main_models.Project.objects.create(
            name='Editors\' Notes\' Idiot Brigade',
            slug='ENIB',
        )

        # We haven't invited this person yet, so this shouldn't make an account
        self.assertEqual(create_invited_user(new_user_email), None)
        
        main_models.ProjectInvitation.objects.create(
            project=test_project,
            email=new_user_email,
            role='editor',
            creator=self.user
        )
        new_user = create_invited_user(new_user_email)

        self.assertTrue(isinstance(new_user, User))
        self.assertEqual(main_models.ProjectInvitation.objects.count(), 0)
        self.assertEqual(new_user.username, 'fakeperson')
