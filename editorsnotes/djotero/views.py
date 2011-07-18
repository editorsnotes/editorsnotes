
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from main.models import Document
from djotero.models import ZoteroLink
import utils
import json

@login_required
def import_zotero(request, username=False):
    o = {}
    if not username:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)
    if user.get_profile().zotero_uid and user.get_profile().zotero_key:
        o['zotero_status'] = True
    else:
        o['zotero_status'] = False
    return render_to_response(
        'import-zotero.html', o, context_instance=RequestContext(request))

def access_list(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    zotero_uid = request.user.get_profile().zotero_uid
    zotero_key = request.user.get_profile().zotero_key
    libraries = utils.request_permissions(zotero_uid, zotero_key)
    return HttpResponse(json.dumps(libraries), mimetype='text/plain')

def list_collections(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    loc = request.GET.get('loc', '') 
    zotero_key = request.user.get_profile().zotero_key
    collections = utils.list_collections(zotero_key, loc)
    return HttpResponse(json.dumps(collections), mimetype='text/plain')
    
def list_items(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    loc = request.GET.get('loc', '')
    zotero_key = request.user.get_profile().zotero_key
    latest = utils.latest_items(zotero_key, loc)
    return HttpResponse(json.dumps(latest), mimetype='text/plain')

def import_items(request):
    o={}
    o['raw'] = request.POST.getlist('item')
    o['items'] = []
    o['imported_docs'] = []
    o['existing_docs'] = []
    for item in o['raw']:
        o['items'].append(json.loads(item,strict=False))
    for doc_import in o['items']:
        if not ZoteroLink.objects.filter(zotero_url=doc_import['url']):
            d = Document(creator=request.user, last_updater=request.user, description=doc_import['csl'])
            d.save()
            o['imported_docs'].append(d)
            link = ZoteroLink(zotero_data=json.dumps(doc_import['json']), zotero_url=doc_import['url'], doc_id=d.id)
            link.save()
        else:
            o['existing_docs'].append(ZoteroLink.objects.filter(zotero_url=doc_import['url'])[0].doc)
    return render_to_response(
        'success.html', o, context_instance=RequestContext(request))

@login_required
def update_zotero_info(request, username=None):
    if not username:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)
    profile = user.get_profile()
    profile.zotero_uid = request.POST.__getitem__('zotero-id')
    profile.zotero_key = request.POST.__getitem__('zotero-key')
    profile.save()
    redirect_url = request.GET.get('return_to', '')
    return HttpResponseRedirect(redirect_url)
