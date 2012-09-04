from django import forms
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.forms.models import inlineformset_factory, modelformset_factory, ModelForm
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from fields import XHTMLWidget
import models as main_models
from models import Project, NoteSection, Document
from editorsnotes.djotero.widgets import ZoteroWidget
from editorsnotes.djotero.models import ZoteroLink
from editorsnotes.djotero.utils import validate_zotero_data
from collections import OrderedDict
import json

################################################################################
# Project forms
################################################################################

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

################################################################################
# Document form & formsets
################################################################################

class DocumentForm(ModelForm):
    zotero_string = forms.CharField(required=False, widget=ZoteroWidget())
    class Media:
        js = (
            "function/wymeditor/jquery.wymeditor.pack.js",
            "function/zotero-localization.js",
            "function/zotero-form-functions.js",
            "function/citeproc-js/xmle4x.js",
            "function/citeproc-js/xmldom.js",
            "function/citeproc-js/citeproc.js",
            "function/citeproc-js/simple.js",
            "function/admin-bootstrap-base.js",
            "function/admin-bootstrap-document.js"
        )
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

    def save_zotero_data(self):
        document = self.instance
        if self.data.get('zotero-data-DELETE', '') == 'DELETE':
            if document.zotero_link():
                z = document.zotero_link()
                z.delete()
        if self.changed_data is not None and 'zotero_string' in self.changed_data:
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

class DocumentLinkForm(ModelForm):
    class Meta:
        model = main_models.DocumentLink
        widgets = {
            'description': forms.widgets.Textarea(
                attrs={ 'cols': 80, 'rows': 2 })
        }
DocumentLinkFormset = inlineformset_factory(
    main_models.Document, main_models.DocumentLink, form=DocumentLinkForm, extra=1)

ScanFormset = inlineformset_factory(
    main_models.Document, main_models.Scan, extra=3)

################################################################################
# Note form and formsets
################################################################################
class NoteForm(ModelForm):
    class Media:
        js = (
            "function/admin-bootstrap-base.js",
            "function/admin-bootstrap-note.js",
            "function/wymeditor/jquery.wymeditor.pack.js",
        )
    class Meta:
        model = main_models.Note
        widgets = {
            'assigned_users': forms.CheckboxSelectMultiple()
        }

class NoteSectionForm(ModelForm):
    class Meta:
        model = NoteSection
        fields = ('document', 'content',)
        widgets = {
            'document' : forms.widgets.HiddenInput(
                attrs={ 'class': 'autocomplete-documents'}) }

################################################################################
# Topic assignment form, used in multiple places
################################################################################

class TopicAssignmentWidget(forms.widgets.HiddenInput):
    def render(self, name, value, attrs=None):
        hidden_input = super(TopicAssignmentWidget, self).render(name, value, attrs=None)
        if value:
            topic = get_object_or_404(main_models.Topic, id=value)
            extra_content = topic.preferred_name
        else:
            extra_content = ('<label>Add topic:</label>' +
                             '<input type="text" class="topic-autocomplete" placeholder="Type to search" />')
        return mark_safe(extra_content + hidden_input)



class TopicAssignmentForm(ModelForm):
    class Meta:
        model = main_models.TopicAssignment
        widgets = {
            'topic': TopicAssignmentWidget()
        }

TopicAssignmentFormset = generic_inlineformset_factory(
    main_models.TopicAssignment, form=TopicAssignmentForm, extra=1)

################################################################################
# Feedback form
################################################################################
PURPOSE_CHOICES = (
    ('1', 'Feedback'),
    ('2', 'Bug report'),
    ('3', 'Request for account'),
    ('9', 'Other')
)

class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=50, label='Your name')
    email = forms.EmailField(label='Your email')
    purpose = forms.ChoiceField(choices=PURPOSE_CHOICES)
    message = forms.CharField(widget=forms.Textarea(
        attrs={'cols': '50', 'rows': '7', 'style': 'width: 50em;' }))
