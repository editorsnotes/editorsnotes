from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import get_models, signals

PROJECT_PERMISSIONS_GROUP = 'Project-specific permissions'

IGNORED_PERMISSIONS = {
    'main.project': ('add_project', 'delete_project', 'change_project',)
}

def _get_project_specific_permissions(model):
    from ..models.auth import ProjectPermissionsMixin
    if not issubclass(model, ProjectPermissionsMixin):
        return []
    ct = ContentType.objects.get_for_model(model)
    auto_model_perms = _get_all_permissions(model._meta, ct)
    ignored_model_perms = IGNORED_PERMISSIONS.get(
        '{}.{}'.format(model._meta.app_label, model._meta.module_name), ())
    return [perm for perm in Permission.objects.filter(content_type=ct)
            if (perm.codename, perm.name) in auto_model_perms and
            perm.codename not in ignored_model_perms]

def _get_project_permission_group():
    group, _ = Group.objects.get_or_create(name=PROJECT_PERMISSIONS_GROUP)
    return group

def get_all_project_permissions():
    group = _get_project_permission_group()
    return group.permissions.all()

def get_all_builtin_project_permissions(models=None):
    perms = set()
    models_to_search = get_models() if models is None else models
    for model in models_to_search:
        perms.update(set([p for p in _get_project_specific_permissions(model)]))
    return perms


def update_project_permissions(*args, **kwargs):
    """
    Add project specific permissions 
    """
    models = get_models()
    if Group not in models or Permission not in models:
        # Don't try to create permission group until we know that Django's auth
        # module has been synced.
        return

    project_perm_group = _get_project_permission_group()
    existing_perms = project_perm_group.permissions.all()
    detected_perms = get_all_builtin_project_permissions(models)
    for perm in detected_perms - set(existing_perms):
        print u'Adding project-specific permission: {}.{}'.format(
            perm.content_type.app_label, perm.codename)
        project_perm_group.permissions.add(perm)
    return

signals.post_syncdb.connect(update_project_permissions)
