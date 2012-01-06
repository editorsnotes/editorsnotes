from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from models import Task
from editorsnotes.main.admin import VersionAdmin

class TaskAdmin(VersionAdmin):
    model = Task
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'assigned_users':
            kwargs['queryset'] = User.objects.filter(
                userprofile__affiliation=request.user.get_profile().affiliation)
            return super(TaskAdmin, self).formfield_for_manytomany(db_field,
                                                                   request,
                                                                   **kwargs)
    exclude = ('project',)
    filter_horizontal = ('assigned_users',)
    def save_model(self, request, obj, form, change):
        obj.project = request.user.get_profile().affiliation
        if not change:
            obj.creator = request.user
        obj.last_updater = request.user
        obj.save()

    class Media:
        css = { 'all': ('style/custom-theme/jquery-ui-1.8.10.custom.css',
                        'style/admin.css') }
        js = ('function/jquery-1.5.1.min.js',
              'function/jquery-ui-1.8.10.custom.min.js',
              'function/wymeditor/jquery.wymeditor.pack.js',
              'function/jquery.timeago.js',
              'function/admin.js')

admin.site.register(Task, TaskAdmin)
