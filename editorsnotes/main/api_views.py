from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from haystack.query import SearchQuerySet, EmptySearchQuerySet
from models import *
import json

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
        if request.GET.get('project_id'):
            query += ' AND project_id:%s' % request.GET.get('project_id')
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
        if request.GET.get('project_id'):
            query += ' AND project_id:%s' % request.GET.get('project_id')
        results = SearchQuerySet().models(Document).narrow(query).load_all()
    
    documents = [ document_to_dict(r.object) for r in results ]
    return HttpResponse(json.dumps(documents), mimetype='text/plain')

def api_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    return HttpResponse(json.dumps(document_to_dict(document)), mimetype='text/plain')

def note_to_dict(note):
    return { 'title': note.title,
             'id': note.id,
             'uri': 'http://%s%s' % (Site.objects.get_current().domain,
                                     note.get_absolute_url()) }

def api_notes(request):
    query = ''
    results = EmptySearchQuerySet()

    if request.GET.get('q'):
        query = ' AND '.join([ 'title:%s*' % term for term 
                               in request.GET.get('q').split() 
                               if len(term) > 1 ])
        if request.GET.get('project_id'):
            query += ' AND project_id:%s' % request.GET.get('project_id')
        results = SearchQuerySet().models(Note).narrow(query).load_all()

    notes = [ note_to_dict(r.object) for r in results ]
    return HttpResponse(json.dumps(notes), mimetype='text/plain')

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
