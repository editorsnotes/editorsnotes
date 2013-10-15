from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

import reversion

from editorsnotes.search import en_index

from ..models.notes import Note

def note(request, note_id, project_slug=None):
    o = {}
    qs = Note.objects\
            .select_related('license', 'project__default_license')\
            .prefetch_related('topics')
    note = get_object_or_404(qs, id=note_id)

    o['note'] = note
    o['license'] = note.license or note.project.default_license
    o['history'] = reversion.get_unique_for_object(note)
    o['topics'] = [ta.container for ta in o['note'].topics.all()]
    o['sections'] = note.sections\
            .order_by('ordering', 'note_section_id')\
            .select_subclasses()\
            .select_related('citationns__document__project',
                            'notereferencens__note_reference__project')
    o['can_edit'] = request.user.is_authenticated() and \
            request.user.has_project_perm(o['note'].project, 'main.change_note')

    return render_to_response(
        'note.html', o, context_instance=RequestContext(request))

def all_notes(request, project_slug=None):
    o = {}
    template = 'all-notes.html'
    o['filtered'] = False

    if request.GET.get('filter'):
        template = 'filtered-notes.html'
        o['filtered'] = True

    # Base query & facets
    query = {
        'query': { 'filtered': { 'query': { 'match_all': {} } } },
        'facets': {
            'project_facet': {
                'terms': { 'field': 'serialized.project.name', 'size': 8 }
            },
            'topic_facet': {
                'terms': { 'field': 'serialized.topics.name', 'size': 16 }
            },
            'status_facet': {
                'terms': { 'field': 'serialized.status' }
            }
        },
        'size': 500
    }

    # Filter query based on facets
    filters = []
    for topic in request.GET.getlist('topic'):
        filters.append({ 'term': { 'serialized.topics.name': topic } })

    project = request.GET.get('project')
    if project:
        filters.append({ 'term': { 'serialized.project.name': project } })

    status = request.GET.get('note_status')
    if status:
        filters.append({ 'term': { 'serialized.status': status } })

    if filters:
        query['query']['filtered']['filter'] = { 'and': filters }

    # Execute built query
    executed_query = en_index.search_model(Note, query)

    # This is gibberish that can be improved, but it lets us use the old xapian
    # code that I implemented a long time ago.
    topic_facets = executed_query['facets']['topic_facet']['terms']
    o['topic_facets_1'] = topic_facets[:8]
    o['topic_facets_2'] = topic_facets[8:] if len(topic_facets) > 8 else []

    project_facets = executed_query['facets']['project_facet']['terms']
    o['project_facets'] = project_facets

    status_facets = executed_query['facets']['status_facet']['terms']
    o['status_facets'] = status_facets

    o['notes'] = [ n['_source']['serialized'] for n in
                   executed_query['hits']['hits'] ]

    return render_to_response(
        template, o, context_instance=RequestContext(request))
