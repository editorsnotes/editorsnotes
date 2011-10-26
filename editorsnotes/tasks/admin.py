from models import Task, Comment
from django.contrib import admin
from editorsnotes.main.admin import VersionAdmin

class CommentInline(admin.StackedInline):
    model = Comment
    extra = 1

class TaskAdmin(VersionAdmin):
    inlines = [CommentInline]
    class Media:
        css = { 'all': ('style/custom-theme/jquery-ui-1.8.10.custom.css',
                        'style/admin.css') }
        js = ('function/jquery-1.5.1.min.js',
              'function/jquery-ui-1.8.10.custom.min.js',
              'function/wymeditor/jquery.wymeditor.pack.js',
              'function/jquery.timeago.js',
              'function/admin.js')

admin.site.register(Task, TaskAdmin)
