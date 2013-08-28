# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
import reversion

from editorsnotes.main.models.auth import Project, FeaturedItem

from .. import forms
from common import VIEW_ERROR_MSG, CHANGE_ERROR_MSG

@login_required
@reversion.create_revision()
def project_roster(request, project_id):
    o = {}
    user = request.user
    project = get_object_or_404(Project, id=project_id)
    can_change = project.attempt('change', user)
    ProjectRosterFormSet = forms.make_project_roster_formset(project)
    ProjectInvitationFormSet = forms.make_project_invitation_formset(project)
    if not project.attempt('view', user):
        return HttpResponseForbidden(VIEW_ERROR_MSG.format(project))

    if request.method == 'POST':
        if not can_change:
            return HttpResponseForbidden(CHANGE_ERROR_MSG.format(project))
        o['roster_formset'] = ProjectRosterFormSet(
            request.POST, prefix='roster')
        o['invitation_formset'] = ProjectInvitationFormSet(
            request.POST, prefix='invitation')
        if o['roster_formset'].is_valid() and o['invitation_formset'].is_valid():
            o['roster_formset'].save()
            for form in o['invitation_formset']:
                if form.cleaned_data.get('DELETE', False):
                    if form.instance:
                        form.instance.delete()
                    continue
                obj = form.save(commit=False)
                if not obj.id:
                    if not form.cleaned_data.has_key('email'):
                        continue
                    obj.creator = request.user
                    obj.project = project
                obj.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Roster for {} saved.'.format(project.name))
            return HttpResponseRedirect(request.path)
    elif can_change:
        o['roster_formset'] = ProjectRosterFormSet(prefix='roster')
        o['invitation_formset'] = ProjectInvitationFormSet(prefix='invitation')

    o['project'] = project
    o['roster'] = [(u, u.get_project_role(project))
                   for u in project.members.order_by('-user__last_login')]

    return render_to_response(
        'project_roster.html', o, context_instance=RequestContext(request))

@login_required
@reversion.create_revision()
def change_project(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    user = request. user

    if not project.attempt('change', user):
        return HttpResponseForbidden(
            content='You do not have permission to edit the details of %s' % project.name)

    if request.method == 'POST':
        form = forms.ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Details of %s saved.' % (project.name))
            redirect = request.GET.get('return_to', request.path)
            return HttpResponseRedirect(redirect)
        else:
            pass
    o['form'] = forms.ProjectForm(instance=project)
    return render_to_response(
        'project_change.html', o, context_instance=RequestContext(request))

@login_required
@reversion.create_revision()
def change_featured_items(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    try:
        project.attempt('change', user)
    except main_models.PermissionError:
        msg = 'You do not have permission to access this page'
        return HttpResponseForbidden(content=msg)

    o['featured_items'] = project.featureditem_set.all()
    o['project'] = project

    if request.method == 'POST':
        redirect = request.GET.get('return_to', request.path)

        added_model = request.POST.get('autocomplete-model', None)
        added_id = request.POST.get('autocomplete-id', None)
        deleted = request.POST.getlist('delete-item')

        if added_model in ['notes', 'topics', 'documents'] and added_id:
            ct = ContentType.objects.get(model=added_model[:-1])
            obj = ct.model_class().objects.get(id=added_id)
            user_affiliation = request.user.get_profile().affiliation
            if not (user_affiliation in obj.affiliated_projects.all()
                    or request.user.is_superuser):
                messages.add_message(
                    request, messages.ERROR,
                    'Item %s is not affiliated with your project' % obj.as_text())
                return HttpResponseRedirect(redirect)
            FeaturedItem.objects.create(content_object=obj,
                                        project=project,
                                        creator=request.user)
        if deleted:
            FeaturedItem.objects\
                .filter(project=project, id__in=deleted)\
                .delete()
        messages.add_message(request, messages.SUCCESS, 'Featured items saved.')
        return HttpResponseRedirect(redirect)

    return render_to_response(
        'featured_items_admin.html', o, context_instance=RequestContext(request))

