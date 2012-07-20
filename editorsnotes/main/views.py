from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
#from django.core.paginator import Paginator, InvalidPage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from haystack.query import SearchQuerySet, EmptySearchQuerySet
from reversion import get_unique_for_object
from urllib import urlopen
from models import *
from editorsnotes.djotero.utils import as_readable, type_map
from editorsnotes.refine.models import TopicCluster
import forms as main_forms
import utils
import json
import re

def _sort_citations(instance):
    cites = { 'all': [] }
    for c in Citation.objects.filter(
        content_type=ContentType.objects.get_for_model(instance), 
        object_id=instance.id):
        cites['all'].append(c)
    cites['all'].sort(key=lambda c: c.ordering)
    return cites

@login_required
def index(request):
    o = {}
    return render_to_response(
        'index.html', o, context_instance=RequestContext(request))

@login_required
def browse(request):
    max_count = 6
    o = {}
    for model in [Topic, Note, Document]:
        model_name = model._meta.module_name
        listname = '%s_list' % model_name
        query_set = model.objects.order_by('-last_updated')

        items = list(query_set[:max_count])
        o[listname] = items
    o['projects'] = Project.objects.all().order_by('name')
    return render_to_response(
        'browse.html', o, context_instance=RequestContext(request))

@login_required
def project(request, project_slug):
    o = {}
    o['project'] = get_object_or_404(Project, slug=project_slug)
    try:
        o['can_change'] = o['project'].attempt('change', request.user)
    except PermissionError:
        pass
    o['project_role'] = request.user.get_profile().get_project_role(
        o['project'])
    return render_to_response(
        'project.html', o, context_instance=RequestContext(request))

@login_required
def all_topics(request, project_slug=None):
    o = {}
    if project_slug:
        o['project'] = get_object_or_404(Project, slug=project_slug)
    if 'type' in request.GET:
        o['type'] = request.GET['type']
        o['fragment'] = ''
        template = 'topic-columns.include'
    else:
        o['type'] = 'PER'
        template = 'all-topics.html'
    if project_slug:
        query_set = set([ ta.topic for ta in TopicAssignment.objects.filter(
            creator__userprofile__affiliation=o['project'],
            topic__type=o['type']) ])
    else:
        query_set = Topic.objects.filter(type=o['type'])
    [o['topics_1'], o['topics_2'], o['topics_3']] = utils.alpha_columns(
        query_set, 'slug', itemkey='topic')
    return render_to_response(
        template, o, context_instance=RequestContext(request))

@login_required
def all_documents(request, project_slug=None):
    o = {}
    template = 'all-documents.html'
    o['filtered'] = False

    if request.GET.get('filter'):
        template = 'filtered-documents.html'
        o['filtered'] = True

    valid_facets = [
        'project_id',
        'related_topic_id',
        'archive',
        'publicationTitle',
        'itemType',
        'creators'
    ]


    # Narrow search query according to GET parameters
    qs = SearchQuerySet().models(Document)
    params = set.intersection(set(valid_facets), set(request.GET))
    query = []
    for param in params:
        query_filter = [ '%s:"%s"' % (param, val) for val
                        in request.GET.get(param).split('|') ]
        query += [ ' AND '.join(query_filter)]
    qs = qs.narrow(' AND '.join(query)) if query else qs

    # Facet results
    for f in valid_facets:
        qs = qs.facet(f)

    # Pass facets to template
    o['facets'] = {}
    facet_counts = qs.facet_counts()['fields'] 
    for facet in facet_counts:

        # Leave out facets with no more than one choice that are not selected
        if len(facet_counts[facet]) == 1 and \
           facet_counts[facet][0][0] == None and \
           facet not in params:
            continue
        
        # Sort results & limit to 30
        sorted_facets = sorted(facet_counts[facet],
                               key=lambda x: x[1],
                               reverse=True)
        sorted_facets = sorted_facets[:30]

        # Specific actions for individual facets.
        # Tuple represents one input: value, label, count
        if facet == 'project_id':
            o['facets']['project_id'] = [ (p_id, Project.objects.get(id=p_id), count)
                                      for p_id, count in sorted_facets ]
        elif facet == 'related_topic_id':
            o['facets']['related_topic_id'] = \
                    [ (t_id, Topic.objects.get(id=t_id), count)
                     for t_id, count in sorted_facets ]
        elif facet =='itemType':
            o['facets']['itemType'] = [ (item, type_map['readable'].get(item), count)
                                       for item, count in sorted_facets ]
        else:
            o['facets'][facet] = [ (f, f, count)
                                  for f, count in sorted_facets if f ]

    o['documents'] = qs 
    o['query'] = query
    return render_to_response(
        template, o, context_instance=RequestContext(request))

@login_required
def all_notes(request, project_slug=None):
    o = {}
    template = 'all-notes.html'
    o['filtered'] = False

    if request.GET.get('filter'):
        template = 'filtered-notes.html'
        o['filtered'] = True

    qs = SearchQuerySet().models(Note)
    query = []
    if request.GET.get('topic'):
        query += [ ' AND '.join([ 'related_topic_id:%s' % topic for topic
                                in request.GET.get('topic').split(',') ]) ]
    if request.GET.get('project'):
        query += [ ' AND '.join([ 'project_id:%s' % project for project
                                in request.GET.get('project').split(',') ]) ]
    qs = qs.narrow(' AND '.join(query)) if query else qs

    qs = qs.facet('related_topic_id').facet('project_id')
    facet_fields = qs.facet_counts()['fields']
    topic_facets = sorted(facet_fields['related_topic_id'],
                          key=lambda t: t[1], reverse=True)
    project_facets = sorted(facet_fields['project_id'],
                            key=lambda p: p[1], reverse=True)

    topic_facets = [ (Topic.objects.get(id=t_id), t_count)
                         for t_id, t_count in topic_facets[:16] ]
    o['topic_facets_1'] = topic_facets[:8]
    o['topic_facets_2'] = topic_facets[8:] if (len(topic_facets) > 8) else []

    o['project_facets'] = [ (Project.objects.get(id=p_id), p_count)
                           for p_id, p_count in project_facets ]
    o['notes'] = qs

    return render_to_response(
        template, o, context_instance=RequestContext(request)) 

@login_required
def topic(request, topic_slug):
    o = {}
    o['topic'] = get_object_or_404(Topic, slug=topic_slug)
    o['contact'] = { 'name': settings.ADMINS[0][0], 
                     'email': settings.ADMINS[0][1] }
    o['related_topics'] = o['topic'].related_topics.all()
    o['summary_cites'] = _sort_citations(o['topic'])

    notes = o['topic'].related_objects(Note)
    note_topics = [ [ ta.topic for ta in n.topics.exclude(topic=o['topic']) ] for n in notes ]
    o['notes'] = zip(notes, note_topics)

    o['documents'] = o['topic'].related_objects(Document)

    o['thread'] = { 'id': 'topic-%s' % o['topic'].id, 'title': o['topic'].preferred_name }
    o['alpha'] = (request.user.groups.filter(name='Alpha').count() == 1)

    return render_to_response(
        'topic.html', o, context_instance=RequestContext(request))

@login_required
def note(request, note_id):
    o = {}
    o['note'] = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        form = main_forms.NoteSectionForm(request.POST)
        user = request.user
        if form.is_valid():

            # Quick fix with checking if a document field is blank: wymeditor by
            # default posts '<br/>'
            if not (request.POST.get('document') or
                    len(request.POST.get('content')) > 6):
                messages.add_message(
                    request, messages.ERROR,
                    'Enter a value for one or both of the fields "Content" and "Description"')
                return HttpResponseRedirect(request.path)

            new_section = NoteSection.objects.create(
                creator=user, last_updater=user, note=o['note'])
            if len(request.POST.get('content')) > 6:
                new_section.content = request.POST.get('content')
            if request.POST.get('document'):
                new_section.document = get_object_or_404(
                    Document, id=request.POST.get('document'))
            new_section.save()

            messages.add_message(
                request,
                messages.SUCCESS,
                'Added section to %s' % o['note'])
            return HttpResponseRedirect(request.path)
    user_profile = request.user.get_profile()
    o['affiliated'] = len([p for p in o['note'].get_project_affiliation() if
                           user_profile.get_project_role(p) is not None]) > 0
    o['add_section_form'] = main_forms.NoteSectionForm()
    o['history'] = get_unique_for_object(o['note'])
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
    if o['document'].zotero_link():
        o['zotero_data'] = as_readable(o['document'].zotero_link().zotero_data)
        o['zotero_url'] = o['document'].zotero_link().zotero_url
        o['zotero_date_information'] = o['document'].zotero_link().date_information
    return render_to_response(
        'document.html', o, context_instance=RequestContext(request))

@login_required
def user(request, username=None):
    o = {}
    if not username:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)
    if user.get_profile().zotero_uid and user.get_profile().zotero_key:
        o['zotero_status'] = True
    else:
        o['zotero_status'] = False
    o['profile'] = UserProfile.get_for(user)
    o['log_entries'], ignored = UserProfile.get_activity_for(user, max_count=20)

    affiliation = o['profile'].affiliation
    if affiliation and (o['profile'].get_project_role(affiliation) == 'editor'
                        or user.is_superuser):
        if user.is_superuser:
            o['clusters'] = TopicCluster.objects.all()
        else:
            o['clusters'] = TopicCluster.objects.filter(
                topics__affiliated_projects=o['profile'].affiliation)
    return render_to_response(
        'user.html', o, context_instance=RequestContext(request))

def user_logout(request):
    logout(request)
    return render_to_response(
        'logout.html', context_instance=RequestContext(request))

reel_numbers = re.compile(r'(\S+):(\S+)')
ignored_punctuation = '!#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

@login_required
def search(request):
    query = ''
    results = EmptySearchQuerySet()

    if request.GET.get('q'):
        query = request.GET.get('q')
        match = reel_numbers.search(query)
        if match:
            # so we can match reel numbers exactly
            query = reel_numbers.sub(r'"\1 \2"', query)
        def filter(c):
            if c in ignored_punctuation: return ' '
            return c
        query = ''.join([filter(c) for c in query])
        if len(query) > 0:
            results = SearchQuerySet().auto_query(query).load_all()
        if match:
            # restore the original form of the query so highlighting works
            query = query.replace('"%s %s"' % match.group(1,2), match.group(0))

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

def topic_to_dict(topic):
    return { 'preferred_name': topic.preferred_name,
             'id': topic.id,
             'uri': 'http://%s%s' % (Site.objects.get_current().domain, 
                                     topic.get_absolute_url()) } 

def api_topics(request):
    query = ''
    results = EmptySearchQuerySet()

    if request.GET.get('q'):
        query = ' AND '.join([ 'names:%s*' % term for term 
                               in request.GET.get('q').split() 
                               if len(term) > 1 ])
        results = SearchQuerySet().models(Topic).narrow(query).load_all()
    
    topics = [ topic_to_dict(r.object) for r in results ]
    return HttpResponse(json.dumps(topics), mimetype='text/plain')

def api_topic(request, topic_ids):
    topics_by_id = Topic.objects.in_bulk(topic_ids.split(','))
    topics = [ topic_to_dict(t) for t in topics_by_id.values() ]
    return HttpResponse(json.dumps(topics), mimetype='text/plain')

def document_to_dict(document):
    return { 'description': document.as_text(),
             'id': document.id,
             'uri': 'http://%s%s' % (Site.objects.get_current().domain, 
                                     document.get_absolute_url()) } 

def api_documents(request):
    query = ''
    results = EmptySearchQuerySet()

    if request.GET.get('q'):
        query = ' AND '.join([ 'title:%s*' % term for term 
                               in request.GET.get('q').split() 
                               if len(term) > 1 ])
        results = SearchQuerySet().models(Document).narrow(query).load_all()
    
    documents = [ document_to_dict(r.object) for r in results ]
    return HttpResponse(json.dumps(documents), mimetype='text/plain')

def api_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    return HttpResponse(json.dumps(document_to_dict(document)), mimetype='text/plain')

def transcript_to_dict(transcript):
    return { 'description': transcript.as_text(),
             'id': transcript.id,
             'uri': 'http://%s%s' % (Site.objects.get_current().domain, 
                                     transcript.get_absolute_url()) } 

def api_transcripts(request):
    query = ''
    results = EmptySearchQuerySet()

    if request.GET.get('q'):
        query = ' AND '.join([ 'title:%s' % term for term 
                               in request.GET.get('q').split() 
                               if len(term) > 1 ])
        results = SearchQuerySet().models(Transcript).narrow(query).load_all()
    
    transcripts = [ transcript_to_dict(r.object) for r in results ]
    return HttpResponse(json.dumps(transcripts), mimetype='text/plain')

def api_transcript(request, transcript_id):
    transcript = get_object_or_404(Transcript, id=transcript_id)
    return HttpResponse(json.dumps(transcript_to_dict(transcript)), mimetype='text/plain')

# Proxy for cross-site AJAX requests. For development only.
def proxy(request):
    url = request.GET.get('url')
    if url is None:
        return HttpResponseBadRequest()
    if not url.startswith('http://cache.zoom.it/'):
        return HttpResponseForbidden()
    return HttpResponse(urlopen(url).read(), mimetype='application/xml')
