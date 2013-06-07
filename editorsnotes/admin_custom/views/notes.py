# -*- coding: utf-8 -*-

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
import reversion

from editorsnotes.main.models.notes import Note

from .. import forms
from common import BaseAdminView

class NoteAdminView(BaseAdminView):
    model = Note
    form_class = forms.NoteForm
    formset_classes = (
        # forms.TopicAssignmentFormset,
    )
    template_name = 'note_admin.html'
    def set_additional_object_properties(self, obj):
        obj.project = self.project
        return obj
    def get_form(self, form_class):
        form = form_class(**self.get_form_kwargs())
        form.fields['assigned_users'].queryset = self.project.members.all()
        return form
    def get_object(self, note_id=None):
        return note_id and get_object_or_404(
            Note, id=note_id, project_id=self.project.id)
    def save_formset_form(self, form):
        obj = form.save(commit=False)
        obj.note = self.object
        obj.creator = self.request.user
        obj.save()

@reversion.create_revision()
def note_sections(request, project_slug, note_id):
    note = get_object_or_404(
        Note, id=note_id, project__slug=project_slug)
    o = {}
    o['note'] = note
    if request.method == 'POST':
        o['citations_formset'] = forms.CitationFormset(
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
            return HttpResponseRedirect(note.get_absolute_url())
    else:
        o['citations_formset'] = forms.CitationFormset(
            prefix='citation', instance=note)
    return render_to_response(
        'note_sections_admin.html', o, context_instance=RequestContext(request))


