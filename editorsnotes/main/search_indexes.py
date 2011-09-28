# -*- coding: utf-8 -*-

from haystack import site
from haystack.indexes import *
from models import Document, Transcript, Footnote, Topic, Note

class DocumentIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)

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

class NoteIndex(RealTimeSearchIndex):
    title = CharField(model_attr='as_text')
    text = CharField(document=True, use_template=True)


site.register(Document, DocumentIndex)
site.register(Transcript, TranscriptIndex)
site.register(Footnote, FootnoteIndex)
site.register(Topic, TopicIndex)
site.register(Note, NoteIndex)
