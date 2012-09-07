from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from editorsnotes.djotero.models import ZoteroLink
from editorsnotes.djotero.utils import validate_zotero_data
from reversion import revision
from models import Project, PermissionError, Document, FeaturedItem, DocumentLink
import forms as main_forms
import models as main_models
from forms import ProjectUserFormSet, ProjectForm
from collections import OrderedDict
import json

################################################################################
# Note, topic, document admin
################################################################################

@login_required
@revision.create_on_success
def document_add(request):
    o = {}
    if request.method == 'POST':
        o['form'] = main_forms.DocumentForm(request.POST)
        o['links_formset'] = main_forms.DocumentLinkFormset(
            request.POST, prefix='links')
        o['scans_formset'] = main_forms.ScanFormset(
            request.POST, request.FILES, prefix='scans')
        o['topics_formset'] = main_forms.TopicAssignmentFormset(
            request.POST, prefix='ta')

        formsets_are_valid = map(
            lambda fs: fs.is_valid(),
            [o['links_formset'], o['scans_formset'], o['topics_formset']])

        if o['form'].is_valid() and all(formsets_are_valid):
            document = o['form'].save(commit=False)
            document.creator = request.user
            document.last_updater = request.user
            document.save()

            o['form'].save_zotero_data()

            for form in [f for fs in [o['links_formset'], o['scans_formset']] for f in fs]:
                if (not form.has_changed() or
                    not form.is_valid() or
                    form.cleaned_data['DELETE']):
                    continue
                obj = form.save(commit=False)
                obj.document = document
                obj.creator = request.user
                obj.save()

            for form in o['topics_formset']:
                if not form.has_changed() or not form.is_valid():
                    continue
                if form.cleaned_data['DELETE']:
                    if form.instance and form.instance.id:
                        form.instance.delete()
                elif form.cleaned_data['topic']:
                    # Don't save this topic assignment if it already exists or
                    # if another assignment with the same topic/document exists
                    if (form.instance and form.instance.id):
                        continue
                    if form.cleaned_data['topic'] in document.topics.all():
                        continue
                    ta = form.save(commit=False)
                    ta.creator = request.user
                    ta.topic = form.cleaned_data['topic']
                    ta.content_object = document
                    ta.save()

            if request.is_ajax():
                return HttpResponse(json.dumps(
                    {'document': document.as_text(),
                     'id': document.id} ))

            messages.add_message(request, messages.SUCCESS,
                                 'Document %s added' % document.as_text())
            return HttpResponseRedirect(document.get_absolute_url())

    else:
        o['form'] = main_forms.DocumentForm()
        o['links_formset'] = main_forms.DocumentLinkFormset(prefix='links')
        o['scans_formset'] = main_forms.ScanFormset(prefix='scans')
        o['topics_formset'] = main_forms.TopicAssignmentFormset(prefix='ta')

    return render_to_response(
        'admin/document_add.html', o, context_instance=RequestContext(request))

@login_required
@revision.create_on_success
def document_change(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    o = {}

    if request.method == 'POST':
        o['form'] = main_forms.DocumentForm(request.POST, instance=document)
        o['links_formset'] = main_forms.DocumentLinkFormset(
            request.POST, instance=document, prefix='links')
        o['scans_formset'] = main_forms.ScanFormset(
            request.POST, request.FILES, instance=document, prefix='scans')
        o['topics_formset'] = main_forms.TopicAssignmentFormset(
            request.POST, instance=document, prefix='ta')

        formsets_are_valid = map(
            lambda fs: fs.is_valid(),
            [o['links_formset'], o['scans_formset'], o['topics_formset']])

        if o['form'].is_valid() and all(formsets_are_valid):
            document = o['form'].save(commit=False)
            document.last_updater = request.user
            document.save()

            o['form'].save_zotero_data()

            for form in [f for fs in [o['links_formset'], o['scans_formset']] for f in fs]:
                if not form.has_changed() or not form.is_valid():
                    # We already know the form is valid, but have to call it in
                    # able to access form.cleaned_data
                    continue
                if form.cleaned_data['DELETE']:
                    if form.instance:
                        form.instance.delete()
                else:
                    obj = form.save(commit=False)
                    if not (form.instance and form.instance.id is not None):
                        # new item
                        obj.creator = request.user
                        obj.document = document
                    obj.save()

            for form in o['topics_formset']:
                if not form.has_changed() or not form.is_valid():
                    continue
                if form.cleaned_data['DELETE']:
                    if form.instance and form.instance.id:
                        form.instance.delete()
                elif form.cleaned_data['topic']:
                    if (form.instance and form.instance.id):
                        continue
                    if form.cleaned_data['topic'] in document.topics.all():
                        continue
                    ta = form.save(commit=False)
                    ta.creator = request.user
                    ta.topic = form.cleaned_data['topic']
                    ta.content_object = document
                    ta.save()

            messages.add_message(request, messages.SUCCESS, 'Document changed')
            return HttpResponseRedirect(document.get_absolute_url())

    else:
        o['form'] = main_forms.DocumentForm(instance=document)
        o['links_formset'] = main_forms.DocumentLinkFormset(
            instance=document, prefix='links')
        o['scans_formset'] = main_forms.ScanFormset(
            instance=document, prefix='scans')
        o['topics_formset'] = main_forms.TopicAssignmentFormset(
            instance=document, prefix='ta')

    return render_to_response(
        'admin/document_change.html', o, context_instance=RequestContext(request))

@login_required
@revision.create_on_success
def note_add(request):
    o = {}
    if request.method == 'POST':
        o['form'] = main_forms.NoteForm(request.POST)
        o['form'].fields['assigned_users'].queryset=\
                main_models.UserProfile.objects.filter(
                    affiliation=request.user.get_profile().affiliation,
                    user__is_active=1).order_by('user__last_name')
        o['topics_formset'] = main_forms.TopicAssignmentFormset(
            request.POST, prefix='ta')
        if o['form'].is_valid() and o['topics_formset'].is_valid():
            note = o['form'].save(commit=False)
            note.creator = request.user
            note.last_updater = request.user
            note.save()
            o['form'].save_m2m()
            for form in o['topics_formset']:
                if not form.has_changed() or not form.is_valid():
                    continue
                if form.cleaned_data['DELETE']:
                    continue
                if form.cleaned_data['topic']:
                    if form.cleaned_data['topic'] in note.topics.all():
                        continue
                    ta = form.save(commit=False)
                    ta.creator = request.user
                    ta.topic = form.cleaned_data['topic']
                    ta.content_object = note
                    ta.save()

            return HttpResponseRedirect(note.get_absolute_url())
    else:
        o['form'] = main_forms.NoteForm()
        o['form'].fields['assigned_users'].queryset=\
                main_models.UserProfile.objects.filter(
                    affiliation=request.user.get_profile().affiliation,
                    user__is_active=1).order_by('user__last_name')
        o['topics_formset'] = main_forms.TopicAssignmentFormset(prefix='ta')
    return render_to_response(
        'admin/note_add.html', o, context_instance=RequestContext(request))

@login_required
@revision.create_on_success
def note_change(request, note_id):
    note = get_object_or_404(main_models.Note, id=note_id)
    o = {}

    if request.method == 'POST':
        o['form'] = main_forms.NoteForm(request.POST, instance=note)
        o['form'].fields['assigned_users'].querset=\
                main_models.UserProfile.objects.filter(
                    affiliation=request.user.get_profile().affiliation,
                    user__is_active=1).order_by('user__last_name')
        o['topics_formset'] = main_forms.TopicAssignmentFormset(
            request.POST, instance=note, prefix='ta')
        if o['form'].is_valid() and o['topics_formset'].is_valid():
            note = o['form'].save(commit=False)
            note.last_updater = request.user
            note.save()
            o['form'].save_m2m()
            for form in o['topics_formset']:
                if not form.has_changed() or not form.is_valid():
                    continue
                if form.cleaned_data['DELETE']:
                    if form.instance and form.instance.id:
                        form.instance.delete()
                    continue
                elif form.cleaned_data['topic']:
                    if form.cleaned_data['topic'] in note.topics.all():
                        continue
                    ta = form.save(commit=False)
                    ta.creator = request.user
                    ta.topic = form.cleaned_data['topic']
                    ta.content_object = note
                    ta.save()
        return HttpResponseRedirect(note.get_absolute_url())

    else:
        o['form'] = main_forms.NoteForm(instance=note)
        o['form'].fields['assigned_users'].queryset=\
                main_models.UserProfile.objects.filter(
                    affiliation=request.user.get_profile().affiliation,
                    user__is_active=1).order_by('user__last_name')
        o['topics_formset'] = main_forms.TopicAssignmentFormset(
            instance=note, prefix='ta')
    return render_to_response(
        'admin/note_change.html', o, context_instance=RequestContext(request))

@login_required
@revision.create_on_success
def notesection_add(request):
    o = {}
    if request.method == 'POST':
        pass
    else:
        pass
    return render_to_response(
        'admin/notesection_add.html', o, context_instance=RequestContext(request))

@login_required
@revision.create_on_success
def notesection_change(request):
    o = {}
    if request.method == 'POST':
        pass
    else:
        pass
    return render_to_response(
        'admin/notesection_change.html', o, context_instance=RequestContext(request))



################################################################################
# Project management
################################################################################

@login_required
@revision.create_on_success
def project_roster(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    # Test user permissions
    if not project.attempt('view', user):
        return HttpResponseForbidden(
            content='You do not have permission to view the roster of %s' % project.name)
    o['can_change'] = project.attempt('change', user)

    # Save project roster
    if request.method == 'POST':
        if not o['can_change']:
            messages.add_message(request, messages.ERROR,
                                 'Cannot edit project roster')
        else:
            formset = ProjectUserFormSet(request.POST)
            if formset.is_valid():
                for form in formset:
                    form.project = project
                formset.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Roster for %s saved.' % (project.name))
                return HttpResponseRedirect(request.path)
            else:
                #TODO
                pass

    # Render project form, disabling inputs if user can't change them
    project_roster = User.objects.filter(userprofile__affiliation=project)\
            .order_by('-is_active', '-last_login')
    o['formset'] = ProjectUserFormSet(queryset=project_roster)
    for form in o['formset']:
        u = form.instance
        if not o['can_change']:
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

@login_required
@revision.create_on_success
def change_project(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    user = request. user

    if not project.attempt('change', user):
        return HttpResponseForbidden(
            content='You do not have permission to edit the details of %s' % project.name)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
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

@login_required
@revision.create_on_success
def change_featured_items(request, project_id):
    o = {}
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    try:
        project.attempt('change', user)
    except PermissionError:
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
            FeaturedItem.objects.filter(project=project, id__in=deleted).delete()
        messages.add_message(request, messages.SUCCESS, 'Featured items saved.')
        return HttpResponseRedirect(redirect)

    return render_to_response(
        'admin/featured_items_change.html', o, context_instance=RequestContext(request))

