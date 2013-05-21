# -*- coding: utf-8 -*-

from haystack import site
from haystack.indexes import *
from django.db.models.fields import FieldDoesNotExist
from models import Document, Transcript, Footnote, TopicNode, Note
from editorsnotes.djotero.utils import get_creator_name
import json

class DocumentIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)
    project_id = MultiValueField()
    related_topic_id = MultiValueField()
    representations = MultiValueField()

    # Zotero fields
    creators = MultiValueField()
    archive = CharField()
    itemType = CharField()
    publicationTitle = CharField()
    def prepare_project_id(self, obj):
        return [p.id for p in obj.get_project_affiliation()]
    def prepare_related_topic_id(self, obj):
        return [t.id for t in obj.get_all_related_topics()]
    def prepare_representations(self, obj):
        return [r for r in obj.get_all_representations()]
    def prepare(self, obj):
        self.prepared_data = super(DocumentIndex, self).prepare(obj)

        z = obj.zotero_link()
        zotero_data = json.loads(z.zotero_data) if z else {}
        fields_to_index = ['archive', 'publicationTitle', 'itemType']

        for field in fields_to_index:
            if zotero_data.get(field):
                self.prepared_data[field] = zotero_data[field]

        names = []
        if zotero_data.get('creators'):
            for c in zotero_data['creators']:
                creator = get_creator_name(c)
                names.append(creator)
        self.prepared_data['creators'] = [n for n in names if n]

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
        return [p.id for p in obj.get_connected_projects()]

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

#site.register(Document, DocumentIndex)
#site.register(Transcript, TranscriptIndex)
#site.register(Footnote, FootnoteIndex)
#site.register(TopicNode, TopicIndex)
#site.register(Note, NoteIndex)
