from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
import json
from models import Task, Comment

@login_required
def task(request, task_id):
    o = {}
    o['task'] = Task.objects.get(id=task_id)
    return render_to_response(
        'task.html', o, context_instance=RequestContext(request))

def all_tasks(request):
    o = {}
    o['tasks'] = Task.objects.all()
    return render_to_response(
        'all-tasks.html', o, context_instance=RequestContext(request))

def add_comment(request, task_id):
    o = {}
    u = request.user
    message = request.POST.get('comment-text', '')
    attachments = request.POST.getlist('attachment')
    if message:
        c = Comment.objects.create(creator=u,
                                   task=Task.objects.get(id=task_id),
                                   text=message)
        c.save()
        o['status'] = 'ok'
        o['new_comment'] = c.text
    else:
        o['status'] = 'broke'
    raise Exception
    return HttpResponse(json.dumps(o), mimetype='text/plain')
