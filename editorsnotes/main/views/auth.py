import re

from django.contrib import auth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django_browserid.views import Verify
import reversion

from ..models.auth import User, Project, ProjectInvitation

@reversion.create_revision()
def create_invited_user(email):
    invitation = ProjectInvitation.objects.filter(email=email)
    if not invitation.exists():
        return None
    invitation = invitation.get()

    project = invitation.project
    role = project.roles.get(role=invitation.role)

    username = re.sub(r'[^\w\-.]', '', email[:email.rindex('@')])[:29]
    if User.objects.filter(username=username).exists():
        existing_names = [
            u.username[len(username):] for u in
            User.objects.filter(username__startswith=username)]
        username += str([
            i for i in range(0, 10) if str(i) not in existing_names][0])

    new_user = User(username=username, email=email)
    new_user.set_unusable_password()
    new_user.save()

    role.users.add(new_user)
    invitation.delete()

    return new_user

class CustomBrowserIDVerify(Verify):
    failure_url = '/accounts/login/'
    def get_success_url(self):
        return self.request.user.get_absolute_url()

def user_logout(request):
    auth.logout(request)
    return render_to_response(
        'logout.html', context_instance=RequestContext(request))

def user(request, username=None):
    o = {}
    if not username:
        user = request.user
        o['own_profile'] = True
    else:
        user = get_object_or_404(User, username=username)
        o['own_profile'] = user == request.user
    o['user'] = user


    o['log_entries'], ignored = User.get_activity_for(user, max_count=20)

    # FIX
    # o['profile'] = get_for(user)
    # o['affiliation'] = o['profile'].affiliation
    # o['project_role'] = (o['profile'].get_project_role(o['affiliation'])
    #                      if o['affiliation'] else None)

    if ['own_profile']:
        o['zotero_status'] = user.zotero_key and user.zotero_uid
    return render_to_response(
        'user.html', o, context_instance=RequestContext(request))

def project(request, project_slug):
    o = {}
    o['project'] = get_object_or_404(Project, slug=project_slug)
    o['log_entries'], ignored = Project.get_activity_for(o['project'], max_count=10)

    if request.user.is_authenticated():
        o['project_role'] = o['project'].get_role_for(request.user)
        o['can_view_roster'] = request.user.has_project_perm(
            o['project'], 'main.view_project_roster')
        o['can_change_roster'] = request.user.has_project_perm(
            o['project'], 'main.change_project_roster')
        o['can_change_featured_items'] = request.user.has_project_perm(
            o['project'], 'main.change_featureditem')
        o['show_edit_row'] = any((
            o['can_view_roster'], o['can_change_roster'],
            o['can_change_featured_items']))
    return render_to_response(
        'project.html', o, context_instance=RequestContext(request))

def all_projects(request):
    return HttpResponse('hi')
