# vim: set tw=0:

from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'edit/^$', views.projects.change_project, name='main_project_change'),
    url(r'^roster/$', views.projects.project_roster, name='main_project_roster_change'),
    url(r'^featured_items/$', views.projects.change_featured_items, name='main_featured_items_change'),
    url(r'^topics/add/$', views.topics.TopicAdminView.as_view(), name='main_topic_add'),
    url(r'^topics/(?P<topic_node_id>\d+)/edit/$', views.topics.TopicAdminView.as_view(), name='main_topic_change'),
    url(r'^documents/add/$', views.documents.DocumentAdminView.as_view(), name='main_document_add'),
    url(r'^documents/(?P<document_id>\d+)/edit/$', views.documents.DocumentAdminView.as_view(), name='main_document_change'),
    url(r'^documents/(?P<document_id>\d+)/transcript/edit/$', views.documents.TranscriptAdminView.as_view(), name='main_transcript_add_or_change'),
    url(r'^notes/add/$', views.notes.NoteAdminView.as_view(), name='main_note_add'),
    url(r'^notes/(?P<note_id>\d+)/edit/$', views.notes.NoteAdminView.as_view(), name='main_note_change'),
    url(r'^notes/(?P<note_id>\d+)/sections/$', views.notes.note_sections, name='main_note_sections_change'),
)
