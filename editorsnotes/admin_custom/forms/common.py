# -*- coding: utf-8 -*-

from django import forms
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.forms.models import ModelForm
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe

from editorsnotes.main.models.topics import (
    TopicNodeAssignment, ProjectTopicContainer)

#class TopicAssignmentWidget(forms.widgets.HiddenInput):
#    def render(self, name, value, attrs=None):
#        hidden_input = super(TopicAssignmentWidget, self).render(name, value, attrs=None)
#        if value:
#            topic = get_object_or_404(ProjectTopicContainer, id=value)
#            extra_content = topic.preferred_name
#        else:
#            extra_content = ''
#        return mark_safe(extra_content + hidden_input)
#
#class TopicAssignmentForm(ModelForm):
#    class Meta:
#        model = TopicNodeAssignment
#        widgets = {'topic': TopicNodeAssignmentWidget()}
#
#TopicAssignmentFormset = generic_inlineformset_factory(
#    TopicNodeAssignment, form=TopicNodeAssignmentForm, extra=1)
