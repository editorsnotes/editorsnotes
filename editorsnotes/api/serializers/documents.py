from collections import OrderedDict
import json

from rest_framework import serializers
from rest_framework.reverse import reverse

from editorsnotes.main.models import Document, Scan, Transcript
from editorsnotes.main.utils import remove_stray_brs

from .. import fields
from .mixins import RelatedTopicSerializerMixin, EmbeddedItemsMixin
from ..ld import ROOT_NAMESPACE

__all__ = ['DocumentSerializer', 'ScanSerializer', 'TranscriptSerializer']


class ZoteroField(serializers.Field):
    def to_representation(self, value):
        return value and json.loads(value, object_pairs_hook=OrderedDict)

    def to_internal_value(self, data):
        return json.dumps(data)


class HyperLinkedImageField(serializers.ImageField):
    def to_native(self, value):
        if not value.name:
            ret = None
        elif 'request' in self.context:
            ret = self.context['request'].build_absolute_uri(value.url)
        else:
            ret = value.url
        return ret


class ScanSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')
    image = HyperLinkedImageField()
    image_thumbnail = HyperLinkedImageField(read_only=True)
    height = serializers.SerializerMethodField()
    width = serializers.SerializerMethodField()

    class Meta:
        model = Scan
        fields = ('id', 'image', 'image_thumbnail', 'height', 'width',
                  'created', 'creator',)

    def get_height(self, obj):
        try:
            return obj.image.height
        except IOError:
            return None

    def get_width(self, obj):
        try:
            return obj.image.width
        except IOError:
            return None


class UniqueDocumentDescriptionValidator:
    message = 'Document with this description already exists.'

    def set_context(self, serializer):
        self.instance = getattr(self, 'instance', None)

    def __call__(self, attrs):
        if self.instance is not None:
            description = attrs.get('description', self.instance.description)
        else:
            description = attrs['description']

        project = attrs['project']
        qs = Document.objects.filter(
            description_digest=Document.hash_description(description),
            project=project)
        if self.instance is not None:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError({
                'description': [self.message]
            })


class DocumentSerializer(RelatedTopicSerializerMixin, EmbeddedItemsMixin,
                         serializers.ModelSerializer):
    url = fields.IdentityURLField(view_name='api:documents-detail')
    type = serializers.SerializerMethodField()
    project = fields.HyperlinkedAffiliatedProjectField(
        default=fields.CurrentProjectDefault())
    updaters = fields.UpdatersField()

    transcript = fields.CustomLookupHyperlinkedField(
        read_only=True,
        view_name='api:transcripts-detail',
        lookup_kwarg_attrs={
            'project_slug': 'project.slug',
            'document_id': 'id'
        }
    )

    zotero_data = ZoteroField(required=False)
    related_topics = fields.TopicAssignmentField(many=True)
    scans = ScanSerializer(many=True, required=False, read_only=True)
    cited_by = serializers.SerializerMethodField('get_citations')

    referenced_by = fields.UnqualifiedURLField(source='get_referencing_items')

    class Meta:
        model = Document
        fields = (
            'id',
            'url',
            'type',
            'project',

            'description',

            'created',
            'last_updated',
            'updaters',

            'zotero_data',
            'scans',
            'transcript',

            'related_topics',
            'cited_by',
            'referenced_by',
        )
        embedded_fields = (
            'project',
            'updaters',
            'transcript',
            'related_topics',
            'referenced_by',
        )
        validators = [
            UniqueDocumentDescriptionValidator()
        ]

    def get_type(self, obj):
        return ROOT_NAMESPACE + 'Document'

    def get_citations(self, obj):
        return obj.get_citations()

    def get_transcript_url(self, obj):
        if not obj.has_transcript():
            return None
        return reverse(
            'api:transcripts-detail',
            args=[obj.project.slug, obj.id],
            request=self.context['request']
        )

    def validate_description(self, value):
        description_stripped = Document.strip_description(value)
        if not description_stripped:
            raise serializers.ValidationError('Field required.')
        remove_stray_brs(value)
        return value


class TranscriptSerializer(EmbeddedItemsMixin, serializers.ModelSerializer):
    url = fields.IdentityURLField(
        view_name='api:transcripts-detail',
        lookup_kwarg_attrs={
            'project_slug': 'document.project.slug',
            'document_id': 'document.id'
        }
    )
    project = fields.HyperlinkedAffiliatedProjectField()
    document = fields.CustomLookupHyperlinkedField(
        read_only=True,
        view_name='api:documents-detail',
        lookup_kwarg_attrs={
            'project_slug': 'document.project.slug',
            'pk': 'document.id'
        }
    )
    references = fields.UnqualifiedURLField(source='get_referenced_items')

    class Meta:
        model = Transcript
        fields = (
            'url',
            'project',
            'document',

            'markup',
            'markup_html',

            'references'
        )
        embedded_fields = (
            'project',
            'document',
            'references',
        )
