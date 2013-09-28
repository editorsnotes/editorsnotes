from editorsnotes.main.models.documents import Document

from .base import BaseListAPIView, BaseDetailView, CreateReversionMixin
from ..serializers import DocumentSerializer

class DocumentList(BaseListAPIView, CreateReversionMixin):
    model = Document
    serializer_class = DocumentSerializer
    def pre_save(self, obj):
        super(DocumentList, self).pre_save(obj)
        obj.project = self.request.project

class DocumentDetail(BaseDetailView, CreateReversionMixin):
    model = Document
    serializer_class = DocumentSerializer
