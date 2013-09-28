from rest_framework.permissions import DjangoModelPermissions, SAFE_METHODS

class ProjectSpecificPermissions(DjangoModelPermissions):
    """
    Permissions for project-specific items.
    """
    def get_view_permissions(self, request, view):
        """
        Allow views to explicitly define what permissions hsould be checked,
        otherwise determine permissions as in DjangoModelPermissions.

        Custom view permissions should be defined as a dictionary with http
        methods as keys, e.g.:

        class MyView(SomeRestFrameworkView):
            permissions_classes = (ProjectSpecificPermissions,)
            permissions = {'POST': ('foo.do_x', 'bar.do_y',),
                           'DELETE': ('baz.delete_z',)}

        """
        if hasattr(view, 'permissions') and request.method in view.permissions:
            return view.permissions.get(request.method)

        # Unfortunately, this has to be copied over instead of hooked into.
        model_cls = getattr(view, 'model', None)
        queryset = getattr(view, 'queryset', None)
        if model_cls is None and queryset is not None:
            model_cls = queryset.model

        assert model_cls, ('Cannot apply DjangoModelPermissions on a view that'
                           ' does not have `.model` or `.queryset` property.')

        return self.get_required_permissions(request.method, model_cls)

    def has_permission(self, request, view):

        perms = self.get_view_permissions(request, view)

        if request.method in SAFE_METHODS and not perms:
            return True

        # request.project must be set
        if request.user and request.user.is_authenticated():
            return request.user.has_project_perms(request.project, perms)

        return False
