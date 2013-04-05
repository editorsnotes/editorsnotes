# -*- coding: utf-8 -*-

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
import reversion

from .. import fields
from base import URLAccessible, CreationMetadata, PermissionsMixin
        
class UserProfile(models.Model, URLAccessible):
    user = models.ForeignKey(User, unique=True)
    affiliation = models.ForeignKey('Project', blank=True, null=True,
                                    related_name='members')
    zotero_key = models.CharField(max_length='24', blank=True, null=True)
    zotero_uid = models.CharField(max_length='6', blank=True, null=True)
    class Meta:
        app_label = 'main'
    def _get_display_name(self):
        "Returns the full name if available, or the username if not."
        display_name = self.user.username
        if self.user.first_name:
            display_name = self.user.first_name
            if self.user.last_name:
                display_name = '%s %s' % (self.user.first_name, self.user.last_name)
        return display_name
    display_name = property(_get_display_name)
    @models.permalink
    def get_absolute_url(self):
        return ('user_view', [str(self.user.username)])
    def as_text(self):
        return self.display_name
    @staticmethod
    def get_for(user):
        try:
            return user.get_profile()
        except UserProfile.DoesNotExist:
            return UserProfile.objects.create(user=user)
    @staticmethod
    def get_activity_for(user, max_count=50):
        return activity_for(user, max_count=50)
    def get_project_role(self, project):
        try:
            role = Group.objects.get(
                user=self.user,
                name__startswith=project.slug)
            return role.name[role.name.index('_') + 1:-1]
        except Group.DoesNotExist:
            return None
    def save(self, *args, **kwargs):
        if self.affiliation:
            project_groups = self.user.groups.filter(
                user = self.user,
                name__startswith=self.affiliation.slug)
            if len(project_groups) > 1:
                raise Exception("Only one project role allowed")
        super(UserProfile, self).save(*args, **kwargs)
        if self.affiliation and not self.get_project_role(self.affiliation):
            if self.user.groups.filter(name='Editors'):
                g = Group.objects.get(name='%s_editors' % self.affiliation.slug)
            else:
                g = Group.objects.get(name='%s_researchers' % self.affiliation.slug)
            self.user.groups.add(g)

PROJECT_ROLES = (
    ('editor', 'Editor'),
    ('researcher', 'Researcher')
)

class Project(models.Model, URLAccessible, PermissionsMixin):
    name = models.CharField(max_length='80')
    slug = models.SlugField(help_text='Used for project-specific URLs and groups')
    image = models.ImageField(upload_to='project_images', blank=True, null=True)
    description = fields.XHTMLField(blank=True, null=True)
    class Meta:
        app_label = 'main'
    @models.permalink
    def get_absolute_url(self):
        return ('project_view', [self.slug])
    def as_text(self):
        return self.name
    def has_description(self):
        return self.description is not None
    @staticmethod
    def get_affiliation_for(user, single=True):
        profile = UserProfile.get_for(user)
        qs = Project.objects.filter(members=profile)
        if single:
            qs = qs[:1]
        return qs
    @staticmethod
    def get_activity_for(project, max_count=50):
        return activity_for(project, max_count=max_count)
    def allow_view_for(self, user):
        if user.has_perm('main.%s.view_project' % self.slug) or user.is_superuser:
            return True
        else:
            return False
    def allow_change_for(self, user):
        if user.has_perm('main.%s.change_project' % self.slug) or user.is_superuser:
            return True
        else:
            return False
    def get_or_create_project_roles(self):
        base_project_permissions = (
            ('main.note', ('change', 'delete',)),
            ('main.project', ('view',)),
            ('main.document', ('change', 'delete',)),
            ('main.topic', ('change', 'delete',)),
            ('main.transcript', ('change', 'delete',)),
            ('main.footnote', ('change', 'delete',)),
        )
        editor_project_permissions = (
            ('main.project', ('change',)),
        )

        slug = self.slug
        editors, created = Group.objects.get_or_create(
            name='%s_editors' % slug)
        researchers, created = Group.objects.get_or_create(
            name='%s_researchers' % slug)

        for m, actions in base_project_permissions:
            app_label, model_name = m.split('.')
            ct = ContentType.objects.get(
                app_label=app_label, model=model_name)
            model = ct.model_class()

            for action in actions:
                perm, created = Permission.objects.get_or_create(
                    content_type=ct,
                    codename='%s.%s_%s' % (
                        slug, action, model._meta.module_name),
                    name='Can %s %s %s' % (
                        action, slug, model._meta.verbose_name_plural.lower())
                )
                editors.permissions.add(perm)
                researchers.permissions.add(perm)

        for m, actions in editor_project_permissions:
            app_label, model_name = m.split('.')
            ct = ContentType.objects.get(
                app_label=app_label, model=model_name)
            model = ct.model_class()
            for action in actions:
                perm, created = Permission.objects.get_or_create(
                    content_type=ct,
                    codename='%s.%s_%s' % (
                        slug, action, model._meta.module_name),
                    name='Can %s %s %s' % (
                        action, slug, model._meta.verbose_name_plural.lower())
                )
                editors.permissions.add(perm)
    def save(self, *args, **kwargs):
        super(Project, self).save(*args, **kwargs)
        self.get_or_create_project_roles()

class ProjectInvitation(CreationMetadata):
    class Meta:
        app_label = 'main'
    project = models.ForeignKey(Project)
    email = models.EmailField()
    role = models.CharField(
        max_length=10, choices=PROJECT_ROLES, default='researcher')
    def __unicode__(self):
        return '{} ({})'.format(self.email, self.project.name)

class FeaturedItem(CreationMetadata):
    class Meta:
        app_label = 'main'
    project = models.ForeignKey(Project)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    def __unicode__(self):
        return '(%s)-- %s' % (self.project.slug, self.content_object.__repr__())


def activity_for(model, max_count=50):
    u'''
    Return recent activity for a user or project.
    '''
    if isinstance(model, User):
        user_ids = [model.id]
    elif isinstance(model, Project):
        user_ids = [u.user_id for u in model.members.all()]
    else:
        raise TypeError(
            'Argument must either be an instance of a User or a Project')

    activity = []
    checked_object_ids = {
        'topic': [],
        'note': [],
        'document': [],
        'transcript': []
    }

    for entry in reversion.models.Version.objects\
            .select_related('content_type__name', 'revision')\
            .order_by('-revision__date_created')\
            .filter(content_type__app_label='main',
                    content_type__model__in=checked_object_ids.keys(),
                    revision__user_id__in=user_ids):
        if entry.object_id in checked_object_ids[entry.content_type.name]:
            continue
        checked_object_ids[entry.content_type.name].append(entry.object_id)
        if entry.type == reversion.models.VERSION_DELETE:
            continue
        obj = entry.object
        if obj is None:
            continue
        activity.append({
            'what': obj,
            'when': entry.revision.date_created
        })
        if len(activity) == max_count:
            break
    return activity, checked_object_ids
