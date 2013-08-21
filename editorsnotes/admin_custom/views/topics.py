# -*- coding: utf-8 -*- 

from django.shortcuts import get_object_or_404

from editorsnotes.main.models.topics import Topic

from .. import forms
from common import BaseAdminView

class TopicAdminView(BaseAdminView):
    form_class = forms.TopicForm
    formset_classes = (
        forms.TopicAssignmentFormset,
        forms.AliasFormset,
        forms.CitationFormset,
    )
    template_name = 'topic_admin.html'
    def get_object(self, topic_id=None):
        return topic_id and get_object_or_404(Topic, id=topic_id)
    def save_citation_formset_form(self, form):
        obj = form.save(commit=False)
        if not obj.id:
            obj.content_object = self.object
            obj.creator = self.request.user
        obj.last_updater = self.request.user
        obj.save()
    def save_alias_formset_form(self, form):
        obj = form.save(commit=False)
        if not obj.id:
            obj.creator = self.request.user
        obj.topic = self.object
        obj.save()
