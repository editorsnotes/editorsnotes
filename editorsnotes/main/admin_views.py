from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django import http
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import View, ModelFormMixin, TemplateResponseMixin

from editorsnotes.main import forms as main_forms
from editorsnotes.main import models as main_models

import reversion
import json

def collect_forms(form, formsets, **kwargs):
    if kwargs['instance'] is None:
        del(kwargs['instance'])
    f = form(**kwargs)
    fs = []
    for formset in formsets:
        fs_kwargs = kwargs
        fs_kwargs['prefix'] = formset.model._meta.module_name
        fs.append(formset(**fs_kwargs))
    return f, fs

def forms_are_valid(form, formsets):
    return all(map(lambda f: f.is_valid(), [form] + formsets))

def save_topic_form(form, obj, user):
    if not form.cleaned_data['topic']:
        return
    if form.instance and form.instance.id:
        return
    if form.cleaned_data['topic'] in obj.topics.all():
        return
    ta = form.save(commit=False)
    ta.creator = user
    ta.topic = form.cleaned_data['topic']
    ta.content_object = obj
    ta.save()
    return

###########################################################################
# Note, topic, document admin
###########################################################################

class ProcessInlineFormsetsView(View):
    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formsets = self.collect_formsets()
        return self.render_to_response(self.get_context_data(
            form=form, formsets=formsets))
    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formsets = self.collect_formsets()
        if all(map(lambda f: f.is_valid(), [form] + formsets)):
            return self.form_valid(form, formsets)
        else:
            return self.form_invalid(form, formsets)

    def collect_formsets(self):
        fs = []
        if hasattr(self, 'formset_classes'):
            for formset in self.formset_classes:
                fs_kwargs = self.get_form_kwargs()
                fs_kwargs.pop('initial', 0)
                fs_kwargs['prefix'] = formset.model._meta.module_name
                fs.append(formset(**fs_kwargs))
        return fs
    def save_formsets(self, formsets):
        for fs in formsets:
            save_method = getattr(
                self, 'save_%s_formset_form' % fs.prefix, 'save_formset_form')
            for form in fs:
                if not form.has_changed() or not form.is_valid():
                    continue
                if form.cleaned_data['DELETE']:
                    if form.instance and form.instance.id:
                        form.instance.delete()
                    continue
                save_method(form)
        return formsets
    def save_formset_form(self, form):
        raise NotImplementedError(
            'Child views must create a default formset saving method.')

class BaseAdminView(ProcessInlineFormsetsView, ModelFormMixin, TemplateResponseMixin):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BaseAdminView, self).dispatch(*args, **kwargs)
    def get(self, request, *args, **kwargs):
        self.object = self.get_object(**kwargs)
        self.template_name = self.template_base % ('change' if self.object else 'add')
        if self.object and not self.object.attempt('change', self.request.user):
            return http.HttpResponseForbidden(
                'You do not have permission to change this object')
        return super(BaseAdminView, self).get(request, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object(**kwargs)
        self.template_name = self.template_base % ('change' if self.object else 'add')
        if self.object and not self.object.attempt('change', self.request.user):
            return http.HttpResponseForbidden(
                'You do not have permission to change this object')
        return super(BaseAdminView, self).post(request, *args, **kwargs)

    def get_object(self):
        raise NotImplementedError(
            'Child views must create get_object method')
    def get_form_kwargs(self):
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        if hasattr(self, 'object') and self.object:
            kwargs.update({'instance': self.object})
        return kwargs

    def form_valid(self, form, formsets):
        with reversion.create_revision():
            obj = form.save(commit=False)
            action = 'add' if not obj.id else 'change'
            if action == 'add':
                obj.creator = self.request.user
            obj.last_updater = self.request.user
            obj.save()
            self.object = obj

            # Set reversion metadata
            reversion.set_user(self.request.user)
            reversion.set_comment('%sed %s.' % (action, obj._meta.module_name))

            # Now save models that depend on this object existing
            obj.affiliated_projects.add(
                *main_models.Project.get_affiliation_for(self.request.user))
            self.save_formsets(formsets)
            form.save_m2m()

            # Sorry for this :( It's complicated saving the zotero string in
            # the document form, since it's a separate model. I would just
            # stick this inside the DocumentForm's save_m2m, where, really,
            # it makes sense, but that method is dynamically created from
            # save_instance() in django/forms/models.py
            if hasattr(form, 'save_zotero_data'):
                form.save_zotero_data()

        return redirect(self.get_success_url())
    def form_invalid(self, form, formsets):
        return self.render_to_response(
            self.get_context_data(form=form, formsets=formsets))

    def save_topicassignment_formset_form(self, form):
        if not form.cleaned_data['topic']:
            return
        if form.instance and form.instance.id:
            return
        if form.cleaned_data['topic'] in self.instance.topics.all():
            return
        ta = form.save(commit=False)
        ta.creator = self.request.user
        ta.topic = form.cleaned_data['topic']
        ta.content_object = obj
        ta.save()
        return ta

class DocumentAdminView(BaseAdminView):
    form_class = main_forms.DocumentForm
    formset_classes = (
        main_forms.TopicAssignmentFormset,
        main_forms.DocumentLinkFormset,
        main_forms.ScanFormset
    )
    template_base = 'admin/document_%s.html'
    def get_object(self, document_id=None):
        return document_id and get_object_or_404(main_models.Document, id=document_id)
    def save_formset_form(self, form):
        obj = form.save(commit=False)
        obj.document = document
        obj.creator = request.user
        obj.save()
        return obj

class NoteAdminView(BaseAdminView):
    form_class = main_forms.NoteForm
    formset_classes = (
        main_forms.TopicAssignmentFormset,
    )
    template_base = 'admin/note_%s.html'
    def get_form(self, form_class):
        form = form_class(**self.get_form_kwargs())
        form.fields['assigned_users'].queryset=\
                main_models.UserProfile.objects.filter(
                    affiliation=main_models.Project.get_affiliation_for(self.request.user),
                    user__is_active=1).order_by('user__last_name')
        return form
    def get_object(self, note_id=None):
        return note_id and get_object_or_404(main_models.Note, id=note_id)
    def save_formset_form(self, form):
        obj = form.save(commit=False)
        obj.note = note
        obj.creator = request.user
        obj.save()

@login_required
@revision.create_on_success
def document_admin(request, document_id=None):
    o = {}
    instance = document_id and get_object_or_404(main_models.Document,
                                                 id=document_id)
    form = main_forms.DocumentForm
    formsets = (
        main_forms.TopicAssignmentFormset,
        main_forms.DocumentLinkFormset,
        main_forms.ScanFormset,
    )

    if request.is_ajax() and request.method == 'POST' and instance is None:
        o['form'] = main_forms.DocumentForm(request.POST)
        if o['form'].is_valid():
            document = o['form'].save(commit=False)
            document.creator = request.user
            document.last_updater = request.user
            document.save()
            o['form'].save_zotero_data()
            return http.HttpResponse(json.dumps(
                {'description': document.as_html(), 'id': document.id}))
        else:
            return http.HttpResponse(json.dumps(o['form'].errors))

    if request.method == 'POST':
        o['form'], o['formsets'] = collect_forms(form, formsets,
                                                 data=request.POST,
                                                 files=request.FILES,
                                                 instance=instance)
        if forms_are_valid(o['form'], o['formsets']):
            document = o['form'].save(commit=False)
            if not document.id:
                document.creator = request.user
            document.last_updater = request.user
            document.save()

            o['form'].save_zotero_data()

            for formset in o['formsets']:
                for form in formset:
                    if not form.has_changed() or not form.is_valid():
                        continue
                    if form.cleaned_data['DELETE']:
                        if form.instance and form.instance.id:
                            form.instance.delete()
                        continue

                    if formset.prefix == 'topicassignment':
                        save_topic_form(form, document, request.user)
                    else:
                        obj = form.save(commit=False)
                        obj.document = document
                        obj.creator = request.user
                        obj.save()
            messages.add_message(
                request, messages.SUCCESS, 'Document %s %s' % (
                    document.as_text(), 'changed' if instance else 'added'))
            return http.HttpResponseRedirect(document.get_absolute_url())
    else:
        o['form'], o['formsets'] = collect_forms(form, formsets, instance=instance)
    return render_to_response(
        'admin/document_%s.html' % ('change' if document_id else 'add'),
        o, context_instance=RequestContext(request))

@login_required
@revision.create_on_success
def note_admin(request, note_id=None):
    o = {}
    instance = note_id and get_object_or_404(main_models.Note, id=note_id)

    form = main_forms.NoteForm
    formsets = (
        main_forms.TopicAssignmentFormset,
    )

    if request.method == 'POST':
        o['form'], o['formsets'] = collect_forms(form, formsets,
                                                 data=request.POST,
                                                 instance=instance)
        o['form'].fields['assigned_users'].queryset=\
                main_models.UserProfile.objects.filter(
                    affiliation=request.user.get_profile().affiliation,
                    user__is_active=1).order_by('user__last_name')
        if forms_are_valid(o['form'], o['formsets']):
            note = o['form'].save(commit=False)
            if not note.id:
                note.creator = request.user
            note.last_updater = request.user
            note.save()
            o['form'].save_m2m()

            for formset in o['formsets']:
                for form in formset:
                    if not form.has_changed() or not form.is_valid():
                        continue
                    if form.cleaned_data['DELETE']:
                        if form.instance and form.instance.id:
                            form.instance.delete()
                        continue
                    if formset.prefix == 'topicassignment':
                        save_topic_form(form, note, request.user)

            messages.add_message(
                request, messages.SUCCESS, 'Note %s %s' % (
                    note.title, 'changed' if instance else 'added'))
            return http.HttpResponseRedirect(note.get_absolute_url())
    else:
        o['form'], o['formsets'] = collect_forms(form, formsets, instance=instance)
        o['form'].fields['assigned_users'].queryset=\
                main_models.UserProfile.objects.filter(
                    affiliation=request.user.get_profile().affiliation,
                    user__is_active=1).order_by('user__last_name')
    return render_to_response(
        'admin/note_%s.html' % ('change' if note_id else 'add'),
        o, context_instance=RequestContext(request))

@revision.create_on_success
def note_sections(request, note_id):
    note = get_object_or_404(main_models.Note, id=note_id)
    o = {}
    o['note'] = note
    if request.method == 'POST':
        o['sections_formset'] = main_forms.NoteSectionFormset(
            request.POST, instance=note, auto_id=False)
        if o['sections_formset'].is_valid():
            for form in o['sections_formset']:
                if not form.has_changed() or not form.is_valid():
                    continue
                if form.cleaned_data['DELETE']:
                    if form.instance and form.instance.id:
                        form.instance.delete()
                    continue
                obj = form.save(commit=False)
                if not obj.id:
                    obj.creator = request.user
                obj.last_updater = request.user
                obj.save()
            reversion.set_user(request.user)
            reversion.set_comment('Note sections changed')
            messages.add_message(
                request, messages.SUCCESS, 'Note %s updated' % note.title)
            return http.HttpResponseRedirect(note.get_absolute_url())
    else:
        o['sections_formset'] = main_forms.NoteSectionFormset(instance=note,
                                                              auto_id=False)
    return render_to_response(
        'admin/note-sections.html', o, context_instance=RequestContext(request))


###########################################################################
# Project management
###########################################################################

@login_required
@reversion.revision.create_on_success
def project_roster(request, project_id):
    o = {}
    project = get_object_or_404(main_models.Project, id=project_id)
    user = request.user

    # Test user permissions
    if not project.attempt('view', user):
        return http.HttpResponseForbidden(
            content='You do not have permission to view the roster of %s' % project.name)
    o['can_change'] = project.attempt('change', user)

    # Save project roster
    if request.method == 'POST':
        if not o['can_change']:
            messages.add_message(request, messages.ERROR,
                                 'Cannot edit project roster')
        else:
            formset = main_forms.ProjectUserFormSet(request.POST)
            if formset.is_valid():
                for form in formset:
                    form.project = project
                formset.save()
                messages.add_message(request, messages.SUCCESS,
                                     'Roster for %s saved.' % (project.name))
                return http.HttpResponseRedirect(request.path)
            else:
                #TODO
                pass

    # Render project form, disabling inputs if user can't change them
    project_roster = User.objects.filter(userprofile__affiliation=project)\
            .order_by('-is_active', '-last_login')
    o['formset'] = main_forms.ProjectUserFormSet(queryset=project_roster)
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
@reversion.revision.create_on_success
def change_project(request, project_id):
    o = {}
    project = get_object_or_404(main_models.Project, id=project_id)
    user = request. user

    if not project.attempt('change', user):
        return http.HttpResponseForbidden(
            content='You do not have permission to edit the details of %s' % project.name)

    if request.method == 'POST':
        form = main_forms.ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Details of %s saved.' % (project.name))
            redirect = request.GET.get('return_to', request.path)
            return http.HttpResponseRedirect(redirect)
        else:
            pass
    o['form'] = main_forms.ProjectForm(instance=project)
    return render_to_response(
        'admin/project_change.html', o, context_instance=RequestContext(request))

@login_required
@reversion.revision.create_on_success
def change_featured_items(request, project_id):
    o = {}
    project = get_object_or_404(main_models.Project, id=project_id)
    user = request.user

    try:
        project.attempt('change', user)
    except main_models.PermissionError:
        msg = 'You do not have permission to access this page'
        return http.HttpResponseForbidden(content=msg)

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
                return http.HttpResponseRedirect(redirect)
            main_models.FeaturedItem.objects.create(content_object=obj,
                                        project=project,
                                        creator=request.user)
        if deleted:
            main_models.FeaturedItem.objects.filter(project=project, id__in=deleted).delete()
        messages.add_message(request, messages.SUCCESS, 'Featured items saved.')
        return http.HttpResponseRedirect(redirect)

    return render_to_response(
        'admin/featured_items_change.html', o, context_instance=RequestContext(request))

