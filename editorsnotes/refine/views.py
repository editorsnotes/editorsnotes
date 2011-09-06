from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from models import TopicCluster

@login_required
def show_clusters(request):
    o = {}
    o['clusters'] = TopicCluster.objects.all()
    return render_to_response(
        'view-clusters.html', o, context_instance=RequestContext(request))
