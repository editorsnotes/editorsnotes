from django import forms
from django.forms.models import ModelForm, inlineformset_factory

from editorsnotes.main.models.notes import Note, CitationNS

class NoteForm(ModelForm):
    class Media:
        js = (
            "function/admin-bootstrap-note.js",
        )
    class Meta:
        model = Note
        exclude = ('affiliated_projects',)
        widgets = {
            'assigned_users': forms.CheckboxSelectMultiple()
        }

class CitationSectionForm(ModelForm):
    class Meta:
        model = CitationNS
        fields = ('document', 'content', 'ordering',)
        widgets = {'document' : forms.widgets.HiddenInput()}

CitationSectionFormset = inlineformset_factory(
    Note, CitationNS, form=CitationSectionForm, extra=1)
