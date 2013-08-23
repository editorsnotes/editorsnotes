# -*- coding: utf-8 -*-

import json

from haystack import site
from haystack.indexes import (
    RealTimeSearchIndex, CharField, DateTimeField, MultiValueField)

from editorsnotes.djotero.utils import get_creator_name

from models.documents import Document, Footnote, Transcript
from models.notes import Note
from models.topics import TopicNode

class DocumentIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)
    project = CharField(model_attr='project')
    project_slug = MultiValueField(faceted=True)

    related_topic_id = MultiValueField(faceted=True)
    representations = MultiValueField(faceted=True)

    # Zotero fields
    creators = MultiValueField(faceted=True)
    archive = CharField(faceted=True)
    itemType = CharField(faceted=True)
    publicationTitle = CharField(faceted=True)
    def prepare_related_topic_id(self, obj):
        return [t.id for t in obj.get_all_related_topics()]
    def prepare_representations(self, obj):
        return [r for r in obj.get_all_representations()]
    def prepare_project_slug(self, obj):
        return [obj.project.slug]
    def prepare(self, obj):
        self.prepared_data = super(DocumentIndex, self).prepare(obj)

        if obj.zotero_data is None:
            return self.prepared_data

        zotero_data = json.loads(obj.zotero_data)
        for field in ['archive', 'publicationTitle', 'itemType']:
            if field in zotero_data:
                self.prepared_data[field] = zotero_data[field]
            elif field == 'itemType':
                self.prepared_data[field] = 'none'

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
    project = MultiValueField()
    project_slug = MultiValueField(faceted=True)
    related_topic_id = MultiValueField(faceted=True)
    def prepare_project(self, obj):
        return [pc.project.name for pc in obj.project_containers.all()]
    def prepare_project_slug(self, obj):
        return [pc.project.slug for pc in obj.project_containers.all()]
    def prepare_related_topic_id(self, obj):
        return [ta.id for ta in obj.related_objects(model=TopicNode)]
    def index_queryset(self):
        return self.model.objects.select_related('project_containers__project')

class NoteIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)
    project = CharField(model_attr='project')
    project_slug = MultiValueField(faceted=True)
    related_topic_id = MultiValueField(faceted=True)
    last_updated = DateTimeField(model_attr='last_updated')
    def prepare_project_slug(self, obj):
        return [obj.project.slug]
    def prepare_related_topic_id(self, obj):
        return [t.topic.id for t in obj.topics.all()]
    def index_queryset(self):
        return self.model.objects.select_related('project')

site.register(Document, DocumentIndex)
site.register(Transcript, TranscriptIndex)
site.register(Footnote, FootnoteIndex)
site.register(TopicNode, TopicIndex)
site.register(Note, NoteIndex)
