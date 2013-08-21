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

class NoteSectionForm(ModelForm):
    class Meta:
        model = CitationNS
        fields = ('document', 'content',)
        widgets = {'document' : forms.widgets.HiddenInput()}

NoteSectionFormset = inlineformset_factory(
    Note, CitationNS, form=NoteSectionForm, extra=1)


