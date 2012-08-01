from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from editorsnotes.main.models import Topic, Document
from models import TopicCluster, BadClusterPair
from itertools import combinations
from lxml import html
import utils as rutils
import re


@login_required
def show_topic_clusters(request):
    o = {}
    user_profile = request.user.get_profile()
    affiliation = user_profile.affiliation
    if not (request.user.is_superuser or
             ( affiliation and
               user_profile.get_project_role(affiliation) == 'editor')):
        return HttpResponseBadRequest('Insufficient permissions')

    start = int(request.GET.get('start', 0))
    max_count = 20

    if request.user.is_superuser:
        clusters = TopicCluster.objects.all()
    else:
        clusters = TopicCluster.objects.filter(
            topics__affiliated_projects=affiliation)

    o['total_clusters'] = clusters.count()
    o['start'] = start + 1

    if start + max_count < o['total_clusters'] + 1:
        o['end'] = start + max_count
        o['next'] = o['end']
    else:
        o['end'] = o['total_clusters']

    if start > 0:
        o['previous'] = (start - max_count
                         if start - max_count > 0 else 0)
    o['clusters'] = clusters.order_by('id')[start:start + max_count]

    return render_to_response(
        'view-clusters.html', o, context_instance=RequestContext(request))

def merge_topic_cluster(request, cluster_id):
    o = {}
    o['cluster'] = get_object_or_404(TopicCluster, id=cluster_id)

    # Make sure person trying to merge topics is an editor of one of the
    # affiliated projects or a site admin
    #
    # (This is a quick fix-- Should integrate with overall permissions framework
    # at some point)
    user_affiliation = request.user.get_profile().affiliation
    if not (request.user.is_superuser or
            any([ t for t in o['cluster'].topics.all()
                  if user_affiliation in t.affiliated_projects.all()] )):
        return HttpResponseBadRequest('Insufficient permissions')

    if request.user.is_superuser:
        next_cluster = TopicCluster.objects.filter(id__gt=cluster_id)
    else:
        next_cluster = TopicCluster.objects.filter(
            id__gt=cluster_id,
            topics__affiliated_projects=user_affiliation)

    next_url = (reverse('merge_topic_cluster_view',
                        kwargs={'cluster_id': next_cluster[0].id}) 
                if next_cluster else '/')

    if next_url != '/':
        o['next_cluster_url'] = next_url

    # Merge or delete the cluster
    if request.POST:
        action = request.POST.get('action')


        if action == 'delete_cluster':
            for obj1, obj2 in combinations(o['cluster'].topics.all(), 2):
                BadClusterPair.objects.create(
                    content_type=ContentType.objects.get_for_model(Topic),
                    obj1=int(obj1.id),
                    obj2=int(obj2.id))
            o['cluster'].delete()

            messages.add_message(request, messages.SUCCESS,
                                 'Cluster with id %s deleted' % cluster_id)

            url = request.GET.get('return_to', next_url)
            return HttpResponseRedirect(url)

        elif action == 'merge_cluster':
            topics = Topic.objects.filter(id__in=request.POST.getlist('topic'))
            merged_topic = rutils.merge_topics(topics, request.user)
            o['cluster'].delete()
            message = 'Successfully merged to new topic <a href="%s">%s</a>' % (
                merged_topic.get_absolute_url(), merged_topic.as_html())
            messages.add_message(request, messages.SUCCESS, message)

            url = request.GET.get('return_to', next_url)
            return HttpResponseRedirect(url)

    # Review choices for merging
    elif request.GET.get('continue'):
        topics_to_merge = request.GET.getlist('topic')
        topics = Topic.objects.filter(id__in=topics_to_merge,
                                      in_cluster=cluster_id)

        if len(topics) != len(topics_to_merge):
            return HttpResponseBadRequest()

        name, aliases = rutils.get_preferred_topic_name(topics)
        o['topics'] = topics
        o['preferred_name'], o['new_aliases'] = name, aliases
        o['article'] = rutils.get_combined_article(topics)
        o['related_objects'] = []
        o['existing_aliases'] = []

        for topic in topics:
            o['related_objects'] += topic.related_objects()
            o['existing_aliases'] += topic.aliases.all()

        o['related_objects'].sort(key=repr)
        o['existing_aliases'].sort(key=repr)

        return render_to_response(
            'review-merged-topics.html', o, context_instance=RequestContext(request))

    # Present choices for merging
    else:
        return render_to_response(
            'merge-topics.html', o, context_instance=RequestContext(request))
