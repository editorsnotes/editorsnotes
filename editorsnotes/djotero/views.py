
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest
import utils
import json

@login_required
def import_zotero(request):
    o = {}
    
    
    
    # 1. connect to zotero to determine API key's privileges
    
    # 2. After selection of source, pull last 10 items edited
    
    # 3. Add selected source's data & zotero ID to document being dealt with
    
    return render_to_response(
        'import-zotero.html', o, context_instance=RequestContext(request))

def access_list(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    zotero_uid = '161334'
    zotero_key = 'r0KBtuDLU0Jh2s1jAPVLZymn'
    libraries = utils.request_permissions(zotero_uid, zotero_key)
    return HttpResponse(json.dumps(libraries), mimetype='text/plain')

def list_items(request):
    #if not request.is_ajax():
    #    return HttpResponseBadRequest()
    loc = request.GET.get('loc', '')
    zotero_uid = '161334'
    zotero_key = 'r0KBtuDLU0Jh2s1jAPVLZymn'
    latest = utils.latest_items(zotero_key, loc)
    return HttpResponse(json.dumps(latest), mimetype='text/plain')
