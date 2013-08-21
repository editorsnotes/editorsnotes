from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic.edit import View, ModelFormMixin, TemplateResponseMixin
import reversion

from editorsnotes.main import models as main_models

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
            save_method = (
                getattr(self, 'save_%s_formset_form' % fs.prefix, None)
                or self.save_formset_form)
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
###########################################################################
# Project management
###########################################################################
