# -*- coding: utf-8 -*-

import unittest

from django.contrib.auth.models import User, Permission
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from lxml import etree

import models as main_models
from models.topics import TopicNode
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

class ProjectTopicTestCase(TestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.project = main_models.Project.objects.get(slug='emma')
        self.user = self.project.members.all()[0].user
        self.project2 = main_models.Project.objects.get(slug='sanger')
        self.user2 = self.project2.members.all()[0].user

    def test_create_project_topic(self):
        new_topic = TopicNode.objects.create_project_topic(
            self.project, self.user, name=u'Emma Goldman')
        self.assertTrue(isinstance(new_topic, main_models.topics.TopicNode))
        new_topic2 = TopicNode.objects.create_project_topic(
            self.project2, self.user2, topic_node=new_topic)
        self.assertEqual(new_topic, new_topic2)
        self.assertEqual(main_models.topics.TopicName.objects.count(), 2)
        self.assertEqual(new_topic.get_connected_projects().count(), 2)

    def test_merge_topic_nodes(self):
        good_topic = TopicNode.objects.create_project_topic(
            self.project, self.user, name='Emma Goldman')
        bad_topic = TopicNode.objects.create_project_topic(
            self.project, self.user, name=u'Емма Голдман')

        # No connection between this project & topic, so we should get an
        # exception
        self.assertRaises(
            main_models.topics.TopicMergeError,
            bad_topic.merge_project_topic_connections,
            self.project2, good_topic
        )

        bad_topic.merge_project_topic_connections(self.project, good_topic)

        self.assertEqual(bad_topic.deleted, True)
        self.assertEqual(bad_topic.merged_into, good_topic)
        self.assertEqual(good_topic.names.count(), 2)

    def test_delete_topic_nodes(self):
        topic = TopicNode.objects.create_project_topic(
            self.project, self.user, name='MISTAKE TOPIC')
        summary = main_models.topics.TopicSummary.objects.create(
            project=self.project,
            creator=self.user,
            last_updater=self.user,
            topic=topic,
            content='WHOOPS'
        )
        self.assertEqual(len(topic.get_project_connections(self.project)), 2)
        topic.delete_project_connections(self.project)
        self.assertTrue(topic.deleted)

class ProjectSpecificPermissionsTestCase(TestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.project = main_models.Project.objects.create(
            name='Alexander Berkman Papers Project',
            slug='abpp')
        self.user = User.objects.create(
            username='jd',
            first_name='John',
            last_name='Doe',
            is_superuser=False)
        role = self.project.roles.get_or_create_by_name(
            'Editor', is_super_role=True)
        role.users.add(self.user)

    def test_super_role(self):
        from management import get_all_project_permissions

        role = self.project.roles.get()
        self.assertEqual(role, self.project.roles.get_for_user(self.user))
        user_profile = main_models.UserProfile.get_for(self.user)

        # "Super roles" should have all project-specific permissions
        self.assertEqual(len(user_profile.get_project_permissions(self.project)),
                         len(get_all_project_permissions()))

        self.assertTrue(user_profile.has_project_perm(self.project, 'main.add_note'))
        self.assertFalse(user_profile.has_project_perm(self.project, 'made up permission'))

    def test_other_project_perms(self):
        user_profile = main_models.UserProfile.get_for(self.user)
        egp = main_models.Project.objects.get(slug='emma')

        # User is not a member of this project, so shouldn't have any permissions
        self.assertEqual(egp.roles.get_for_user(self.user), None)
        self.assertEqual(len(user_profile.get_project_permissions(egp)), 0)
        self.assertFalse(user_profile.has_project_perm(egp, 'main.add_note'))

    def test_limited_role(self):
        # Make a role with only one permission & make sure users of that role
        # can only do that.
        researcher = User.objects.create(username='a_researcher')
        new_role = self.project.roles.get_or_create_by_name('Researcher')
        note_perm = Permission.objects.get_by_natural_key('change_note', 'main', 'note')
        new_role.users.add(researcher)
        new_role.add_permissions(note_perm)

        user_profile = main_models.UserProfile.get_for(researcher)
        self.assertEqual(len(user_profile.get_project_permissions(self.project)), 1)
        self.assertTrue(user_profile.has_project_perm(self.project, 'main.change_note'))
        self.assertFalse(user_profile.has_project_perm(self.project, 'main.delete_note'))
        self.assertFalse(user_profile.has_project_perm(self.project, 'main.change_topicsummary'))

    def test_invalid_project_permission(self):
        new_role = self.project.roles.get_or_create_by_name('Researcher')
        ok_perm1 = Permission.objects.get_by_natural_key('change_note', 'main', 'note')
        ok_perm2 = Permission.objects.get_by_natural_key('delete_note', 'main', 'note')

        # This isn't a project specific permission
        bad_perm = Permission.objects.get_by_natural_key('add_group', 'auth', 'group')

        new_role.add_permissions(ok_perm1, ok_perm2)
        self.assertRaises(ValueError, new_role.add_permissions, bad_perm)
        self.assertEqual(len(new_role.get_permissions()), 2)
