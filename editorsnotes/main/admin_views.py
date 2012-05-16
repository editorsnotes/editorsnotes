from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from models import Project, PermissionError
from forms import ProjectUserFormSet

def project_roster(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    try:
        can_view = project.attempt('view', user)
    except PermissionError:
        msg = 'You do not have permission to view the roster of %s' % (
            project.name)
        return HttpResponseForbidden(content=msg)
    if request.method == 'POST':
        can_change = False
        try:
            can_change = project.attempt('change', user)
        except PermissionError:
            messages.add_message(
                request,
                messages.ERROR,
                'Cannot edit project roster')
        if can_change:
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
        if u == request.user:
            for field in form.fields:
                f = form.fields[field]
                f.widget.attrs['readonly'] = 'readonly'
        form.initial['project_role'] = u.get_profile().get_project_role(project)
    return render_to_response(
        'admin/project_roster.html', o, context_instance=RequestContext(request))
