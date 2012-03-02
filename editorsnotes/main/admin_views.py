from django.contrib.auth.models import User, Group
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from models import Project

def project_roster(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    o['roster'] = User.objects.filter(
        userprofile__affiliation=project).order_by('-is_active', 'id')
    o['editor_group'] = Group.objects.get(name='Editors')
    return render_to_response(
        'admin/project_roster.html', o,
        context_instance=RequestContext(request))
