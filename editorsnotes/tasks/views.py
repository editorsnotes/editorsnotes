from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
import json
from models import Task, TaskComment, AttachmentAssignment
from editorsnotes.main.models import Note, Topic, Document
from editorsnotes.main.views import _sort_citations

@login_required
def task(request, task_id):
    o = {}
    o['task'] = Task.objects.get(id=task_id)
    o['user'] = request.user
    notes_query = o['task'].attachments.filter(content_type__name='note')
    notes = [note.content_object for note in notes_query]
    note_topics = [ [ ta.topic for ta in n.topics.all() ] for n in notes ]
    note_citations = [ _sort_citations(n) for n in notes ]
    o['notes'] = zip(notes, note_topics, note_citations)
    return render_to_response(
        'task.html', o, context_instance=RequestContext(request))

def all_tasks(request):
    o = {}
    o['tasks'] = Task.objects.all()
    return render_to_response(
        'all-tasks.html', o, context_instance=RequestContext(request))

def add_comment(request, task_id):
    u = request.user
    message = request.POST.get('comment-text', '')
    attachments = request.POST.getlist('attachment')
    parent_task = Task.objects.get(id=task_id)
    if message:
        c = TaskComment.objects.create(creator=u,
                                   task=parent_task,
                                   text=message)
        c.save()
    else:
        #TODO: blank comments
        pass
    for attachment in attachments:
        if not attachment:
            continue
        attachment_type = attachment.split(' ')[0]
        attachment_id = int(attachment.split(' ')[1])
        if attachment_type == 'notes':
            o = Note.objects.get(id=attachment_id)
        elif attachment_type == 'documents':
            o = Document.objects.get(id=attachment_id)
        elif attachment_type == 'topics':
            o = Topic.objects.get(id=attachment_id)
        else:
            continue
        assignment = AttachmentAssignment.objects.create(
            content_object = o,
            comment = c,
            task = parent_task,
            creator = request.user
            )
        assignment.save()
    return_url = request.GET.get('return_to', '/')
    return HttpResponseRedirect(return_url)
