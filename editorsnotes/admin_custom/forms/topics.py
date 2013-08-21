from django import forms
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.forms.models import ModelForm, inlineformset_factory

from editorsnotes.main.models.topics import Topic, Alias
from editorsnotes.main.models.documents import Citation

class TopicForm(ModelForm):
    class Media:
        js = (
            "function/admin-bootstrap-topic.js",
            "function/admin-bootstrap-note-sections.js",
        )
    class Meta:
        model = Topic
        fields = ('preferred_name', 'type', 'summary',)

class AliasForm(ModelForm):
    class Meta:
        model = Alias
        fields = ('name',)

AliasFormset = inlineformset_factory(
    Topic, Alias, form=AliasForm, extra=1)

class CitationForm(ModelForm):
    class Meta:
        model = Citation
        fields = ('document', 'notes', 'ordering',)
        widgets = {'document': forms.widgets.HiddenInput()}

CitationFormset = generic_inlineformset_factory(
    Citation, form=CitationForm, extra=1)
