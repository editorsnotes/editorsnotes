from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loaders.app_directories import load_template_source
from models import Project, PermissionError
from forms import ProjectUserFormSet, ProjectForm

def project_roster(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    try:
        project.attempt('view', user)
    except PermissionError:
        msg = 'You do not have permission to view the roster of %s' % (
            project.name)
        return HttpResponseForbidden(content=msg)

    try:
        can_change = project.attempt('change', user)
        o['can_change'] = True
    except PermissionError:
        can_change = False

    if request.method == 'POST':
        if not can_change:
            messages.add_message(
                request,
                messages.ERROR,
                'Cannot edit project roster')
        else:
            formset = ProjectUserFormSet(request.POST)
            if formset.is_valid():
                for form in formset:
                    form.project = project
                formset.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Roster for %s saved.' % (project.name))
                return HttpResponseRedirect(request.path)
            else:
                #TODO
                pass

    project_roster = User.objects.filter(
        userprofile__affiliation=project).order_by('-is_active', '-last_login')
    o['formset'] = ProjectUserFormSet(queryset=project_roster)
    for form in o['formset']:
        u = form.instance
        if not can_change:
            for field in form.fields:
                f = form.fields[field]
                f.widget.attrs['disabled'] = 'disabled'
        elif u == request.user:
            for field in form.fields:
                f = form.fields[field]
                f.widget.attrs['readonly'] = 'readonly'
        form.initial['project_role'] = u.get_profile().get_project_role(project)
    return render_to_response(
        'admin/project_roster.html', o, context_instance=RequestContext(request))

def change_project(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    user = request. user

    try:
        project.attempt('change', user)
    except PermissionError:
        msg = 'You do not have permission to edit the details of %s' % (
            project.name)
        return HttpResponseForbidden(content=msg)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Details of %s saved.' % (project.name))
            redirect = request.GET.get('return_to', request.path)
            return HttpResponseRedirect(redirect)
        else:
            pass
    o['form'] = ProjectForm(instance=project)
    return render_to_response(
        'admin/project_change.html', o, context_instance=RequestContext(request))

def modal_document_edit(request):
    template_text = load_template_source('handlebars.html')[0]
    return HttpResponse(template_text)
