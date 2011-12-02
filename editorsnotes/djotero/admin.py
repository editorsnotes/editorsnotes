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
        js = ('/media/function/zotero-admin-inline.js',)
admin.site.register(ZoteroLink, ZoteroLinkAdmin)
