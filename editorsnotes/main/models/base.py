# -*- coding: utf-8 -*-

import json

from django.contrib.auth.models import User
from django.core import urlresolvers
from django.db import models
from django.utils.html import conditional_escape
import reversion

from .. import utils

class CreationMetadata(models.Model):
    creator = models.ForeignKey(User, editable=False, related_name='created_%(class)s_set')
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True
        get_latest_by = 'created'

class LastUpdateMetadata(CreationMetadata):
    last_updater = models.ForeignKey(User, editable=False, related_name='last_to_update_%(class)s_set')
    last_updated = models.DateTimeField(auto_now=True)    
    class Meta:
        abstract = True

class Administered():
    def get_admin_url(self):
        return urlresolvers.reverse(
            'admin:main_%s_change' % self._meta.module_name, args=(self.id,))

class URLAccessible():
    @models.permalink
    def get_absolute_url(self):
        return ('%s_view' % self._meta.module_name, [str(self.id)])
    def __unicode__(self):
        return utils.truncate(self.as_text())
    def as_text(self):
        raise Exception('Must implement %s.as_text()' % self._meta.module_name)
    def as_html(self):
        return '<span class="%s">%s</span>' % (
            self._meta.module_name, conditional_escape(self.as_text()))

class PermissionError(StandardError):
    pass

# Adapted from http://djangosnippets.org/snippets/1502/
class PermissionsMixin(object):
    def attempt(self, action, user, msg=None):
        return PermissionsMixin._attempt(self, action, user, msg)

    @staticmethod
    def _attempt(obj, action, user, msg):
        # Need to fix for users who are not logged in
        if not (isinstance(action, basestring) and isinstance(user, User)):
            raise TypeError
        if user.is_superuser or getattr(obj, 'allow_%s_for' % action)(user):
            return True
        else:
            return False

class ProjectSpecific(models.Model, PermissionsMixin):
    affiliated_projects = models.ManyToManyField('Project', blank=True, null=True)
    class Meta:
        abstract = True

    def get_all_updaters(self):
        all_updaters = set()
        for version in reversion.get_for_object(self):
            uid = json.loads(
                version.serialized_data)[0]['fields'].get('last_updater')
            if uid:
                all_updaters.add(uid)
        return [User.objects.select_related().get(id=u).get_profile() for u in all_updaters]

    def get_project_affiliation(self):
        projects = {u.affiliation for u in self.get_all_updaters() if u.affiliation}
        return list(projects)

    # Custom Project permissions
    def allow_delete_for(self, user):
        object_affiliation = self.affiliated_projects.all()
        # Make sure no other projects are using this object before deleting
        other_contributing_projects = set.difference(
            set(object_affiliation), set([user.get_profile().affiliation]))
        if len(other_contributing_projects):
            msg = 'Cannot delete %s because it is in use by %s' % (
                self, ', '.join([p.name for p in other_contributing_projects]))
            raise PermissionError(msg)
        else:
            return True
    def allow_change_for(self, user):
        object_affiliation = self.affiliated_projects.all()
        can_change = False
        for p in object_affiliation:
            if user.has_perm('%s.%s.change_%s' % (self._meta.app_label, p.slug, self._meta.module_name)):
                can_change=True
                break
        return can_change
    def allow_view_for(self, user):
        object_affiliation = self.affiliated_projects.all()
        can_view = False
        for p in object_affiliation:
            if user.has_perm('%s.%s.view_%s' % (self._meta.app_label, p.slug, self._meta.module_name)):
                can_view=True
                break
        return can_view
