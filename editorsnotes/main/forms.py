from django import forms
from django.forms.models import modelformset_factory, ModelForm
from django.contrib.auth.models import User, Group
from fields import XHTMLWidget
from models import Project, NoteSection, Document
from editorsnotes.djotero.models import ZoteroLink
from editorsnotes.djotero.utils import validate_zotero_data
from collections import OrderedDict
import json

class ProjectUserForm(ModelForm):
    project_roles = ['editor', 'researcher']
    project_role = forms.ChoiceField(
        choices=tuple([(r, r.title()) for r in project_roles]))
    class Meta:
        model = User
    def __init__(self, *args, **kwargs):
        super(ProjectUserForm, self).__init__(*args, **kwargs)
        if kwargs.has_key('instance'):
            u = kwargs['instance']
            self.user_object = u
            self.user_display_name = u.get_full_name() or u.username
    def save(self, commit=True):
        model = super(ProjectUserForm, self).save(commit=False)
        existing_role = model.get_profile().get_project_role(self.project)
        if existing_role != self.cleaned_data['project_role']:
            old_role = model.groups.get(name__startswith='%s_' % (
                self.project.slug))
            new_role = Group.objects.get(name__startswith="%s_%s" % (
                self.project.slug, self.cleaned_data['project_role']))
            model.groups.remove(old_role)
            model.groups.add(new_role)
        if commit:
            model.save()
        return model

ProjectUserFormSet = modelformset_factory(
    User,
    form=ProjectUserForm,
    extra=0,
    fields=('is_active',),
)

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = ('slug',)

class NoteSectionForm(ModelForm):
    class Meta:
        model = NoteSection
        fields = ('document', 'content',)
        widgets = {
            'document' : forms.widgets.HiddenInput(
                attrs={ 'class': 'autocomplete-documents'}) }

class DocumentForm(ModelForm):
    zotero_string = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput())
    class Meta:
        model = Document
        fields = ('description', 'edtf_date',)
        widgets = {
            'edtf_date': forms.widgets.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)

        if kwargs.has_key('instance'):
            document = kwargs['instance']
            self.initial['zotero_string'] = (
                document.zotero_link().zotero_data
                if document.zotero_link() else '')

    def clean_zotero_string(self):
        data = self.cleaned_data['zotero_string']
        if data == '':
            return data

        if not json.loads(data).has_key('fields'):
            raise forms.ValidationError('Zotero string not in correct format')
        zotero_fields = json.loads(data)['fields']
        zotero_data = OrderedDict()
        for field in zotero_fields:
            key, val = field.items()[0]
            zotero_data[key] = val
        if not validate_zotero_data(zotero_data):
            raise forms.ValidationError('Zotero string invalid')

        return json.dumps(zotero_data)

    def save_zotero_data(self):
        document = self.instance
        if self.cleaned_data['zotero_string']:
            if document.zotero_link():
                z = document.zotero_link()
                z.zotero_data = self.cleaned_data['zotero_string']
                z.save()
            else:
                z = ZoteroLink.objects.create(
                    doc=document, zotero_data=self.cleaned_data['zotero_string'])
            return z
        else:
            return None
