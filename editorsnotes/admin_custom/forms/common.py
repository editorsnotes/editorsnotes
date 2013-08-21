from django import forms
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.forms.models import ModelForm
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe

from editorsnotes.main.models.topics import Topic, TopicAssignment

class TopicAssignmentWidget(forms.widgets.HiddenInput):
    def render(self, name, value, attrs=None):
        hidden_input = super(TopicAssignmentWidget, self).render(name, value, attrs=None)
        if value:
            topic = get_object_or_404(Topic, id=value)
            extra_content = topic.preferred_name
        else:
            extra_content = ''
        return mark_safe(extra_content + hidden_input)

class TopicAssignmentForm(ModelForm):
    class Meta:
        model = TopicAssignment
        widgets = {'topic': TopicAssignmentWidget()}

TopicAssignmentFormset = generic_inlineformset_factory(
    TopicAssignment, form=TopicAssignmentForm, extra=1)
