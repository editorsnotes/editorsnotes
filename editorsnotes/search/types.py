from pyelasticsearch.exceptions import ElasticHttpNotFoundError

from editorsnotes.api import serializers

class DocumentTypeAdapter(object):
    def __init__(self, es, index_name, model=None, highlight_fields=None,
                 display_field=None):
        if display_field is None:
            raise ValueError('Define a display field for this document type')
        self.display_field = display_field

        self.model = model or self.get_model()
        self.serializer = self.get_serializer()
        self.type_label = self.model._meta.module_name
        self.highlight_fields = highlight_fields
        
        self.es = es
        self.index_name = index_name

    def __unicode__(self):
        return self.model._meta.module_name

    def get_model(self):
        try:
            model = getattr(self, 'model')
        except AttributeError:
            raise NotImplementedError('Either set the `model` attribute or '
                                      'override get_model() to return a model.')
        return model

    def get_serializer(self):
        default_serializer_name = '{}Serializer'.format(self.model._meta.object_name)
        try:
            serializer = getattr(serializers, default_serializer_name)
        except AttributeError:
            raise NotImplementedError('Override this method to define a serializer.')
        return serializer

    def get_mapping(self):
        mapping = {
            self.type_label : {
                'properties': {
                    'autocomplete': {
                        'type': 'completion',
                        'payloads': True
                    }
                }
            }
        }
        return mapping

    def clear(self):
        try:
            self.es.delete_all(self.index_name, self.type_label)
        except ElasticHttpNotFoundError:
            pass

    def data_from_serializer(self, obj):
        return self.serializer(obj).data

    def format_data(self, obj):
        if not hasattr(obj, '_rest_serialized'):
            obj._rest_serialized = self.serializer(obj).data
        data = { 
            'id': obj.id,
            'serialized': obj._rest_serialized,
            'autocomplete': { 'input': obj.as_text() }
        }
        return data

    def get_object(self, instance=None, pk=None):
        if pk is None and instance is None:
            raise ValueError('Provide either a pk or instance to update.')
        obj = instance or self.model.objects.get(pk=pk)
        if not isinstance(obj, self.model):
            raise ValueError('Instance must be a {} object'.format(self.model))
        return obj

    def index(self, instance=None, pk=None):
        obj = self.get_object(instance, pk)
        doc = self.format_data(obj)
        self.es.index(self.index_name, self.type_label, doc, obj.pk, refresh=True)

    def update(self, instance=None, pk=None):
        obj = self.get_object(instance, pk)
        doc = self.format_data(obj)
        self.es.update(self.index_name, self.type_label, obj.pk, doc=doc, refresh=True)

    def remove(self, instance=None, pk=None):
        obj = self.get_object(instance, pk)
        self.es.delete(self.index_name, self.type_label, obj.pk)

    def update_all(self, qs=None, chunk_size=300):
        i = 0
        _qs = qs or self.model.objects.all()
        self.clear()

        # Break up qs into chunks & bulk index each
        while True:
            chunk = _qs[i:i + chunk_size]
            if not chunk:
                break
            data = [ self.format_data(obj) for obj in chunk ]
            self.es.bulk_index(self.index_name, self.type_label, data)
            i += chunk_size
