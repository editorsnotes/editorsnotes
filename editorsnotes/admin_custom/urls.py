# -*- coding: utf-8 -*-
# vim: set tw=0:

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^$', views.projects.change_project, name='project_edit_view'),
    url(r'^roster/$', views.projects.project_roster, name='project_roster_view'),
    url(r'^featured_items/$', views.projects.change_featured_items, name='change_featured_items_view'),
    url(r'^topics/add/$', views.topics.TopicAdminView.as_view(), name='add_topic_view'),
    url(r'^topics/(?P<topic_node_id>\d+)/$', views.topics.TopicAdminView.as_view(), name='change_topic_view'),
    url(r'^documents/add/$', views.documents.DocumentAdminView.as_view(), name='add_document_view'),
    url(r'^documents/(?P<document_id>\d+)/$', views.documents.DocumentAdminView.as_view(), name='change_document_view'),
    url(r'^documents/(?P<document_id>\d+)/transcript/$', views.documents.TranscriptAdminView.as_view(), name='change_transcript_view'),
    url(r'^notes/add/$', views.notes.NoteAdminView.as_view(), name='add_note_view'),
    url(r'^notes/(?P<note_id>\d+)/$', views.notes.NoteAdminView.as_view(), name='change_note_view'),
    url(r'^notes/(?P<note_id>\d+)/sections/$', views.notes.note_sections, name='change_note_sections_view'),
)
