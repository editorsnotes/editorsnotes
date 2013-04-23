from rest_framework import permissions
from editorsnotes.main.models.base import ProjectSpecific

class ProjectSpecificPermission(permissions.BasePermission):
    """
    Permissions for project-specific items.
    """
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, ProjectSpecific):
            # Defer to other backends.
            return True

        if request.method == 'DELETE':
            return obj.attempt('delete', request.user)
        elif request.method == 'PUT':
            return obj.attempt('change', request.user)
        else:
            # Defer to other backends.
            return True
