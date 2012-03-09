# -*- coding: utf-8 -*-

from haystack import site
from haystack.indexes import *
from django.db.models.fields import FieldDoesNotExist
from models import Document, Transcript, Footnote, Topic, Note

class DocumentIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)
    project_id = MultiValueField()
    def prepare_project_id(self, obj):
        return [p.id for p in obj.get_project_affiliation()]

class TranscriptIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)

class FootnoteIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)

class TopicIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)
    names = CharField(use_template=True)
    project_id = MultiValueField()
    def prepare_project_id(self, obj):
        return [p.id for p in obj.get_project_affiliation()]

class NoteIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)
    project_id = MultiValueField()
    def prepare_project_id(self, obj):
        return [p.id for p in obj.get_project_affiliation()]

site.register(Document, DocumentIndex)
site.register(Transcript, TranscriptIndex)
site.register(Footnote, FootnoteIndex)
site.register(Topic, TopicIndex)
site.register(Note, NoteIndex)
