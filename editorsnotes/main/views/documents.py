from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from editorsnotes.djotero.utils import as_readable
from editorsnotes.search import en_index

from ..models.documents import Document, Footnote, Transcript
from ..models.topics import Topic, ProjectTopicContainer
from ..models.notes import CitationNS

def footnote(request, project_slug, document_id, footnote_id):
    o = {}
    o['footnote'] = get_object_or_404(Footnote, id=footnote_id)
    o['thread'] = { 'id': 'footnote-%s' % o['footnote'].id, 
                    'title': o['footnote'].footnoted_text() }
    return render_to_response(
        'footnote.html', o, context_instance=RequestContext(request))

def document(request, project_slug, document_id):
    o = {}
    o['document'] = get_object_or_404(Document, id=document_id)
    o['topics'] = (
        [ ta.container for ta in o['document'].related_topics.all() ] +
        [ c.content_object for c in o['document'].citations.filter(
                content_type=ContentType.objects.get_for_model(ProjectTopicContainer)) ])
    o['scans'] = o['document'].scans.all()
    o['domain'] = Site.objects.get_current().domain

    notes = [ns.note for ns in CitationNS.objects\
            .select_related('note')\
            .filter(document=o['document'])]
    note_topics = [ [ ta.topic for ta in n.related_topics.all() ] for n in notes ]
    o['notes'] = zip(notes, note_topics)

    if o['document'].zotero_data:
        o['zotero_data'] = as_readable(o['document'].zotero_data)
        if o['document'].zotero_link:
            o['zotero_url'] = o['document'].zotero_link.zotero_url
            o['zotero_date_information'] = o['document'].zotero_link.date_information
    return render_to_response(
        'document.html', o, context_instance=RequestContext(request))

def transcript(request, project_slug, document_id):
    transcript = get_object_or_404(Transcript, document_id=document_id)
    return HttpResponse(transcript)

def all_documents(request, project_slug=None):
    o = {}
    template = 'all-documents.html'
    o['filtered'] = False

    if request.GET.get('filter'):
        template = 'filtered-documents.html'
        o['filtered'] = True

    facet_fields = (
        ('project', 'serialized.project.name'),
        ('topic', 'serialized.related_topics.name'),
        ('archive', 'serialized.zotero_data.archive'),
        ('publicationTitle', 'serialized.zotero_data.publicationTitle'),
        ('itemType', 'serialized.zotero_data.itemType'),
        ('creators', 'serialized.zotero_data.creators'),
        ('representations', 'serialized.representations'),
    )
    facet_dict = dict(facet_fields)

    query = {
        'query': { 'filtered': { 'query': { 'match_all': {} } } },
        'facets': {},
        'size': 100
    }

    for label, field in facet_fields:
        query['facets'][label] = { 'terms': { 'field': field, 'size': 30 } }

    filters = []
    params = [ p for p in request.GET.keys() if p.endswith('[]') ]

    for field in params:
        facet_field = facet_dict.get(field[:-2], None)
        if facet_field is None:
            continue
        for val in request.GET.getlist(field):
            filters.append({ 'term': { facet_field: val } })

    if filters:
        query['query']['filtered']['filter'] = { 'and': filters }

    executed_query = en_index.search_model(Document, query)

    o['facets'] = {}
    for facet_label, facet_vals in executed_query['facets'].items():
        o['facets'][facet_label] = [ (f['term'], f['term'], f['count'])
                                     for f in facet_vals['terms'] ]

    o['documents'] = [ d['_source']['serialized'] for d in
                       executed_query['hits']['hits'] ]

    return render_to_response(
        template, o, context_instance=RequestContext(request))
