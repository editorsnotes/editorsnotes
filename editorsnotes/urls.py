# -*- coding: utf-8 -*-
# vim: set tw=0:

from django.conf.urls import patterns, url, include
from django.conf import settings
from django.views.generic.base import RedirectView
from editorsnotes.main.views import CustomBrowserIDVerify, LegacyTopicRedirectView

# These will be intercepted by apache in production
urlpatterns = patterns('',
    (r'^favicon.ico$', RedirectView.as_view(url='/static/style/icons/favicon.ico')),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.MEDIA_ROOT }),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT }),
    (r'^proxy$', 'editorsnotes.main.views.proxy'),
)

# Auth patterns
urlpatterns += patterns('',
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/logout/$', 'user_logout', name='user_logout_view'),
    url(r'^accounts/profile/$', 'editorsnotes.main.views.user'),
    url(r'^accounts/browserid/$', CustomBrowserIDVerify.as_view(), name='browserid_verify'),
    url(r'^user/(?P<username>[\w@\+\.\-]+)/$', 'user', name='user_view'),
)

# Base patterns
urlpatterns += patterns('editorsnotes.main.views',
    url(r'^$', 'index', name='index_view'),
    url(r'^about/$', 'about', name='about_view'),
    url(r'^about/test/$', 'about_test'),
    url(r'^search/$', 'search', name='search_view'),
    url(r'^topic/(?P<topic_slug>[\w\-,]+)/$', LegacyTopicRedirectView.as_view(), name='topic_view'),
)

# Admin patterns
urlpatterns += patterns('',
    url(r'^projects/(?P<project_slug>\w+)/', include('editorsnotes.admin_custom.urls')),
)

# Main model patterns
urlpatterns += patterns('',
    url(r'^', include('editorsnotes.main.urls')),
)

#urlpatterns += patterns('editorsnotes.djotero.views',
#    url(r'^document/upload/$', 'import_zotero', name='import_zotero_view'),
#    url(r'^document/upload/libraries/$', 'libraries', name='libraries_view'),
#    url(r'^document/upload/collections/$', 'collections', name='collections_view'),
#    url(r'^document/upload/items/$', 'items', name='items_view'),
#    url(r'^document/upload/continue/$', 'items_continue', name='items_continue_view'),
#    url(r'^document/upload/import/$', 'import_items', name='import_items_view'),
#    url(r'^user/zotero_info$', 'update_zotero_info', name='update_zotero_info_view'),
#    url(r'^api/document/template/', 'zotero_template'),
#    url(r'^api/document/blank/$', 'get_blank_item', name='get_blank_item_view'),
#    url(r'^api/document/csl/$', 'zotero_json_to_csl', name='zotero_json_to_csl_view'),
#    url(r'^api/document/archives/$', 'api_archives', name='api_archives_view'),
#)
#urlpatterns += patterns('editorsnotes.refine.views',
#    url(r'^topics/clusters/$', 'show_topic_clusters', name='show_topic_clusters_view'),
#    url(r'^topics/merge/(?P<cluster_id>\d+)/$', 'merge_topic_cluster', name='merge_topic_cluster_view'),
#)
