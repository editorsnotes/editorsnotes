from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic.base import RedirectView

from editorsnotes.search import en_index

from .. import utils
from ..models.auth import Project
from ..models.documents import Document, Citation
from ..models.notes import Note
from ..models.topics import Topic, TopicNode, ProjectTopicContainer

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

def topic_node(request, topic_node_id):
    o = {}
    node_qs = TopicNode.objects.select_related()
    o['topic_node'] = get_object_or_404(node_qs, id=topic_node_id)
    return render_to_response(
        'topic_node.html', o, context_instance=RequestContext(request))

def topic(request, project_slug, topic_node_id):
    o = {}
    topic_qs = ProjectTopicContainer.objects\
            .select_related('creator', 'last_updater', 'project')
    o['topic'] = topic = get_object_or_404(topic_qs,
                                           topic_id=topic_node_id,
                                           project__slug=project_slug)
    o['projects'] = topic.project

    topic_query = {'query': {'term': {'serialized.related_topics.url':
                                      topic.get_absolute_url() }}}

    model_searches = ( en_index.search_model(model, topic_query) for model in
                       (Document, Note, ProjectTopicContainer) )

    o['documents'], o['notes'], o['related_topics'] = (
        [ result['_source']['serialized'] for result in search['hits']['hits'] ]
        for search in model_searches
    )

    return render_to_response(
        'topic.html', o, context_instance=RequestContext(request))
