from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.forms.models import (
    inlineformset_factory, modelformset_factory, ModelForm, BaseModelFormSet)
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe

from editorsnotes.djotero.widgets import ZoteroWidget
from editorsnotes.djotero.models import ZoteroLink
from editorsnotes.main import models as main_models
from fields import MultipleFileInput


################################################################################
# Project forms
################################################################################

def make_project_invitation_formset(project):
    if not isinstance(project, main_models.Project):
        raise ValueError('{} is not a project.'.format(project))

    project_invitations = main_models.ProjectInvitation.objects\
            .select_related('project')\
            .filter(project__id=project.id)

    class ProjectInvitationFormSet(BaseModelFormSet):
        def __init__(self, *args, **kwargs):
            kwargs['queryset'] = project_invitations
            super(ProjectInvitationFormSet, self).__init__(*args, **kwargs)

    class ProjectInvitationForm(ModelForm):
        class Meta:
            model = main_models.ProjectInvitation
            fields = ('email', 'role',)
        def __init__(self, *args, **kwargs):
            super(ProjectInvitationForm, self).__init__(*args, **kwargs)
            self.fields['email'].widget.attrs['placeholder'] = 'Email to invite'
        def clean_email(self):
            data = self.cleaned_data['email']
            user = User.objects.filter(email=data)
            if user.count() > 1:
                msg = 'Multiple users with this email address.'
                raise forms.ValidationError(msg)
            elif user.count() == 1 and user[0].get_profile().affiliation == project:
                msg = 'User with email {} already in project'.format(data)
                raise forms.ValidationError(msg)
            existing_invite = main_models.ProjectInvitation.objects.filter(
                email=data, project=project)
            if not self.instance.id and existing_invite.count():
                msg = 'User with email {} already invited.'.format(data)
                raise forms.ValidationError(msg)
            return data
    return modelformset_factory(
        main_models.ProjectInvitation,
        formset=ProjectInvitationFormSet,
        form=ProjectInvitationForm,
        can_delete=True,
        extra=1
    )


def make_project_roster_formset(project):
    """
    Returns a formset for editing project roles.
    """
    if not isinstance(project, main_models.Project):
        raise ValueError('{} is not a project.'.format(project))

    project_roster = main_models.User.objects\
            .select_related('userprofile')\
            .filter(userprofile__affiliation=project)\
            .order_by('-last_login')

    class ProjectRosterFormSet(BaseModelFormSet):
        def __init__(self, *args, **kwargs):
            kwargs['queryset'] = project_roster
            super(ProjectRosterFormSet, self).__init__(*args, **kwargs)

    class ProjectMemberForm(ModelForm):
        project_role = forms.ChoiceField(choices=main_models.PROJECT_ROLES)
        class Meta:
            model = User
        def __init__(self, *args, **kwargs):
            super(ProjectMemberForm, self).__init__(*args, **kwargs)
            if not self.instance.pk:
                return
            profile = self.instance.get_profile()
            self.initial['project_role'] = profile.get_project_role(project)
        def save(self, commit=True):
            user = self.instance
            existing_role = user.get_profile().get_project_role(project)
            if existing_role != self.cleaned_data['project_role']:
                old_role = user.groups.get(name__startswith='{}_'.format(
                    project.slug))
                new_role = Group.objects.get(name__startswith='{}_{}'.format(
                    project.slug, self.cleaned_data['project_role']))
                user.groups.remove(old_role)
                user.groups.add(new_role)
            user.save()
            return user

    return modelformset_factory(
        User,
        formset=ProjectRosterFormSet,
        form=ProjectMemberForm,
        fields=(),
        extra=0
    )

class ProjectForm(ModelForm):
    class Meta:
        model = main_models.Project
        exclude = ('slug',)

################################################################################
# Document form & formsets
################################################################################

class DocumentForm(ModelForm):
    zotero_string = forms.CharField(required=False, widget=ZoteroWidget())
    class Media:
        js = (
            "function/admin-bootstrap-document.js",
        )
    class Meta:
        model = main_models.Document
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
        exclude = ('affiliated_projects',)
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
            "function/admin-bootstrap-note.js",
        )
    class Meta:
        model = main_models.Note
        exclude = ('affiliated_projects',)
        widgets = {
            'assigned_users': forms.CheckboxSelectMultiple()
        }

class NoteSectionForm(ModelForm):
    class Meta:
        model = main_models.notes.CitationNS
        fields = ('document', 'content',)
        widgets = {'document' : forms.widgets.HiddenInput()}

NoteSectionFormset = inlineformset_factory(
    main_models.Note, main_models.notes.CitationNS, form=NoteSectionForm, extra=1)


################################################################################
# Topic form and formsets
################################################################################

class TopicForm(ModelForm):
    class Media:
        js = (
            "function/admin-bootstrap-topic.js",
            "function/admin-bootstrap-note-sections.js",
        )
    class Meta:
        model = main_models.Topic
        fields = ('preferred_name', 'type', 'summary',)

class AliasForm(ModelForm):
    class Meta:
        model = main_models.Alias
        fields = ('name',)

AliasFormset = inlineformset_factory(
    main_models.Topic, main_models.Alias, form=AliasForm, extra=1)


################################################################################
# Transcript form 
################################################################################

class TranscriptForm(ModelForm):
    class Media:
        js = (
            'function/admin-bootstrap-transcript.js',
        )
    class Meta:
        model = main_models.Transcript
        fields = ('content',)

class FootnoteForm(ModelForm):
    class Meta:
        model = main_models.Footnote
        fields = ('content',)
    stamp = forms.CharField(required=False, widget=forms.HiddenInput)

FootnoteFormset = inlineformset_factory(
    main_models.Transcript, main_models.Footnote, form=FootnoteForm, extra=1)


################################################################################
# Generic forms used in multiple places
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
        widgets = {'topic': TopicAssignmentWidget()}

TopicAssignmentFormset = generic_inlineformset_factory(
    main_models.TopicAssignment, form=TopicAssignmentForm, extra=1)

class CitationForm(ModelForm):
    class Meta:
        model = main_models.Citation
        fields = ('document', 'notes', 'ordering',)
        widgets = {'document': forms.widgets.HiddenInput()}

CitationFormset = generic_inlineformset_factory(
    main_models.Citation, form=CitationForm, extra=1)
