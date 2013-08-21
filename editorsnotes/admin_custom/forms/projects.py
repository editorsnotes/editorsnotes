from django import forms
from django.contrib.auth import Group
from django.forms.models import (
    BaseModelFormSet, ModelForm, modelformset_factory)

from editorsnotes.main.model.auth import (
    User, Project, ProjectInvitation, PROJECT_ROLES)

def make_project_invitation_formset(project):
    if not isinstance(project, Project):
        raise ValueError('{} is not a project.'.format(project))

    project_invitations = ProjectInvitation.objects\
            .select_related('project')\
            .filter(project__id=project.id)

    class ProjectInvitationFormSet(BaseModelFormSet):
        def __init__(self, *args, **kwargs):
            kwargs['queryset'] = project_invitations
            super(ProjectInvitationFormSet, self).__init__(*args, **kwargs)

    class ProjectInvitationForm(ModelForm):
        class Meta:
            model = ProjectInvitation
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
            existing_invite = ProjectInvitation.objects.filter(
                email=data, project=project)
            if not self.instance.id and existing_invite.count():
                msg = 'User with email {} already invited.'.format(data)
                raise forms.ValidationError(msg)
            return data
    return modelformset_factory(
        ProjectInvitation,
        formset=ProjectInvitationFormSet,
        form=ProjectInvitationForm,
        can_delete=True,
        extra=1
    )


def make_project_roster_formset(project):
    """
    Returns a formset for editing project roles.
    """
    if not isinstance(project, Project):
        raise ValueError('{} is not a project.'.format(project))

    project_roster = User.objects\
            .select_related('userprofile')\
            .filter(userprofile__affiliation=project)\
            .order_by('-last_login')

    class ProjectRosterFormSet(BaseModelFormSet):
        def __init__(self, *args, **kwargs):
            kwargs['queryset'] = project_roster
            super(ProjectRosterFormSet, self).__init__(*args, **kwargs)

    class ProjectMemberForm(ModelForm):
        project_role = forms.ChoiceField(choices=PROJECT_ROLES)
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
        model = Project
        exclude = ('slug',)

