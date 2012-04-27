# -*- coding: utf-8 -*-

from haystack import site
from haystack.indexes import *
from django.db.models.fields import FieldDoesNotExist
from models import Document, Transcript, Footnote, Topic, Note
import json

class DocumentIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)
    project_id = MultiValueField()
    def prepare_project_id(self, obj):
        return [p.id for p in obj.get_project_affiliation()]
    def prepare(self, obj):
        self.prepared_data = super(DocumentIndex, self).prepare(obj)

        z = obj.zotero_link()
        zotero_data = json.loads(z.zotero_data) if z else {}

        if 'archive' in zotero_data and len(zotero_data['archive']):
            self.prepared_data['archive'] = zotero_data['archive']

        names = []
        if 'creators' in zotero_data and len(zotero_data['creators']):
            creators = zotero_data['creators']
            for c in creators:
                name = c.get('name') or (c.get('firstName') + ' ' +
                                         c.get('lastName')).strip().rstrip()
                names.append(name)
        self.prepared_data['creators'] = names
        return self.prepared_data
    def get_model(self):
        return Document
    def index_queryset(self):
        return self.get_model().objects.exclude(import_id__startswith='inglis')


class TranscriptIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)
    def get_model(self):
        return Transcript
    def index_queryset(self):
        return self.get_model().objects.exclude(
            document__import_id__startswith='inglis')

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
    related_topic_id = MultiValueField()
    last_updated = DateTimeField(model_attr='last_updated')
    def prepare_project_id(self, obj):
        return [p.id for p in obj.get_project_affiliation()]
    def prepare_related_topic_id(self, obj):
        return [t.topic.id for t in obj.topics.all()]

site.register(Document, DocumentIndex)
site.register(Transcript, TranscriptIndex)
site.register(Footnote, FootnoteIndex)
site.register(Topic, TopicIndex)
site.register(Note, NoteIndex)
