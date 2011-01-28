from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
#from django.core.paginator import Paginator, InvalidPage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from haystack.query import SearchQuerySet, EmptySearchQuerySet
from urllib import urlopen
from models import *
import utils
import json

def _sort_citations(instance):
    cites = { 'primary': [], 'secondary': [] }
    for c in Citation.objects.filter(
        content_type=ContentType.objects.get_for_model(instance), 
        object_id=instance.id):
        if c.type == 'P': cites['primary'].append(c)
        elif c.type == 'S': cites['secondary'].append(c)
    cites['primary'].sort(key=lambda c: c.document.ordering)
    cites['secondary'].sort(key=lambda c: c.document.ordering)
    return cites

@login_required
def index(request, project_slug=None):
    max_count = 6
    o = {}
    if project_slug:
        o['project'] = get_object_or_404(Project, slug=project_slug)
        print o['project'].get_absolute_url()
    o['user_activity'], skip_object_ids = UserProfile.get_activity_for(
        request.user, max_count)
    for model in [Topic, Note, Document, Transcript]:
        model_name = model._meta.module_name
        if model_name == 'transcript':
            listname = 'document_list'
        else:
            listname = '%s_list' % model_name
        query_set = model.objects\
                .exclude(id__in=skip_object_ids[model_name])\
                .order_by('-last_updated')
        if project_slug:
            query_set = query_set.filter(
                last_updater__userprofile__affiliation=o['project'])
        o[listname] = list(query_set[:max_count])
    o['document_list'] = sorted(o['document_list'],
                              key=lambda x: x.last_updated, 
                              reverse=True)[:max_count]
    return render_to_response(
        'index.html', o, context_instance=RequestContext(request))

@login_required
def all_topics(request, project_slug=None):
    o = {}
    if project_slug:
        o['project'] = get_object_or_404(Project, slug=project_slug)
    o['topics_1'] = []
    o['topics_2'] = []
    o['topics_3'] = []
    #if project_slug:
    #    query_set = Topic.objects.filter(
    #        last_updater__userprofile__affiliation=o['project'])
    #else:
    query_set = Topic.objects.all()
    all_topics = list(query_set)
    prev_letter = 'A'
    topic_index = 1
    list_index = 1 
    for topic in all_topics:
        first_letter = topic.slug[0].upper()
        if not first_letter == prev_letter:
            if list_index < 3 and topic_index > (len(all_topics) / 3.0):
                topic_index = 1
                list_index += 1
            prev_letter = first_letter
        o['topics_%s' % list_index].append(
            { 'topic': topic, 'first_letter': first_letter })
        topic_index += 1
    return render_to_response(
        'all-topics.html', o, context_instance=RequestContext(request))

@login_required
def all_documents(request, project_slug=None):
    o = {}
    if project_slug:
        o['project'] = get_object_or_404(Project, slug=project_slug)
    o['documents'] = []
    if project_slug:
        query_set = Document.objects.filter(
            last_updater__userprofile__affiliation=o['project'])
    else:
        query_set = Document.objects.all()
    for document in query_set:
        first_letter = document.ordering[0].upper()
        o['documents'].append(
            { 'document': document, 'first_letter': first_letter })
    return render_to_response(
        'all-documents.html', o, context_instance=RequestContext(request))

@login_required
def all_notes(request, project_slug=None):
    o = {}
    if project_slug:
        o['project'] = get_object_or_404(Project, slug=project_slug)
    if project_slug:
        query_set = Note.objects.filter(
            last_updater__userprofile__affiliation=o['project'])
    else:
        query_set = Note.objects.all()
    # TODO: Make this a custom manager method for Note, maybe
    notes = dict((n.id, n) for n in query_set)
    o['notes_by_topic_1'] = []
    o['notes_by_topic_2'] = []
    topic_assignments = [ ta for ta in 
                          TopicAssignment.objects.assigned_to_model(Note) 
                          if ta.object_id in notes ]
    ta_index = 1
    list_index = 1
    topic = None
    categorized_note_ids = set()
    for ta in topic_assignments:
        if topic and not ta.topic.slug == topic['slug']:
            o['notes_by_topic_%s' % list_index].append(topic)
            topic = None
            if list_index < 2 and ta_index > (len(topic_assignments) / 2.2):
                ta_index = 1
                list_index += 1        
        if not topic:
            topic = { 'slug': ta.topic.slug, 
                      'name': ta.topic.preferred_name, 
                      'notes': [] }
        topic['notes'].append(notes[ta.object_id])
        categorized_note_ids.add(ta.object_id)
        ta_index += 1
    uncategorized_notes = []
    for note_id in (set(notes.keys()) - categorized_note_ids):
        uncategorized_notes.append(notes[note_id])
    o['notes_by_topic_1'].insert(0, { 'slug': 'uncategorized',
                                      'name': 'uncategorized', 
                                      'notes': uncategorized_notes })
    return render_to_response(
        'all-notes.html', o, context_instance=RequestContext(request))

@login_required
def topic(request, topic_slug):
    o = {}
    o['topic'] = get_object_or_404(Topic, slug=topic_slug)
    o['contact'] = { 'name': settings.ADMINS[0][0], 
                     'email': settings.ADMINS[0][1] }
    o['related_topics'] = o['topic'].related_topics.all()
    o['summary_cites'] = _sort_citations(o['topic'])
    notes = o['topic'].related_objects(Note)
    o['notes'] = zip(notes, 
                    [ [ ta.topic for ta in n.topics.exclude(topic=o['topic']) ] for n in notes ],
                    [ _sort_citations(n) for n in notes ])
    o['documents'] = o['topic'].related_objects(Document)
    o['thread'] = { 'id': 'topic-%s' % o['topic'].id, 'title': o['topic'].preferred_name }
    return render_to_response(
        'topic.html', o, context_instance=RequestContext(request))

@login_required
def note(request, note_id):
    o = {}
    o['note'] = get_object_or_404(Note, id=note_id)
    o['topics'] = [ ta.topic for ta in o['note'].topics.all() ]
    o['cites'] = _sort_citations(o['note'])
    return render_to_response(
        'note.html', o, context_instance=RequestContext(request))

@login_required
def footnote(request, footnote_id):
    o = {}
    o['footnote'] = get_object_or_404(Footnote, id=footnote_id)
    o['thread'] = { 'id': 'footnote-%s' % o['footnote'].id, 
                    'title': o['footnote'].footnoted_text() }
    return render_to_response(
        'footnote.html', o, context_instance=RequestContext(request))

@login_required
def document(request, document_id):
    o = {}
    o['document'] = get_object_or_404(Document, id=document_id)
    o['topics'] = (
        [ ta.topic for ta in o['document'].topics.all() ] +
        [ c.content_object for c in o['document'].citations.filter(
                content_type=ContentType.objects.get_for_model(Topic)) ])
    o['scans'] = o['document'].scans.all()
    o['domain'] = Site.objects.get_current().domain
    notes = [ c.content_object for c in o['document'].citations.filter(
            content_type=ContentType.objects.get_for_model(Note)) ]
    o['notes'] = zip(notes, 
                     [ [ ta.topic for ta in n.topics.all() ] for n in notes ],
                     [ _sort_citations(n) for n in notes ])    
    return render_to_response(
        'document.html', o, context_instance=RequestContext(request))

@login_required
def user(request, username=None):
    o = {}
    if not username:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)
    o['profile'] = UserProfile.get_for(user)
    o['log_entries'], ignored = UserProfile.get_activity_for(user)
    return render_to_response(
        'user.html', o, context_instance=RequestContext(request))

@login_required
def search(request):
    query = ''
    results = EmptySearchQuerySet()

    if request.GET.get('q'):
        query = request.GET.get('q')
        results = SearchQuerySet().auto_query(query).load_all()

    # paginator = Paginator(results, 20)
    
    # try:
    #     page = paginator.page(int(request.GET.get('page', 1)))
    # except InvalidPage:
    #     raise Http404('No such page of results!')
    
    o = {
        # 'page': page,
        # 'paginator': paginator,
        'results': results,
        'query': query,
    }
    
    return render_to_response(
        'search.html', o, context_instance=RequestContext(request))

def api_topics(request):
    query = ''
    results = EmptySearchQuerySet()

    if request.GET.get('q'):
        query = ' AND '.join([ 'names:%s' % term for term 
                               in request.GET.get('q').split() 
                               if len(term) > 1 ])
        results = SearchQuerySet().models(Topic).narrow(query).load_all()
    
    topics = [ { 'preferred_name': r.object.preferred_name,
                 'uri': 'http://%s%s' % (Site.objects.get_current().domain, 
                                         r.object.get_absolute_url()) } 
               for r in results ]
    return HttpResponse(json.dumps(topics), mimetype='text/plain')

# Proxy for cross-site AJAX requests. For development only.
def proxy(request):
    url = request.GET.get('url')
    if url is None:
        return HttpResponseBadRequest()
    if not url.startswith('http://cache.zoom.it/'):
        return HttpResponseForbidden()
    return HttpResponse(urlopen(url).read(), mimetype='application/xml')
