from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from editorsnotes.djotero.utils import as_readable, type_map

from ..models.auth import Project
from ..models.documents import Document, Footnote, Transcript
from ..models.topics import Topic, TopicNode
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
        [ ta.topic for ta in o['document'].topics.all() ] +
        [ c.content_object for c in o['document'].citations.filter(
                content_type=ContentType.objects.get_for_model(Topic)) ])
    o['scans'] = o['document'].scans.all()
    o['domain'] = Site.objects.get_current().domain

    notes = [ns.note for ns in CitationNS.objects\
            .select_related('note')\
            .filter(document=o['document'])]
    note_topics = [ [ ta.topic for ta in n.topics.all() ] for n in notes ]
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

    # Narrow search query according to GET parameters
    qs = SearchQuerySet().models(Document)

    query = []
    params = [p for p in request.GET.keys() if p[-2:] == '[]']
    for param in params:
        this_query = [ '%s:"%s"' % (param[:-2], val)
                      for val in request.GET.getlist(param) ]
        query += [' AND '.join(this_query)]
    qs = qs.narrow(' AND '.join(query)) if query else qs

    # Facet results
    valid_facets = (
        'project_slug',
        'related_topic_id',
        'archive',
        'publicationTitle',
        'itemType',
        'creators',
        'representations'
    )
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
                    [ (t_id, TopicNode.objects.get(id=t_id), count)
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

