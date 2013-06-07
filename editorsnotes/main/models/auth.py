# -*- coding: utf-8 -*-

from django.contrib.auth.models import AbstractUser, Group
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

import reversion

from .. import fields
from ..management import get_all_project_permissions
from base import URLAccessible, CreationMetadata

class User(AbstractUser, URLAccessible):
    zotero_key = models.CharField(max_length='24', blank=True, null=True)
    zotero_uid = models.CharField(max_length='6', blank=True, null=True)
    class Meta:
        app_label = 'main'
    def _get_display_name(self):
        "Returns the full name if available, or the username if not."
        display_name = self.username
        if self.first_name:
            display_name = self.first_name
            if self.last_name:
                display_name = '%s %s' % (self.first_name, self.last_name)
        return display_name
    display_name = property(_get_display_name)
    @models.permalink
    def get_absolute_url(self):
        return ('user_view', [str(self.username)])
    def as_text(self):
        return self.display_name
    def belongs_to(self, project):
        return project.get_role_for(self) is not None
    def get_affiliated_projects(self):
        return Project.objects.filter(roles__group__user=self)
    def get_affiliated_projects_with_roles(self):
        roles = ProjectRole.objects.filter(group__user=self)
        return [(role.project, role) for role in roles]
    def _get_project_role(self, project):
        role_attr = '_{}_role_cache'
        if not hasattr(self, role_attr):
            setattr(self, role_attr, project.get_role_for(self))
        return getattr(self, role_attr)
    def _get_project_permissions(self, project):
        """
        Get all of a user's permissions within a project.

        I thought about implementing this in an authentication backend, where a
        perm would be `{projectslug}-{app}.{perm}` instead of the typical
        `{app}.{perm}`, but this is more explicit. If we ever decide to role
        this UserProfile into a custom User model, it would make sense to move
        this method to a custom backend.
        """
        role = self._get_project_role(project)
        if self.is_superuser or role.is_super_role:
            perm_list = get_all_project_permissions()
        elif role is None:
            perm_list = []
        else:
            perm_list = role.get_permissions()
        return set(['{}.{}'.format(perm.content_type.app_label, perm.codename)
                    for perm in perm_list])
    def get_project_permissions(self, project):
        perms_attr = '_{}_permissions_cache'.format(project.slug)
        if not hasattr(self, perms_attr):
            setattr(self, perms_attr, self._get_project_permissions(project))
        return getattr(self, perms_attr)
    def has_project_perm(self, project, perm):
        """
        Returns whether a user has a permission within a project.

        Perm argument should be a string consistent with how Django handles
        permissions in its admin: `{app_label}.{permission.codename}`
        """
        if self.is_superuser:
            return True
        role = self._get_project_role(project)
        if role.is_super_role:
            return True
        return perm in self.get_project_permissions(project)
    def has_project_perms(self, project, perm_list):
        return all(self.has_project_perm(project, p) for p in perm_list)
    @staticmethod
    def get_activity_for(user, max_count=50):
        return activity_for(user, max_count=50)

class ProjectPermissionsMixin(object):
    """
    A mixin for objects which are meant to have an affiliated project.

    If a model inherits from this class, project-specific permissions will
    automatically be handled for it. This includes Django's default permissions
    (add, change, delete), as well as any custom permissions.

    Inheriting models must implement a get_affiliation method that returns
    objects' affiliated project.
    """
    def get_affiliation(self):
        raise NotImplementedError(
            'Must define get_affiliation method which returns the project for this model.')

class ProjectManager(models.Manager):
    def for_user(self, user):
        return self.select_related('roles__group__user')\
                .filter(roles__group__user=user)

class Project(models.Model, URLAccessible, ProjectPermissionsMixin):
    name = models.CharField(max_length='80')
    slug = models.SlugField(help_text='Used for project-specific URLs and groups')
    image = models.ImageField(upload_to='project_images', blank=True, null=True)
    description = fields.XHTMLField(blank=True, null=True)
    objects = ProjectManager()
    class Meta:
        app_label = 'main'
        permissions = (
            (u'view_roster', u'Can view project roster.'),
            (u'edit_roster', u'Can edit project roster.'),
        )
    @models.permalink
    def get_absolute_url(self):
        return ('project_view', [self.slug])
    def get_affiliation(self):
        return self
    def as_text(self):
        return self.name
    def has_description(self):
        return self.description is not None
    @property
    def members(self):
        role_groups = self.roles.values_list('group_id', flat=True)
        return User.objects.filter(groups__in=role_groups)
    def get_role_for(self, user):
        qs = self.roles.filter(group__user=user)
        return qs.get() if qs.exists() else None
    @staticmethod
    def get_activity_for(project, max_count=50):
        return activity_for(project, max_count=max_count)


##################################
# Supporting models for projects #
##################################
def called_from_project(func):
    """
    Wrapper for ProjectRoleManager methods meant to be called from a project.
    """
    def wrapped(self, *args, **kwargs):
        if not isinstance(getattr(self, 'instance', None), Project):
            raise AttributeError('Method only accessible via a project instance.')
        return func(self, *args, **kwargs)
    return wrapped

class ProjectRoleManager(models.Manager):
    use_for_related_field = True
    def create_project_role(self, project, role, **kwargs):
        """
        Create a project role & related group by the role name.
        """
        group_name = u'{}-{}'.format(project.slug, role)
        role_group = Group.objects.create(name=group_name)
        return self.create(project=project, role=role, group=role_group,
                           **kwargs)
    def for_project(self, project):
        return self.filter(project=project)
    @called_from_project
    def get_or_create_by_name(self, role, **kwargs):
        """
        Get or create a project role by role name. Only callable from Projects.

        kwargs are only used in creating a project; lookup is by role name only.
        """
        project = self.instance
        try:
            role = self.get(project=project, role=role)
        except ProjectRole.DoesNotExist:
            role = self.create_project_role(project, role, **kwargs)
        return role
    @called_from_project
    def clear_for_user(self, user):
        """
        Clear all role assignments for a user. Only callable from Projects.
        """
        project_group_ids = self.values_list('group_id')
        assigned_groups = user.groups.filter(id__in=project_group_ids)
        user.groups.remove(*assigned_groups)
        return
    @called_from_project
    def get_for_user(self, user):
        qs = self.for_project(self.instance)\
                .select_related()\
                .filter(group__user=user)
        return qs.get() if qs.exists() else None

class ProjectRole(models.Model):
    """
    A container for project members for use with project-level permissions.

    Basically an augmented version of django's Group model from contrib.auth,
    but only related to a group via a one-to-one relationship instead of
    replacing the model entirely.

    A "super_role" role will have all permissions possible inside a project.
    Other roles can have permissions assigned through the project group.

    Roles should be typically be created and accessed through project instances,
    e.g. `project.roles.get_or_create_by_name('editor')`
    """
    project = models.ForeignKey(Project, related_name='roles')
    is_super_role = models.BooleanField(default=False)
    role = models.CharField(max_length=40)
    group = models.OneToOneField(Group)
    objects = ProjectRoleManager()
    class Meta:
        app_label = 'main'
        unique_together = ('project', 'role',)
    def __unicode__(self):
        return u'{} - {}'.format(self.project.name, self.role)
    def _get_valid_permissions(self):
        if not hasattr(self, '_valid_permissions_cache'):
            self._valid_permissions_cache = get_all_project_permissions()
        return self._valid_permissions_cache
    def get_permissions(self):
        if self.is_super_role:
            return self._get_valid_permissions()
        else:
            return set(self.group.permissions.all())
    def add_permissions(self, *perms):
        for perm in perms:
            if perm not in self._get_valid_permissions():
                raise ValueError(
                    '{} is not a valid project-specific permission.'.format(perm))
            self.group.permissions.add(perm)
        return
    def remove_permissions(self, *perms):
        for perm in perms:
            self.group.permissions.remove(perm)
        return
    def clear_permissions(self):
        self.group.permissions.clear()
        return
    @property
    def users(self):
        return self.group.user_set

class ProjectInvitation(CreationMetadata):
    class Meta:
        app_label = 'main'
    project = models.ForeignKey(Project)
    email = models.EmailField()
    role = models.CharField(max_length=10)
    def __unicode__(self):
        return '{} ({})'.format(self.email, self.project.name)

class FeaturedItem(CreationMetadata, ProjectPermissionsMixin):
    class Meta:
        app_label = 'main'
    project = models.ForeignKey(Project)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    def __unicode__(self):
        return u'(%s)-- %s' % (self.project.slug, self.content_object.__repr__())
    def get_affiliation(self):
        return self.project


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
