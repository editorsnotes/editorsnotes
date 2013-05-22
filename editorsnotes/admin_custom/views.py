from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import View, ModelFormMixin, TemplateResponseMixin

from editorsnotes.main import models as main_models
import forms as admin_forms

import reversion
import json

VIEW_ERROR_MSG = 'You do not have permission to view {}.'
CHANGE_ERROR_MSG = 'You do not have permission to change {}.'

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
        for fs in formsets:
            valid = formsets[fs].is_valid()
        if all([form.is_valid()] + map(lambda fs: formsets[fs].is_valid(), formsets)):
            return self.form_valid(form, formsets)
        else:
            return self.form_invalid(form, formsets)

    def collect_formsets(self):
        fs = {}
        if hasattr(self, 'formset_classes'):
            for formset in self.formset_classes:
                prefix = formset.model._meta.module_name

                fs_kwargs = self.get_form_kwargs()
                fs_kwargs.pop('initial', 0)
                fs_kwargs['prefix'] = prefix

                fs[prefix] = formset(**fs_kwargs)
        return fs
    def save_formsets(self, formsets):
        for fs in formsets.values():
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
        if self.object and not self.object.attempt('change', self.request.user):
            return http.HttpResponseForbidden(CHANGE_ERROR_MSG.format(object))
        return super(BaseAdminView, self).get(request, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object(**kwargs)
        if self.object and not self.object.attempt('change', self.request.user):
            return http.HttpResponseForbidden(CHANGE_ERROR_MSG.format(object))
        return super(BaseAdminView, self).post(request, *args, **kwargs)

    def get_object(self):
        raise NotImplementedError(
            'Child views must create get_object method')
    def get_form_kwargs(self):
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        if hasattr(self, 'object') and self.object:
            kwargs.update({'instance': self.object})
        return kwargs

    def save_object(self, form, formsets):
        obj = form.save(commit=False)
        action = 'add' if not obj.id else 'change'
        if action == 'add':
            obj.creator = self.request.user
        obj.last_updater = self.request.user
        obj.save()
        return obj, action

    def form_valid(self, form, formsets):
        with reversion.create_revision():
            self.object, action = self.save_object(form, formsets)

            # Set reversion metadata
            reversion.set_user(self.request.user)
            reversion.set_comment('%sed %s.' % (action, self.object._meta.module_name))

            # Now save models that depend on this object existing
            self.object.affiliated_projects.add(
                *main_models.Project.get_affiliation_for(self.request.user))
            self.save_formsets(formsets)
            form.save_m2m()

        return redirect(self.get_success_url())
    def form_invalid(self, form, formsets):
        return self.render_to_response(
            self.get_context_data(form=form, formsets=formsets))

    def save_topicassignment_formset_form(self, form):
        if not form.cleaned_data['topic']:
            return
        if form.instance and form.instance.id:
            return
        if form.cleaned_data['topic'] in self.object.topics.all():
            return
        ta = form.save(commit=False)
        ta.creator = self.request.user
        ta.topic = form.cleaned_data['topic']
        ta.content_object = self.object
        ta.save()
        return ta

class DocumentAdminView(BaseAdminView):
    form_class = admin_forms.DocumentForm
    formset_classes = (
        admin_forms.TopicAssignmentFormset,
        admin_forms.DocumentLinkFormset,
        admin_forms.ScanFormset
    )
    template_name = 'document_admin.html'
    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            return self.ajax_post(request, *args, **kwargs)
        return super(DocumentAdminView, self).post(request, *args, **kwargs)

    def get_object(self, document_id=None):
        return document_id and get_object_or_404(main_models.Document, id=document_id)

    def save_object(self, form, formsets):
        obj, action = super(DocumentAdminView, self).save_object(form, formsets)
        form.save_zotero_data()
        return obj, action

    def save_formset_form(self, form):
        obj = form.save(commit=False)
        obj.document = self.object
        obj.creator = self.request.user
        obj.save()
        return obj

    def ajax_post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        self.object = self.get_object()
        if self.object is not None:
            return http.HttpResponse(
                'Cannot save existing documents via ajax.', status=400)
        if form.is_valid():
            with reversion.create_revision():
                document = form.save(commit=False)
                document.creator = self.request.user
                document.last_updater = self.request.user
                document.save()
                form.save_zotero_data()
            return http.HttpResponse(json.dumps(
                {'value': document.as_text(),
                 'id': document.id}
            ))
        else:
            return http.HttpResponse(json.dumps(form.errors), status=400)

class NoteAdminView(BaseAdminView):
    form_class = admin_forms.NoteForm
    formset_classes = (
        admin_forms.TopicAssignmentFormset,
    )
    template_name = 'note_admin.html'
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
        obj.note = self.object
        obj.creator = self.request.user
        obj.save()

class TopicAdminView(BaseAdminView):
    form_class = admin_forms.TopicForm
    formset_classes = (
        admin_forms.TopicAssignmentFormset,
        admin_forms.AliasFormset,
        admin_forms.CitationFormset,
    )
    template_name = 'topic_admin.html'
    def get_object(self, topic_id=None):
        return topic_id and get_object_or_404(main_models.Topic, id=topic_id)
    def save_citation_formset_form(self, form):
        obj = form.save(commit=False)
        if not obj.id:
            obj.content_object = self.object
            obj.creator = self.request.user
        obj.last_updater = self.request.user
        obj.save()

class TranscriptAdminView(BaseAdminView):
    form_class = admin_forms.TranscriptForm
    formset_classes = (
        admin_forms.FootnoteFormset,
    )
    template_name = 'transcript_admin.html'
    def get(self, request, *args, **kwargs):
        response = super(TranscriptAdminView, self).get(request, *args, **kwargs)

        footnote_fs = response.context_data['formsets']['footnote']
        footnote_ids = self.object.get_footnote_href_ids()

        footnote_fs.forms.sort(key=lambda fn: footnote_ids.index(fn.instance.id)
                               if fn.instance.id in footnote_ids else 9999)

        return response
    def get_object(self, transcript_id=None):
        return transcript_id and get_object_or_404(
            main_models.Transcript, id=transcript_id)
    def save_object(self, form, formsets):
        obj = form.save(commit=False)
        action = 'add' if not obj.id else 'change'
        if action == 'add':
            obj.creator = self.request.user
            obj.document = self.document
        obj.last_updater = self.request.user
        obj.save()
        return obj, action
    def save_footnote_formset_form(self, form):
        footnote = form.save(commit=False)
        transcript = self.object
        stamp = form.cleaned_data.get('stamp', None)

        if not footnote.id:
            footnote.transcript = transcript
            footnote.creator = self.request.user
        footnote.last_updater = self.request.user
        footnote.save()

        if stamp:
            a = transcript.content.cssselect('a.footnote[href$="%s"]' % stamp)[0]
            a.attrib['href'] = footnote.get_absolute_url()
            transcript.save()


@reversion.create_revision()
def note_sections(request, note_id):
    note = get_object_or_404(main_models.Note, id=note_id)
    o = {}
    o['note'] = note
    if request.method == 'POST':
        o['citations_formset'] = admin_forms.CitationFormset(
            request.POST, instance=note, prefix='citation')
        if o['citations_formset'].is_valid():
            for form in o['citations_formset']:
                if not form.has_changed() or not form.is_valid():
                    continue
                if form.cleaned_data['DELETE']:
                    if form.instance and form.instance.id:
                        form.instance.delete()
                    continue
                obj = form.save(commit=False)
                if not obj.id:
                    obj.content_object = note
                    obj.creator = request.user
                obj.last_updater = request.user
                obj.save()
            reversion.set_user(request.user)
            reversion.set_comment('Note sections changed')
            messages.add_message(
                request, messages.SUCCESS, 'Note %s updated' % note.title)
            return http.HttpResponseRedirect(note.get_absolute_url())
    else:
        o['citations_formset'] = admin_forms.CitationFormset(
            prefix='citation', instance=note)
    return render_to_response(
        'note_sections_admin.html', o, context_instance=RequestContext(request))


###########################################################################
# Project management
###########################################################################

@login_required
@reversion.create_revision()
def project_roster(request, project_id):
    o = {}
    user = request.user
    project = get_object_or_404(main_models.Project, id=project_id)
    can_change = project.attempt('change', user)
    ProjectRosterFormSet = admin_forms.make_project_roster_formset(project)
    ProjectInvitationFormSet = admin_forms.make_project_invitation_formset(project)
    if not project.attempt('view', user):
        return http.HttpResponseForbidden(VIEW_ERROR_MSG.format(project))

    if request.method == 'POST':
        if not can_change:
            return http.HttpResponseForbidden(CHANGE_ERROR_MSG.format(project))
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
            return http.HttpResponseRedirect(request.path)
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
    project = get_object_or_404(main_models.Project, id=project_id)
    user = request. user

    if not project.attempt('change', user):
        return http.HttpResponseForbidden(
            content='You do not have permission to edit the details of %s' % project.name)

    if request.method == 'POST':
        form = admin_forms.ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Details of %s saved.' % (project.name))
            redirect = request.GET.get('return_to', request.path)
            return http.HttpResponseRedirect(redirect)
        else:
            pass
    o['form'] = admin_forms.ProjectForm(instance=project)
    return render_to_response(
        'project_change.html', o, context_instance=RequestContext(request))

@login_required
@reversion.create_revision()
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
            main_models.FeaturedItem.objects\
                .filter(project=project, id__in=deleted)\
                .delete()
        messages.add_message(request, messages.SUCCESS, 'Featured items saved.')
        return http.HttpResponseRedirect(redirect)

    return render_to_response(
        'featured_items_admin.html', o, context_instance=RequestContext(request))

