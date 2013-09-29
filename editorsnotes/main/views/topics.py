from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic.base import RedirectView

from .. import utils
from ..models.auth import Project
from ..models.documents import Document, Citation
from ..models.notes import Note
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

def topic_node(request, topic_node_id):
    o = {}
    node_qs = TopicNode.objects\
            .prefetch_related('project_containers__project')\
            .select_related('creator', 'last_updater', 'project_containers')
    o['topic'] = topic = get_object_or_404(node_qs, id=topic_node_id)
    o['projects'] = [c.project for c in o['topic'].project_containers.all()]
    o['related_topics'] = topic.related_objects(TopicNode)
    o['notes'] = topic.related_objects(Note)\
            .select_related('project')\
            .prefetch_related('topics__container__project',
                              'topics__container__topic')
    document_ids = SearchQuerySet()\
            .models(Document)\
            .filter(related_topic_id=topic.id)\
            .values_list('pk', flat=True)
    o['documents'] = Document.objects.filter(id__in=document_ids)
    o['summaries'] = [container.summary for container in
                      topic.project_containers.all() 
                      if container.has_summary()]
    o['editable_project_containers'] = [
        container for container in topic.project_containers.all()
        if request.user.is_authenticated() and request.user.has_project_perm(
            container.project, 'main.change_projecttopiccontainer')]
            
    return render_to_response(
        'topic2.html', o, context_instance=RequestContext(request))

def project_topic(request, project_slug, topic_node_id):
    return HttpResponse('hi')
