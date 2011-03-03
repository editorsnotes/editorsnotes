from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/profile/$', 'editorsnotes.main.views.user'),
    (r'^admin/', include(admin.site.urls)),
    (r'^comments/', include('django.contrib.comments.urls')),

    # The following won't actually be called in production, since Apache will intercept them.
    (r'^favicon.ico$', 'django.views.generic.simple.redirect_to', 
     { 'url': '/media/style/icons/favicon.ico' }),
    (r'^media/scans/(?P<path>.*)$', 'django.views.static.serve',
     { 'document_root': '/home/patrick/Code/editorsnotes/uploads/scans' }),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     { 'document_root': '/home/patrick/Code/editorsnotes/editorsnotes/static' }),
    (r'^proxy$', 'editorsnotes.main.views.proxy'),
)
urlpatterns += patterns('editorsnotes.main.views',
    url(r'^document/(?P<document_id>\d+)/$', 'document', name='document_view'),
    url(r'^topic/(?P<topic_slug>[-a-z0-9]+)/$', 'topic', name='topic_view'),
    url(r'^note/(?P<note_id>\d+)/$', 'note', name='note_view'),
    url(r'^user/(?P<username>[\w@\+\.\-]+)/$', 'user', name='user_view'),
    url(r'^footnote/(?P<footnote_id>\d+)/$', 'footnote', name='footnote_view'),
    url(r'^search/$', 'search', name='search_view'),
    url(r'^api/topics/$', 'api_topics', name='api_topics_view'),
    url(r'^api/topics/(?P<topic_ids>\d+(,\d+)*)/$', 'api_topic', name='api_topic_view'),
    url(r'^api/documents/$', 'api_documents', name='api_documents_view'),
    url(r'^api/documents/(?P<document_id>\d+)/$', 'api_document', name='api_document_view'),
    url(r'^api/transcripts/$', 'api_transcripts', name='api_transcripts_view'),
    url(r'^api/transcripts/(?P<transcript_id>\d+)/$', 'api_transcript', name='api_transcript_view'),
)
index_patterns = patterns('editorsnotes.main.views',
    url(r'^$', 'index', name='index_view'),
    url(r'^documents/$', 'all_documents', name='all_documents_view'),
    url(r'^topics/$', 'all_topics', name='all_topics_view'),
    url(r'^notes/$', 'all_notes', name='all_notes_view'),
)
urlpatterns += index_patterns
urlpatterns += patterns('',
    (r'^(?P<project_slug>[-_a-z0-9]+)/', include(index_patterns)),
)
