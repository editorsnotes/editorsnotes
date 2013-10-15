from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from editorsnotes.api.serializers import TopicSerializer
from editorsnotes.main import models as main_models

from .index import ENIndex
from .types import DocumentTypeAdapter

class DocumentAdapter(DocumentTypeAdapter):
    display_field = 'serialized.description'
    highlight_fields = ('serialized.description',)
    def get_mapping(self):
        mapping = super(DocumentAdapter, self).get_mapping()
        mapping[self.type_label]['properties']['serialized']['properties'].update({
            'zotero_data': {
                'properties': {
                    'itemType': {'type': 'string', 'index': 'not_analyzed'},
                    'publicationTitle': {'type': 'string', 'index': 'not_analyzed'},
                    'archive': {'type': 'string', 'index': 'not_analyzed'},
                }
            }
        })
        return mapping

class TopicAdapter(DocumentTypeAdapter):
    type_label = 'topic'
    display_field = 'serialized.preferred_name'
    highlight_fields = ('serialized.preferred_name',
                        'serialized.summary')
    def get_mapping(self):
        mapping = super(TopicAdapter, self).get_mapping()
        return mapping
    def get_serializer(self):
        return TopicSerializer

en_index = ENIndex()
en_index.register(main_models.Note,
                  display_field='serialized.title',
                  highlight_fields=('serialized.title',
                                    'serialized.content',
                                    'serialized.sections'))
en_index.register(main_models.Document,
                  adapter=DocumentAdapter)
en_index.register(main_models.topics.ProjectTopicContainer,
                  adapter=TopicAdapter)

@receiver(post_save)
def update_elastic_search_handler(sender, instance, created, **kwargs):
    klass = instance.__class__
    if klass in en_index.document_types:
        document_type = en_index.document_types[klass]
        if created:
            document_type.index(instance)
        else:
            document_type.update(instance)
    elif isinstance(klass, main_models.notes.NoteSection):
        update_elastic_search_handler(sender, instance.note, False)

@receiver(post_delete)
def delete_es_document_handler(sender, instance, **kwargs):
    klass = instance.__class__
    if klass in en_index.document_types:
        document_type = en_index.document_types[klass]
        document_type.remove(instance)
