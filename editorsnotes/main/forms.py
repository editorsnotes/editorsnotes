from django import forms
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.forms.models import inlineformset_factory, modelformset_factory, ModelForm
from django.contrib.auth.models import User, Group
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from fields import XHTMLWidget, MultipleFileInput
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
            "function/zotero.jquery.js",
            "function/citeproc-js/xmle4x.js",
            "function/citeproc-js/xmldom.js",
            "function/citeproc-js/citeproc.js",
            "function/admin-bootstrap-base.js",
            "function/admin-bootstrap-document.js",
            "function/wysihtml5/wysihtml5-0.3.0.min.js",
            "function/wysihtml5/parser_rules.js",
        )
        css = {
            'all' : (
                "style/bootstrap-admin.css",
            )
        }
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

class ScanForm(ModelForm):
    class Meta:
        fields = ('image', 'ordering')
        model = main_models.Scan
        widgets = {
            'image': MultipleFileInput(),
            'ordering': forms.HiddenInput()
        }

class ScanFormset(forms.models.BaseInlineFormSet):
    """
    If multiple images were posted from a single file input with the attribute
    "multiple", this formset will split them up into regular forms
    """
    def _construct_forms(self):
        self.forms = []
        forms_from_multiple_input = []

        for i in xrange(self.total_form_count()):
            form = self._construct_form(i)

            # Only pay attention to multiple files from an input if this is the
            # last image field and there is something to save
            if (i < self.total_form_count() - 1 or not form.files):
                self.forms.append(form)
                continue

            # If only one image was posted from this input, treat it as a normal
            # one. This allows us to treat this formset as it normally would be,
            # which is beneficial for several reasons, including continued
            # support for browsers that don't support the "multiple" attribute.
            images = form.files.getlist('%s-image' % form.prefix) 
            if len(images) == 1:
                self.forms.append(form)
                continue

            # Make a copy of the file & data dictionaries, which will be amended
            # in order to make new ScanForm instances
            newfiles = dict((k, v) for k, v in form.files.items())
            newdata = dict((k, v) for k, v in form.data.items())

            # Pretend that each image was posted individually
            j = i
            for image in images:
                prefix = self.add_prefix(j)
                newfiles['%s-image' % prefix] = image
                newdata['%s-ordering' % prefix] = j
                newform = self._construct_form(j, files=newfiles, data=newdata)
                forms_from_multiple_input.append(newform)
                j += 1

        # Only add these new forms to the formset if the images are valid. This
        # does go against the normal flow of validation, but it makes the
        # workflow for adding scans *much* less complicated to take an
        # all-or-nothing approach to accepting multiple images.
        if all(map(lambda f: f.is_valid(), forms_from_multiple_input)):
            self.forms += forms_from_multiple_input
        else:
            # Make the last form an empty one, like it was previously
            self.forms.append(
                self._construct_form(self.total_form_count() - 1, files=None))
            self.bad_multi_images = 'One or more files uploaded were not valid images.'

        # Does the management form need to be changed at all? I can't think of
        # any situation where it would be, but here's how it probably would be
        # done if needed.
        # self.management_form['initial']['TOTAL_FORMS'] = len(self.forms)
            
    # Display errors from a multiple upload field as a non-form error-- in the
    # formset, not the individual form
    def clean(self):
        if hasattr(self, 'bad_multi_images'):
            raise forms.ValidationError(self.bad_multi_images)

ScanFormset = inlineformset_factory(
    main_models.Document, main_models.Scan,
    form=ScanForm, formset=ScanFormset, extra=1)

################################################################################
# Note form and formsets
################################################################################
class NoteForm(ModelForm):
    class Media:
        js = (
            "function/wysihtml5/wysihtml5-0.3.0.min.js",
            "function/wysihtml5/parser_rules.js",
            "function/admin-bootstrap-base.js",
            "function/admin-bootstrap-note.js",
            "function/wymeditor/jquery.wymeditor.pack.js",
        )
        css = {
            'all' : (
                "style/bootstrap-admin.css",
            )
        }
    class Meta:
        model = main_models.Note
        widgets = {
            'assigned_users': forms.CheckboxSelectMultiple()
        }

class NoteSectionForm(ModelForm):
    class Meta:
        model = NoteSection
        fields = ('document', 'content',)
        widgets = {'document' : forms.widgets.HiddenInput()}

NoteSectionFormset = inlineformset_factory(
    main_models.Note, main_models.NoteSection, form=NoteSectionForm, extra=1)

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
            extra_content = ''
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
