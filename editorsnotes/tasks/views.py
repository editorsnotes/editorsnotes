from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
import json
from models import Task, Comment, AttachmentAssignment
from editorsnotes.main.models import Note, Topic, Document

@login_required
def task(request, task_id):
    o = {}
    o['task'] = Task.objects.get(id=task_id)
    o['user'] = request.user
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
    if message:
        c = Comment.objects.create(creator=u,
                                   task=Task.objects.get(id=task_id),
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
            creator = request.user
            )
        assignment.save()
    return_url = request.GET.get('return_to', '/')
    return HttpResponseRedirect(return_url)
