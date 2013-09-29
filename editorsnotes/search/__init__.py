from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from editorsnotes.main import models

from .index import ENIndex

en_index = ENIndex()
en_index.register(models.Document,
                  display_field='serialized.description',
                  highlight_fields=('serialized.description',))
en_index.register(models.Note,
                  display_field='serialized.title',
                  highlight_fields=('serialized.title',
                                    'serialized.content',
                                    'serialized.sections'))

@receiver(post_save)
def update_elastic_search_handler(sender, instance, created, **kwargs):
    klass = instance.__class__
    if klass in en_index.document_types:
        document_type = en_index.document_types[klass]
        if created:
            document_type.index(instance)
        else:
            document_type.update(instance)
    elif isinstance(klass, models.notes.NoteSection):
        update_elastic_search_handler(sender, instance.note, False)

@receiver(post_delete)
def delete_es_document_handler(sender, instance, **kwargs):
    klass = instance.__class__
    if klass in en_index.document_types:
        document_type = en_index.document_types[klass]
        document_type.remove(instance)
