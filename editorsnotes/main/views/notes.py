from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from haystack.query import SearchQuerySet
import reversion

from ..models.notes import Note
from ..models.auth import Project
from ..models.documents import Citation
from ..models.topics import Topic

def note(request, note_id, project_slug=None):
    o = {}
    o['note'] = get_object_or_404(Note, id=note_id)
    o['history'] = reversion.get_unique_for_object(o['note'])
    o['topics'] = [ ta.topic for ta in o['note'].topics.all() ]
    o['cites'] = Citation.objects.get_for_object(o['note'])

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

