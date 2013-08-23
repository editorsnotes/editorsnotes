# -*- coding: utf-8 -*- 

from django.shortcuts import get_object_or_404

from editorsnotes.main.models.topics import ProjectTopicContainer, TopicNode

from .. import forms
from common import BaseAdminView

class TopicAdminView(BaseAdminView):
    model = ProjectTopicContainer
    form_class = forms.TopicForm
    formset_classes = (
        forms.topics.AlternateNameFormset,
        forms.topics.TopicSummaryFormset,
        # forms.TopicAssignmentFormset,
        forms.topics.CitationFormset,
    )
    template_name = 'topic_admin.html'
    def get_object(self, topic_node_id=None):
        return topic_node_id and get_object_or_404(
            ProjectTopicContainer,
            topic_id=topic_node_id, project__slug=self.project.slug)
    def set_additional_object_properties(self, obj, form):
        if not obj.id:
            if form.cleaned_data['topic']:
                topic_node = TopicNode.objects.get(
                    id=form.cleaned_data['topic'])
            else:
                topic_node = TopicNode.objects.create(
                    _preferred_name=obj.preferred_name,
                    type=form.cleaned_data['topic_type'])
            obj.topic_id = topic_node.id
        return obj
    def save_citation_formset_form(self, form):
        obj = form.save(commit=False)
        if not obj.id:
            obj.content_object = self.object
            obj.creator = self.request.user
        obj.last_updater = self.request.user
        obj.save()
    def save_alternatename_formset_form(self, form):
        obj = form.save(commit=False)
        if not obj.id:
            obj.creator = self.request.user
        obj.container = self.object
        obj.save()
