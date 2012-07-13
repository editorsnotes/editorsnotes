from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from editorsnotes.main.models import Topic, Document
from models import TopicCluster

@login_required
def show_clusters(request):
    o = {}
    o['clusters'] = TopicCluster.objects.all()
    return render_to_response(
        'view-clusters.html', o, context_instance=RequestContext(request))

def merge_cluster(request):
    o = {}

    cluster = request.GET.get('cluster')
    if not cluster:
        return HttpResponseRedirect(reverse('show_clusters_view'))
    o['cluster'] = get_object_or_404(TopicCluster, id=cluster)

    return render_to_response(
        'merge-topics.html', o, context_instance=RequestContext(request))
