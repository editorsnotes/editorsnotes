from django.core.management.base import BaseCommand
from .. import get_all_builtin_project_permissions, _get_project_permission_group
from editorsnotes.main.models.auth import ProjectRole

class Command(BaseCommand):
    help = 'Delete project-specific permissions which aren\'t automatically generated.'
    def handle(self, *args, **kwargs):
        base_group = _get_project_permission_group()

        builtin_perms = get_all_builtin_project_permissions()
        existing_perms = set(base_group.permissions.all())

        stale_perms = existing_perms - builtin_perms
        for perm in stale_perms:
            self.stdout.write('Removing stale permission: {}.{}'.format(
                perm.content_type.app_label, perm.codename))

        base_group.permissions.remove(*stale_perms)
        stale_roles = ProjectRole.objects\
                .select_related('group__permissions')\
                .filter(group__permissions__in=stale_perms)
        for role in stale_roles:
            role.group.remove(*stale_perms)
        return
