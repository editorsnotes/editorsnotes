from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from editorsnotes.main.models import Document, Topic, TopicAssignment
from editorsnotes.main.templatetags.display import as_link
from models import ZoteroLink
import utils
import json, datetime

@login_required
def import_zotero(request, username=False):
    o = {}
    if not username:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)
    if user.get_profile().zotero_uid and user.get_profile().zotero_key:
        o['zotero_status'] = True
        o['zotero_uid'] = user.get_profile().zotero_uid
    else:
        o['zotero_status'] = False
    o['related_object'] = request.GET.get('rel', '')
    o['related_id'] = request.GET.get('id', '')
    o['return_to'] = request.GET.get('return_to', '/')
    if request.GET.get('apply', ''):
        o['apply_to_docs'] = True
    else:
        o['apply_to_docs'] = False
    return render_to_response(
        'import-zotero.html', o, context_instance=RequestContext(request))

def libraries(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    if request.GET.get('validate', ''):
        zotero_uid = request.GET.get('zotero_uid')
        zotero_key = request.GET.get('zotero_key')
    else:
        zotero_uid = request.user.get_profile().zotero_uid
        zotero_key = request.user.get_profile().zotero_key
    libraries = utils.get_libraries(zotero_uid, zotero_key)
    return HttpResponse(json.dumps(libraries), mimetype='text/plain')

def collections(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    loc = request.GET.get('loc', '') 
    zotero_key = request.user.get_profile().zotero_key
    collections = utils.get_collections(zotero_key, loc)
    return HttpResponse(json.dumps(collections), mimetype='text/plain')
    
def items(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    loc = request.GET.get('loc', '')
    opts = json.loads(request.GET.get('opts', '{}'))
    zotero_key = request.user.get_profile().zotero_key
    items = utils.get_items(zotero_key, loc, opts)
    return HttpResponse(json.dumps(items), mimetype='text/plain')

def import_items(request):
    raw = request.POST.getlist('items[]')
    items = []
    o={}
    o['imported_docs'] = []
    o['existing_docs'] = []
    for item in raw:
        items.append(json.loads(item,strict=False))
    for doc_import in items:
        if not ZoteroLink.objects.filter(zotero_url=doc_import['url']):
            d = Document(creator=request.user, last_updater=request.user, description=doc_import['citation'])
            d.save()
            o['imported_docs'].append(as_link(d))
            link = ZoteroLink(zotero_data=doc_import['json'], zotero_url=doc_import['url'], doc_id=d.id)
            try:
                doc_import['date']['year']
                link.date_information = json.dumps(doc_import['date'])
            except KeyError:
                pass
            link.save()
        else:
            existing_link = ZoteroLink.objects.filter(zotero_url=doc_import['url'])[0]
            o['existing_docs'].append(as_link(existing_link.doc))
            d = existing_link.doc
        if doc_import['related_object'] == 'topic':
            related_topic = Topic.objects.get(id=int(doc_import['related_id']))
            if TopicAssignment.objects.filter(document=d, topic=related_topic):
                pass
            else:
                new_assignment = TopicAssignment.objects.create(content_object=d, topic=related_topic, creator=request.user)
                new_assignment.save()
    return HttpResponse(json.dumps(o), mimetype='text/plain')

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

def batch_import(request):
    o = {}
    return render_to_response('batch-import.html', o, context_instance=RequestContext(request))

def update_link(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    doc_id = request.POST.get('doc_id')
    json_string = request.POST.get('zotero_info')
    doc_information = json.loads(json_string, strict=False)
    document = Document.objects.get(id=doc_id)
    if document.zotero_link():
        document.zotero_link().delete()
    
    link = ZoteroLink(zotero_data=json.dumps(doc_information['json']), zotero_url=doc_information['url'], doc_id=document.id)
    try:
        doc_information['date']['year']
        link.date_information = json.dumps(doc_information['date'])
    except KeyError:
        pass
    link.save()
    document.last_updated = datetime.datetime.now()
    document.save()
    
    return HttpResponse(document, mimetype='text/plain')
