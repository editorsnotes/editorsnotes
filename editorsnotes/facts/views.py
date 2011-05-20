from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from editorsnotes.main.models import Topic
import urllib

@login_required
def topic_facts(request, topic_slug):
    o = {}
    o['topic'] = get_object_or_404(Topic, slug=topic_slug)
    response = urllib.urlopen(
        'http://sameas.org/json?q=%s' % 
        urllib.urlencode({ 'q': o['topic'].preferred_name }))
    return HttpResponse(response.read(), mimetype='text/plain')
