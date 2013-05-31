from itertools import chain

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic.base import RedirectView

from .. import utils
from ..models.auth import Project
from ..models.documents import Document, Citation
from ..models.notes import Note, NoteSection
from ..models.topics import Topic, TopicNode

def _sort_citations(instance):
    cites = { 'all': [] }
    for c in Citation.objects.filter(
        content_type=ContentType.objects.get_for_model(instance), 
        object_id=instance.id):
        cites['all'].append(c)
    cites['all'].sort(key=lambda c: c.ordering)
    return cites


class LegacyTopicRedirectView(RedirectView):
    permanent = True
    query_string = True
    def get_redirect_url(self, topic_slug):
        legacy_topic = get_object_or_404(Topic, slug=topic_slug)
        return reverse('topicnode_view', args=(legacy_topic.merged_into_id,))

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
    query_set = TopicNode.objects.filter(type=o['type'])
    [o['topics_1'], o['topics_2'], o['topics_3']] = utils.alpha_columns(
        query_set, 'preferred_name', itemkey='topic')
    return render_to_response(
        template, o, context_instance=RequestContext(request))


def topic(request, topic_slug):
    o = {}
    o['topic'] = get_object_or_404(Topic, slug=topic_slug)
    o['contact'] = { 'name': settings.ADMINS[0][0], 
                     'email': settings.ADMINS[0][1] }
    o['related_topics'] = o['topic'].related_topics.all()
    o['summary_cites'] = _sort_citations(o['topic'])

    notes = o['topic'].related_objects(Note)
    note_topics = [ [ ta.topic for ta in n.topics.exclude(topic=o['topic']).select_related('topic') ] for n in notes ]
    note_sections = NoteSection.objects.filter(note__in=[n.id for n in notes])

    o['notes'] = zip(notes, note_topics)

    o['documents'] = set(chain(
        o['topic'].related_objects(Document),
        Document.objects.filter(notesection__in=note_sections)))

    o['thread'] = { 'id': 'topic-%s' % o['topic'].id, 'title': o['topic'].preferred_name }
    o['alpha'] = (request.user.groups.filter(name='Alpha').count() == 1)

    return render_to_response(
        'topic.html', o, context_instance=RequestContext(request))

def topic_node(request, topicnode_id):
    o = {}
    empty_qs = TopicNode.objects\
            .select_related(
                'names__project',
                'summaries__citations__document'
            ).prefetch_related(
                'related_topics__topic',
                'summaries__project',
                'summaries__citations__document'
            )
    o['topic'] = topic = get_object_or_404(empty_qs, id=topicnode_id)
    o['notes'] = topic.related_objects(Note)\
            .prefetch_related('topics__topic')
    o['documents'] = set(chain(
        topic.related_objects(Document),
        Document.objects.prefetch_related('citationns_set')\
            .filter(citationns__note_id__in=[n.id for n in o['notes']])))
    return render_to_response(
        'topic2.html', o, context_instance=RequestContext(request))

def project_topic(request, project_slug, topic_node):
    return HttpResponse('hi')
