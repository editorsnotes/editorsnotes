# -*- coding: utf-8 -*-

from collections import Counter

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, Group, PermissionsMixin)
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

import reversion
from licensing.models import License

from editorsnotes.main.management import get_all_project_permissions
from editorsnotes.main.models.base import (URLAccessible, CreationMetadata,
                                           ENMarkup)


__all__ = [
    'User',
    'Project',
    'ProjectRole',
    'ProjectInvitation',
    'FeaturedItem',
    'LogActivity',
    'RevisionLogActivity',

    'UpdatersMixin',
    'ProjectPermissionsMixin'
]


class UserManager(BaseUserManager):
    def create_user(self, email, display_name, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            display_name=display_name)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, display_name, password):
        user = self.create_user(email, display_name, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin, URLAccessible):
    objects = UserManager()

    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True)
    display_name = models.CharField(
        help_text='Display name for a user',
        max_length=200)

    date_joined = models.DateTimeField(
        'date joined',
        default=timezone.now)

    # separate from is_active because they are semantically different. Django
    # suggests that is_active should be used as a way to make someone's account
    # "inactive" without deleting it (which would ruin foreign keys, etc.)
    is_active = models.BooleanField(default=True)
    is_confirmed = models.BooleanField(default=False)

    # TODO: should this be EN markup?
    profile = models.CharField(
        help_text='Profile text for a user.',
        max_length=1000,
        blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']

    class Meta:
        app_label = 'main'

    @models.permalink
    def get_absolute_url(self):
        return ('api:users-detail', [str(self.username)])

    def __unicode__(self):
        return self.display_name

    def as_text(self):
        return self.display_name

    #####################################################
    # Properties required for custom Django user models #
    #####################################################
    def get_full_name(self):
        return self.display_name

    def get_short_name(self):
        return self.display_name

    ###################################
    # Properties relating to projects #
    ###################################
    def belongs_to(self, project):
        return project.get_role_for(self) is not None

    def get_affiliated_projects(self):
        return Project.objects.filter(roles__group__user=self)

    def get_affiliated_projects_with_roles(self):
        roles = ProjectRole.objects.filter(group__user=self)
        return [(role.project, role) for role in roles]

    def _get_project_role(self, project):
        role_attr = '_{}_role_cache'.format(project.slug)
        if not hasattr(self, role_attr):
            setattr(self, role_attr, project.get_role_for(self))
        return getattr(self, role_attr)

    def get_project_permission_objects(self, project):
        """
        Get all of a user's permissions within a project.

        I thought about implementing this in an authentication backend, where a
        perm would be `{projectslug}-{app}.{perm}` instead of the typical
        `{app}.{perm}`, but this is more explicit. If we ever decide to roll
        this UserProfile into a custom User model, it would make sense to move
        this method to a custom backend.
        """
        role = self._get_project_role(project)
        if self.is_superuser or (role is not None and role.is_super_role):
            perm_list = get_all_project_permissions()
        elif role is None:
            perm_list = []
        else:
            perm_list = role.get_permissions()

        return perm_list

    def _get_project_permissions(self, project):
        return {
            '{}.{}'.format(perm.content_type.app_label, perm.codename)
            for perm in self.get_project_permission_objects(project)
        }

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
        return perm in self.get_project_permissions(project)

    def has_project_perms(self, project, perm_list):
        return all(self.has_project_perm(project, p) for p in perm_list)


class UpdatersMixin(object):
    """
    Mixin with method for determining all updaters of a model.
    """
    def get_all_updaters(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        qs = reversion.models.Revision.objects\
            .select_related('user')\
            .filter(version__content_type_id=ct.id,
                    version__object_id_int=self.id)
        user_counter = Counter([revision.user for revision in qs])
        return [user for user, count in user_counter.most_common()]


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
            'Must define get_affiliation method which returns the project for'
            ' this model.'
        )


class ProjectManager(models.Manager):
    def for_user(self, user):
        return self.select_related('roles__group__user')\
            .filter(roles__group__user=user)


class Project(ENMarkup, models.Model, URLAccessible, ProjectPermissionsMixin):
    name = models.CharField(
        max_length='80',
        help_text='The name of the project.'
    )

    slug = models.SlugField(
        help_text=(
            'Used for project-specific URLs and groups. '
            'Valid characters: letters, numbers, or _-'
        ),
        unique=True
    )

    image = models.ImageField(
        'An image representing this project.',
        upload_to='project_images',
        blank=True,
        null=True
    )
    default_license = models.ForeignKey(
        License,
        default=1,
        help_text=(
            'Default license for project notes. '
            'Licenses can also be set on a note-by-note basis.'
        )
    )
    objects = ProjectManager()

    class Meta:
        app_label = 'main'
        permissions = (
            (u'view_project_roster', u'Can view project roster.'),
            (u'change_project_roster', u'Can edit project roster.'),
        )

    @models.permalink
    def get_absolute_url(self):
        return ('api:projects-detail', [self.slug])

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

    def members_by_role(self):
        roles = ProjectRole.objects.for_project(self).select_related('user')
        return roles

    def get_role_for(self, user):
        qs = self.roles.filter(group__user=user)
        return qs.get() if qs.exists() else None


@receiver(models.signals.post_save, sender=Project)
def create_editor_role(sender, instance, created, **kwargs):
    "Creates an editor role after a project has been created."

    # Only create role if this is a newly created project, and it is not being
    # loaded from a fixture (in that case, "raw" is true in kwargs)
    if created and not kwargs.get('raw', False):
        instance.roles.get_or_create_by_name('Editor', is_super_role=True)
    return


##################################
# Supporting models for projects #
##################################
def called_from_project(func):
    """
    Wrapper for ProjectRoleManager methods meant to be called from a project.
    """
    def wrapped(self, *args, **kwargs):
        if not isinstance(getattr(self, 'instance', None), Project):
            raise AttributeError('Method only accessible via a project '
                                 'instance.')
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

        kwargs are only used in creating a project; lookup is by role name
        only.
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

    Roles should be typically be created and accessed through project
    instances, e.g. `project.roles.get_or_create_by_name('editor')`
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

    def delete(self, *args, **kwargs):
        group = self.group
        ret = super(ProjectRole, self).delete(*args, **kwargs)
        group.delete()
        return ret

    def get_permissions(self):
        if self.is_super_role:
            return self._get_valid_permissions()
        else:
            return set(self.group.permissions.all())

    def add_permissions(self, *perms):
        for perm in perms:
            if perm not in self._get_valid_permissions():
                raise ValueError(
                    '{} is not a valid project-specific permission.'.format(
                        perm
                    )
                )
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
    project_role = models.ForeignKey(ProjectRole)

    def __unicode__(self):
        return '{} ({})'.format(self.email, self.project.name)


class FeaturedItem(CreationMetadata, ProjectPermissionsMixin):
    class Meta:
        app_label = 'main'
    project = models.ForeignKey(Project)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __unicode__(self):
        return u'({})-- {}'.format(
            self.project.slug,
            self.content_object.__repr__()
        )

    def get_affiliation(self):
        return self.project


class RevisionProject(models.Model):
    revision = models.OneToOneField(reversion.models.Revision,
                                    related_name='project_metadata')
    project = models.ForeignKey(Project)

    # If a project is deleted, so is this. Should this be changed? Should we
    # not allow projects to be deleted?
    class Meta:
        app_label = 'main'

ADDITION = 0
CHANGE = 1
DELETION = 2


class LogActivity(models.Model):
    """
    Like django.contrib.admin.models.LogEntry, but with URL and project
    """
    time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    project = models.ForeignKey(Project)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    display_title = models.CharField(max_length=300)

    action = models.IntegerField()
    message = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'main'
        ordering = ('-time',)

    def is_addition(self):
        return self.action == ADDITION

    def is_change(self):
        return self.action == CHANGE

    def is_deletion(self):
        return self.action == DELETION

    def get_version(self):
        if self.revision_metadata is None:
            return None
        return self.revision_metadata.revision.version_set\
            .get(content_type_id=self.content_type_id,
                 object_id=self.object_id)


class RevisionLogActivity(models.Model):
    revision = models.ForeignKey(
        reversion.models.Revision, related_name='logactivity_metadata')
    log_activity = models.OneToOneField(
        LogActivity, related_name='revision_metadata')

    class Meta:
        app_label = 'main'
