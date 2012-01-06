from django.contrib import admin
from django.db import models
from models import ZoteroLink
from widgets import ZoteroWidget

class ZoteroLinkAdmin(admin.ModelAdmin):
    fields = ('zotero_data',)
    formfield_overrides = {
        models.TextField : {'widget' : ZoteroWidget},
    }
    class Media:
        css = {
            'all' : ('/media/style/zotero-admin-inline.css',)
        }
        js = ('function/jquery-1.5.1.min.js',
              'function/zotero-admin-inline.js',
              'function/json2.js',)
admin.site.register(ZoteroLink, ZoteroLinkAdmin)
