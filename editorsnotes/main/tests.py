# -*- coding: utf-8 -*-

import unittest

from django.contrib.auth.models import Permission
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from lxml import etree

import models as main_models
from models.topics import ProjectTopicContainer as PTC
import utils
from views.auth import create_invited_user

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
    user = main_models.auth.User(username='testuser', is_staff=True, is_superuser=True)
    user.set_password('testuser')
    user.save()
    return user

class NoteTestCase(TestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.project = main_models.Project.objects.get(slug='emma')
        self.user = self.project.members.all()[0]
    def testStripStyleElementsFromContent(self):
        note = main_models.Note.objects.create(
            content=u'<style>garbage</style><h1>hey</h1><p>this is a <em>note</em></p>', 
            creator=self.user, last_updater=self.user, project=self.project)
        self.assertEquals(
            etree.tostring(note.content),
            '<div><h1>hey</h1><p>this is a <em>note</em></p></div>')
    def testAddCitations(self):
        note = main_models.Note.objects.create(
            content=u'<h1>hey</h1><p>this is a <em>note</em></p>', 
            creator=self.user, last_updater=self.user, project=self.project)
        document = main_models.Document.objects.create(
            description='Ryan Shaw, <em>My Big Book of Cool Stuff</em>, 2010.', 
            creator=self.user, last_updater=self.user, project=self.project)
        main_models.notes.CitationNS.objects.create(
            note=note, document=document, creator=self.user, last_updater=self.user)
        self.assertEquals(note.sections.count(), 1)
        self.assertEquals(note.sections_counter, 1)
        self.assertEquals(document, note.sections.select_subclasses()[0].document)
    def testAssignTopics(self):
        note = main_models.Note.objects.create(
            title='test note',
            content=u'<h1>hey</h1><p>this is a <em>note</em></p>', 
            creator=self.user, last_updater=self.user, project=self.project)
        topic = PTC.objects.get_or_create_by_name(
            u'Example', self.project, self.user)

        self.assertFalse(note.has_topic(topic))

        note.related_topics.create(container=topic, creator=self.user)

        self.assertTrue(note.has_topic(topic))
        self.assertEquals(1, len(note.related_topics.all()))
        self.assertEquals(1, len(topic.assignments.all()))
        self.assertEquals(topic, note.related_topics.all()[0].container)

class NoteTransactionTestCase(TransactionTestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.project = main_models.Project.objects.get(slug='emma')
        self.user = self.project.members.all()[0]
    def testAssignTopicTwice(self):
        note = main_models.Note.objects.create(
            title='test note',
            content=u'<h1>hey</h1><p>this is a <em>note</em></p>', 
            creator=self.user, last_updater=self.user, project=self.project)
        topic = PTC.objects.get_or_create_by_name(
            u'Example', self.project, self.user)
        note.related_topics.create(container=topic, creator=self.user)

        self.assertRaises(IntegrityError,
                          note.related_topics.create,
                          container=topic, creator=self.user)
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
        test_role = test_project.roles.get_or_create_by_name('editor')

        # We haven't invited this person yet, so this shouldn't make an account
        self.assertEqual(create_invited_user(new_user_email), None)
        
        main_models.auth.ProjectInvitation.objects.create(
            project=test_project,
            email=new_user_email,
            role=test_role.role,
            creator=self.user
        )
        new_user = create_invited_user(new_user_email)

        self.assertTrue(isinstance(new_user, main_models.auth.User))
        self.assertEqual(main_models.auth.ProjectInvitation.objects.count(), 0)
        self.assertEqual(new_user.username, 'fakeperson')

class ProjectTopicTestCase(TestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.project = main_models.Project.objects.get(slug='emma')
        self.user = self.project.members.all()[0]
        self.project2 = main_models.Project.objects.get(slug='sanger')
        self.user2 = self.project2.members.all()[0]

    def test_create_project_topic(self):
        topic, container = PTC.objects.create_along_with_node(
            u'Emma Goldman', self.project, self.user)

        self.assertTrue(isinstance(topic, main_models.topics.TopicNode))

        container2 = PTC.objects.create_from_node(
            topic, self.project2, self.user2, name=u'Emma Goldman!!!')

        self.assertEqual(topic, container2.topic)
        self.assertEqual(topic.get_connected_projects().count(), 2)

    def test_merge_topic_nodes(self):
        good_topic, good_container = PTC.objects.create_along_with_node(
            'Emma Goldman', self.project, self.user)
        bad_topic, bad_container = PTC.objects.create_along_with_node(
            u'Емма Голдман', self.project, self.user)

        bad_container.merge_into(good_container)

        bad_topic = bad_container.topic

        self.assertEqual(bad_topic.deleted, True)
        self.assertEqual(bad_container.deleted, True)
        self.assertEqual(bad_topic.merged_into, good_topic)
        self.assertEqual(bad_container.merged_into, good_container)
        self.assertEqual(good_topic.get_connected_projects().count(), 1)

class ProjectSpecificPermissionsTestCase(TestCase):
    fixtures = ['projects.json']
    def setUp(self):
        self.project = main_models.Project.objects.create(
            name='Alexander Berkman Papers Project',
            slug='abpp')
        self.user = main_models.auth.User.objects.create(
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

        # "Super roles" should have all project-specific permissions
        self.assertEqual(len(self.user.get_project_permissions(self.project)),
                         len(get_all_project_permissions()))

        self.assertTrue(self.user.has_project_perm(self.project, 'main.add_note'))

        # Even if this is a super-role, return False for a made up permission.
        # Maybe not, though?
        self.assertFalse(self.user.has_project_perm(self.project, 'made up permission'))

    def test_other_project_perms(self):
        egp = main_models.Project.objects.get(slug='emma')

        # User is not a member of this project, so shouldn't have any permissions
        self.assertEqual(egp.roles.get_for_user(self.user), None)
        self.assertEqual(len(self.user.get_project_permissions(egp)), 0)
        self.assertFalse(self.user.has_project_perm(egp, 'main.add_note'))

    def test_limited_role(self):
        # Make a role with only one permission & make sure users of that role
        # can only do that.
        researcher = main_models.auth.User.objects.create(username='a_researcher')
        new_role = self.project.roles.get_or_create_by_name('Researcher')
        note_perm = Permission.objects.get_by_natural_key('change_note', 'main', 'note')

        new_role.users.add(researcher)
        new_role.add_permissions(note_perm)

        self.assertEqual(len(researcher.get_project_permissions(self.project)), 1)
        self.assertTrue(researcher.has_project_perm(self.project, 'main.change_note'))
        self.assertFalse(researcher.has_project_perm(self.project, 'main.delete_note'))
        self.assertFalse(researcher.has_project_perm(self.project, 'main.change_topicsummary'))

    def test_invalid_project_permission(self):
        new_role = self.project.roles.get_or_create_by_name('Researcher')
        ok_perm1 = Permission.objects.get_by_natural_key('change_note', 'main', 'note')
        ok_perm2 = Permission.objects.get_by_natural_key('delete_note', 'main', 'note')

        # This isn't a project specific permission
        bad_perm = Permission.objects.get_by_natural_key('add_group', 'auth', 'group')

        new_role.add_permissions(ok_perm1, ok_perm2)
        self.assertRaises(ValueError, new_role.add_permissions, bad_perm)
        self.assertEqual(len(new_role.get_permissions()), 2)
