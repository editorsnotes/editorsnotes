from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from editorsnotes.main.models import Topic, Document
from models import TopicCluster
from lxml import html
import utils as rutils
import re


@login_required
def show_clusters(request):
    o = {}
    o['clusters'] = TopicCluster.objects.all()
    return render_to_response(
        'view-clusters.html', o, context_instance=RequestContext(request))

def merge_cluster(request, cluster_id):
    o = {}
    o['cluster'] = get_object_or_404(TopicCluster, id=cluster_id)

    # Merge or delete the cluster
    if request.POST:
        action = request.POST.get('action')

        next_cluster = TopicCluster.objects.filter(id__gt=cluster_id)
        next_url = (reverse('merge_cluster_view',
                            kwargs={'cluster_id': next_cluster[0].id}) 
                    if next_cluster else '/')

        if action == 'delete_cluster':
            o['cluster'].delete()
            messages.add_message(
                request, messages.SUCCESS,
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
                                      topiccluster=cluster_id)

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
