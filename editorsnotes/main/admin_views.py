from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.models import User, Group
from django.contrib import messages
from models import Project
from forms import ProjectUserFormSet

def project_roster(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    if request.method == 'POST':
        formset = ProjectUserFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Roster for %s saved.' % (project.name))
            return HttpResponseRedirect(request.path)
        else:
            #TODO
            pass
    else:
        project_roster = User.objects.filter(
        userprofile__affiliation=project).order_by('-is_active', '-last_login')
        o['formset'] = ProjectUserFormSet(queryset=project_roster)
    return render_to_response(
        'admin/project_roster.html', o, context_instance=RequestContext(request))
