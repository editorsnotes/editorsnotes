# vim: set tw=0:

from django.conf.urls import patterns, url, include
import views

project_specific_patterns = patterns('',
    url(r'^topics/$', views.TopicList.as_view(), name='api-topics-list'),
    url(r'^topics/(?P<topic_node_id>\d+)/$', views.TopicDetail.as_view(), name='api-topics-detail'),
    url(r'^notes/$', views.NoteList.as_view(), name='api-notes-list'),
    url(r'^notes/(?P<pk>\d+)/$', views.NoteDetail.as_view(), name='api-notes-detail'),
    url(r'^notes/(?P<note_id>\d+)/s(?P<section_id>\d+)/$', views.NoteSectionDetail.as_view(), name='api-notes-section-detail'),
    url(r'^documents/$', views.DocumentList.as_view(), name='api-documents-list'),
    url(r'^documents/(?P<pk>\d+)/$', views.DocumentDetail.as_view(), name='api-documents-detail'),
)

urlpatterns = patterns('',
    url(r'^$', views.base.root, name='api-root'),
    url(r'^auth-token/$', 'rest_framework.authtoken.views.obtain_auth_token', name='obtain-auth-token'),
    url(r'^projects/(?P<project_slug>\w+)/', include(project_specific_patterns)),
    url(r'^search/$', views.SearchView.as_view(), name='api-search')
)
