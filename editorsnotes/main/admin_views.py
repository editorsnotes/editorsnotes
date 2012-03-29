from django.contrib.auth.models import User, Group
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from models import Project
from forms import ProjectUserFormSet

def project_roster(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    project_roster = User.objects.filter(
        userprofile__affiliation=project).order_by('-is_active', 'id')

    # This is assuming that one may only be affiliated with one project
    o['editor_group'] = Group.objects.get(name='Editors')

    if request.method == 'POST':
        raise Exception
        pass
    else:
        o['formset'] = ProjectUserFormSet(queryset=project_roster)
    return render_to_response(
        'admin/project_roster.html', o, context_instance=RequestContext(request))
