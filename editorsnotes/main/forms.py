from django import forms
from django.forms.models import modelformset_factory, ModelForm
from django.contrib.auth.models import User
from models import ALL_PROJECT_ROLES

class ProjectUserForm(ModelForm):
    project_role = forms.MultipleChoiceField(
        choices = tuple([(r, r.title()) for r in ALL_PROJECT_ROLES]),
        widget = forms.Select)
    class Meta:
        model = User
    def __init__(self, *args, **kwargs):
        super(ProjectUserForm, self).__init__(*args, **kwargs)
        if kwargs.has_key('instance'):
            u = kwargs['instance']
            self.user_display_name = u.get_full_name() or u.username
            self.last_active = u.last_login
            self.user_email = u.email
            existing_project_role = u.get_profile().get_project_role()
            self.initial['project_role'] = existing_project_role
    def save(self, commit=True):
        model = super(ProjectUserForm, self).save(commit=False)
        profile = model.get_profile()
        existing_role = profile.get_project_role()
        if existing_role != self.cleaned_data['project_role']:
            old_role = model.groups.get(
                name__startswith=profile.affiliation.slug)
            new_role = Group.objects.get(name="%s_%s" % (
                profile.affiliation.slug, self.cleaned_data['project_role']))
            user_roles = model.groups.all()
            user_roles.remove(old_role)
            user_roles.add(new_role)
        if commit:
            model.save()
        return model

ProjectUserFormSet = modelformset_factory(
    User,
    form=ProjectUserForm,
    extra=0,
    fields=('is_active',),
)
