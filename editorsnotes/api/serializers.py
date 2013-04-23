from rest_framework import serializers
from rest_framework.relations import RelatedField, HyperlinkedRelatedField
from editorsnotes.main import models as main_models

class TopicSerializer(serializers.ModelSerializer):
    topics = RelatedField('topics', many=True)
    creator = serializers.Field(source='creator.username')
    last_updater = serializers.Field(source='last_updater.username')
    class Meta:
        model = main_models.Topic
        fields = ('id', 'preferred_name', 'type', 'topics', 'summary',
                  'creator', 'last_updater')

class DocumentSerializer(serializers.ModelSerializer):
    topics = RelatedField('topics', many=True)
    class Meta:
        model = main_models.Document
        fields = ('id', 'description',)


######

class TextNSSerializer(serializers.ModelSerializer):
    section_id = serializers.Field(source='note_section_id')
    section_type = serializers.Field(source='section_type_label')
    class Meta:
        model = main_models.notes.TextNS
        fields = ('section_id', 'section_type', 'content',)

class CitationNSSerializer(serializers.ModelSerializer):
    section_id = serializers.Field(source='note_section_id')
    note_id = serializers.Field(source='note_id')
    section_type = serializers.Field(source='section_type_label')
    document = HyperlinkedRelatedField(view_name='api-documents-detail')
    class Meta:
        model = main_models.notes.CitationNS
        fields = ('note_id', 'section_id', 'section_type', 'document', 'content',)

class NoteReferenceNSSerializer(serializers.ModelSerializer):
    section_id = serializers.Field(source='note_section_id')
    section_type = serializers.Field(source='section_type_label')
    note_reference = HyperlinkedRelatedField(view_name='api-notes-detail')
    class Meta:
        model = main_models.notes.NoteReferenceNS
        fields = ('section_id', 'section_type', 'note_reference', 'content',)

def _serializer_from_section_type(section_type):
    if section_type == 'citation':
        serializer = CitationNSSerializer
    elif section_type == 'text':
        serializer = TextNSSerializer
    elif section_type == 'notereference':
        serializer = NoteReferenceNSSerializer
    else:
        raise NotImplementedError(
            'No such note section type: {}'.format(section_type))
    return serializer

class NoteSectionField(serializers.RelatedField):
    def to_native(self, value):
        section_type = getattr(value, '_section_type')
        section = getattr(value, section_type)
        serializer_class = _serializer_from_section_type(
            section.section_type_label)
        serializer = serializer_class(section)
        return serializer.data

class SectionOrderingField(serializers.WritableField):
    def section_ids(self, note):
        if not hasattr(self, '_section_ids'):
            self._section_ids = [
                ns.note_section_id for ns in note.sections.all()
            ]
        return self._section_ids
    def field_to_native(self, obj, field_name):
        return self.section_ids(obj)
    def field_from_native(self, data, files, field_name, into):
        note = self.root.object

        if not data.has_key(field_name):
            data[field_name] = self.section_ids(note)

        ids = data.get(field_name, None)

        if not isinstance(ids, list):
            raise serializers.ValidationError('Must be a list')

        different_ids = set.symmetric_difference(
            set(ids), set(self.section_ids(note)))

        if len(different_ids):
            raise serializers.ValidationError(
                'Must contain every section id and no more')

        for section in note.sections.all():
            section.ordering = data[field_name].index(section.note_section_id)
            section.save()

        # we don't need to update the "into" dict, because nothing changed.
        # The section_ordering list doesn't map to a native object.

        return 


class NoteSerializer(serializers.ModelSerializer):
    topics = RelatedField('topics', many=True)
    section_ordering = SectionOrderingField()
    sections = NoteSectionField(many=True)
    class Meta:
        model = main_models.Note
        fields = ('id', 'title', 'topics', 'content', 'status', 
                  'section_ordering', 'sections',)

class MinimalNoteSerializer(serializers.ModelSerializer):
    topics = RelatedField('topics', many=True)
    class Meta:
        model = main_models.Note
        fields = ('id', 'title', 'topics', 'content', 'status',)
