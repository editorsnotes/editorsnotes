from django import forms
from django.forms.models import modelformset_factory, ModelForm
from django.contrib.auth.models import User, Group
from fields import XHTMLWidget
from models import Project, NoteSection

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
