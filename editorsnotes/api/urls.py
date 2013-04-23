from django.conf.urls import patterns, url
import views

urlpatterns = patterns(
    '',
    url('^$', views.root, name='api-root'),
    url('^auth-token/$', 'rest_framework.authtoken.views.obtain_auth_token', name='obtain-auth-token'),
    url('^topics/$', views.TopicList.as_view(), name='api-topics-list'),
    url('^topics/(?P<pk>\d+)/$', views.TopicDetail.as_view(), name='api-topics-detail'),
    url('^notes/$', views.NoteList.as_view(), name='api-notes-list'),
    url('^notes/(?P<pk>\d+)/$', views.NoteDetail.as_view(), name='api-notes-detail'),
    url('^notes/(?P<note_id>\d+)/s(?P<section_id>\d+)/$', views.NoteSectionDetail.as_view(), name='api-notes-section-detail'),
    url('^documents/$', views.DocumentList.as_view(), name='api-documents-list'),
    url('^documents/(?P<pk>\d+)/$', views.DocumentDetail.as_view(), name='api-documents-detail'),
)
