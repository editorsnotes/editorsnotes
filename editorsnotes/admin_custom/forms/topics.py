from django import forms
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.forms.models import ModelForm, inlineformset_factory

from editorsnotes.main.models.topics import ProjectTopicContainer
from editorsnotes.main.models.documents import Citation

class TopicForm(ModelForm):
    class Media:
        js = (
            "function/admin-bootstrap-topic.js",
            "function/admin-bootstrap-note-sections.js",
        )
    class Meta:
        model = ProjectTopicContainer
        fields = ('preferred_name', )

#class AliasForm(ModelForm):
#    class Meta:
#        model = Alias
#        fields = ('name',)
#
#AliasFormset = inlineformset_factory(
#    Topic, Alias, form=AliasForm, extra=1)
#
class CitationForm(ModelForm):
    class Meta:
        model = Citation
        fields = ('document', 'notes', 'ordering',)
        widgets = {'document': forms.widgets.HiddenInput()}

CitationFormset = generic_inlineformset_factory(
    Citation, form=CitationForm, extra=1)
