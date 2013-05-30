# -*- coding: utf-8 -*-
# vim: set tw=0:

from django.conf.urls import patterns, url

import .views

list_patterns = patterns('views',
    url(r'^browse/$', 'browse', name='browse_view'),
    url(r'^projects/$', 'all_projects', name='all_projects_view'),
    url(r'^documents/$', 'all_documents', name='all_documents_view'),
    url(r'^topics/$', 'all_topics', name='all_topics_view'),
    url(r'^notes/$', 'all_notes', name='all_notes_view'),
)

project_list_patterns = patterns(
    url(r'^projects/(?P<project_slug>\w+)/documents/$', 'project_documents', name='project_documents_view'),
    url(r'^projects/(?P<project_slug>\w+)/topics/$', 'project_topics', name='project_topics_view'),
    url(r'^projects/(?P<project_slug>\w+)/notes/$', 'project_notes', name='project_notes_view'),
)

project_item_patterns = patterns(
    url(r'^projects/(?P<project_slug\w+)/$', 'project', name='project_view'),

    url(r'^projects/(?P<project_slug\w+)/documents/(?<document_id>\d+)/$', 'document', name='document_view'),
    url(r'^projects/(?P<project_slug\w+)/documents/(?<document_id>\d+)/transcript/$', 'transcript', name='transcript_view'),
    url(r'^projects/(?P<project_slug\w+)/documents/(?<document_id>\d+)/footnotes/(?P<footnote_id>\d+)/$', 'footnote', name='footnote_view'),

    url(r'^projects/(?P<project_slug\w+)/topics/(?<topic_node_id>\d+)/$', 'project_topic', name='project_topic_view'),

    url(r'^projects/(?P<project_slug\w+)/notes/(?<note_id>\d+)/$', 'note', name='note_view'),
)

urlpatterns = list_patterns + project_list_patterns + project_item_patterns
