# vim: set tw=0:

from django.conf.urls import patterns, url

from views.topics import LegacyTopicRedirectView

urlpatterns = patterns('editorsnotes.main.views.auth',
    url(r'^projects/$', 'all_projects', name='all_projects_view'),
    url(r'^projects/(?P<project_slug>\w+)/$', 'project', name='project_view'),
)

urlpatterns += patterns('editorsnotes.main.views.navigation',
    url(r'^browse/$', 'browse', name='browse_view'),
)

urlpatterns += patterns('editorsnotes.main.views.documents',
    url(r'^(?:projects/(?P<project_slug>\w+)/)?documents/$', 'all_documents', name='all_documents_view'),
    url(r'^projects/(?P<project_slug>\w+)/documents/(?P<document_id>\d+)/$', 'document', name='document_view'),
    url(r'^projects/(?P<project_slug>\w+)/documents/(?P<document_id>\d+)/transcript/$', 'transcript', name='transcript_view'),
    url(r'^projects/(?P<project_slug>\w+)/documents/(?P<document_id>\d+)/footnotes/(?P<footnote_id>\d+)/$', 'footnote', name='footnote_view'),
)

urlpatterns += patterns('editorsnotes.main.views.notes',
    url(r'^(?:projects/(?P<project_slug>\w+)/)?notes/$', 'all_notes', name='all_notes_view'),
    url(r'^projects/(?P<project_slug>\w+)/notes/(?P<note_id>\d+)/$', 'note', name='note_view'),
)

urlpatterns += patterns('editorsnotes.main.views.topics',
    url(r'^(?:projects/(?P<project_slug>\w+)/)?topics/$', 'all_topics', name='all_topics_view'),
    url(r'^topics/(?P<topic_node_id>\d+)/$', 'topic_node', name='topic_node_view'),
    url(r'^projects/(?P<project_slug>\w+)/topics/(?P<topic_node_id>\d+)/$', 'topic', name='topic_view'),
    url(r'^topic/(?P<topic_slug>[\w\-,]+)/$', LegacyTopicRedirectView.as_view(), name='legacy_topic_view'),
)
