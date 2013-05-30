# -*- coding: utf-8 -*-
# vim: set tw=0:

from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^$', views.change_project, name='project_edit_view'),
    url(r'^roster/$', views.project_roster, name='project_roster_view'),
    url(r'^featured_items/$', views.change_featured_items, name='change_featured_items_view'),
    url(r'^topics/add/$', views.TopicAdminView.as_view(), name='add_topic_view'),
    url(r'^topics/(?P<topic_node_id>\d+)/$', views.TopicAdminView.as_view(), name='change_topic_view'),
    url(r'^documents/add/$', views.DocumentAdminView.as_view(), name='add_document_view'),
    url(r'^documents/(?P<document_id>\d+)/$', views.DocumentAdminView.as_view(), name='change_document_view'),
    url(r'^documents/(?P<document_id>\d+)/transcript/$', views.TranscriptAdminView.as_view(), name='change_transcript_view'),
    url(r'^notes/add/$', views.NoteAdminView.as_view(), name='add_note_view'),
    url(r'^notes/(?P<note_id>\d+)/$', views.NoteAdminView.as_view(), name='change_note_view'),
    url(r'^notes/(?P<note_id>\d+)/sections/$', views.note_sections, name='change_note_sections_view'),
)
