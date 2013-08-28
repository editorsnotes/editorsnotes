import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from editorsnotes.main.models.auth import User

from .forms import ZoteroForm
from .models import CachedArchive
from .widgets import ZoteroWidget
from . import utils

#@login_required
#def import_zotero(request, username=False):
#    o = {}
#    if not username:
#        user = request.user
#    else:
#        user = get_object_or_404(User, username=username)
#    if user.get_profile().zotero_uid and user.get_profile().zotero_key:
#        o['zotero_status'] = True
#        o['zotero_uid'] = user.get_profile().zotero_uid
#    else:
#        o['zotero_status'] = False
#    o['get_params'] = request.GET.urlencode().replace('%2F', '/')
#    if request.GET.get('apply', ''):
#        o['apply_to_docs'] = True
#    else:
#        o['apply_to_docs'] = False
#    return render_to_response(
#        'import-zotero.html', o, context_instance=RequestContext(request))
#
#def libraries(request):
#    if not request.is_ajax():
#        return HttpResponseBadRequest()
#    if request.GET.get('validate', ''):
#        zotero_uid = request.GET.get('zotero_uid')
#        zotero_key = request.GET.get('zotero_key')
#    else:
#        zotero_uid = request.user.get_profile().zotero_uid
#        zotero_key = request.user.get_profile().zotero_key
#    libraries = utils.get_libraries(zotero_uid, zotero_key)
#    return HttpResponse(json.dumps(libraries), mimetype='application/json')
#
#def collections(request):
#    if not request.is_ajax():
#        return HttpResponseBadRequest()
#    loc = request.GET.get('loc', '')
#    top_level = request.GET.get('top', 0)
#    zotero_key = request.user.get_profile().zotero_key
#    collections = utils.get_collections(zotero_key, loc, int(top_level))
#    return HttpResponse(json.dumps(collections), mimetype='application/json')
#    
#def items(request):
#    if not request.is_ajax():
#        return HttpResponseBadRequest()
#    loc = request.GET.get('loc', '')
#    opts = json.loads(request.GET.get('opts', '{}'))
#    zotero_key = request.user.get_profile().zotero_key
#    items = utils.get_items(zotero_key, loc, opts)
#    return HttpResponse(json.dumps(items), mimetype='application/json')
#
#def items_continue(request):
#    request.session['import_complete'] = False
#    selected_items_list = request.POST.getlist('zotero-item')
#    selected_items = [json.loads(item, strict=False) for item in selected_items_list]
#    o = {}
#    o['items'] = []
#    o['get_params'] = request.GET.urlencode().replace('%2F', '/')
#    for item in selected_items:
#        item_return = {}
#        #Check if this exact item has been imported before
#        if ZoteroLink.objects.filter(zotero_url=item['url']):
#            item_return['existing'] = ('exact',
#                ZoteroLink.objects.filter(zotero_url=item['url'])[0].doc)
#        else:
#            item_return['existing'] = False
#        #TODO: Check if item with this title/creators/date has been imported
#        
#        #Get related topics for tags
#        #item_return['related_topics'] = []
#        #for tag in item['tags']:
#        #    query = ' AND '.join([ 'title:%s' % term for term 
#        #                       in tag['tag'].split() if len(term) > 1 ])
#        #    topic_match_set = [(result.object.preferred_name, result.object.id) for result
#        #                       in SearchQuerySet().models(Topic).narrow(query)
#        #                       if result.score >= 40]
#        #    if topic_match_set:
#        #        item_return['related_topics'].append(topic_match_set)
#        item_return['data'] = json.dumps(item)
#        item_return['citation'] = item['citation']
#        o['items'].append(item_return)
#    return render_to_response(
#        'continue.html', o, context_instance=RequestContext(request))
#
#def import_items(request):
#    if request.session.get('import_complete', False):
#        return HttpResponse('Please only submit items once')
#    item_data = request.POST.getlist('data')
#    item_citations = request.POST.getlist('changed-citation')
#    user = request.user
#    o={}
#    o['created_items'] = []
#    item_counter = 0
#    for item_data_string, updated_citation in zip(item_data, item_citations):
#        item_counter += 1
#        action = request.POST.get('import-action-%s' % item_counter)
#        if action not in ['create', 'update']:
#            continue
#        item_data = json.loads(item_data_string, object_pairs_hook=OrderedDict)
#        if updated_citation:
#            citation = updated_citation
#        else:
#            citation = item_data['citation']
#        if action == "create":
#            d = Document(creator=user, last_updater=user, description=citation)
#            d.save()
#        elif action == "update":
#            update_id = request.POST.get('item-update-%s' % item_counter)
#            d = Document.objects.get(id=update_id)
#            d.last_updated = datetime.datetime.now()
#            d.last_updater = user
#            d.save()
#            if d.zotero_link():
#                d.zotero_link().delete()
#        link = ZoteroLink(zotero_data=item_data['json'], zotero_url=item_data['url'], doc_id=d.id)
#        try:
#            item_data['date']['year']
#            link.date_information = json.dumps(item_data['date'])
#        except KeyError:
#            pass
#        link.save()
#        reltopic = request.GET.get('reltopic', False)
#        if reltopic:
#            related_topic = Topic.objects.get(id=int(reltopic))
#            new_assignment = TopicAssignment.objects.create(
#                content_object=d,
#                topic=related_topic,
#                creator=user
#                )
#            new_assignment.save()
#        o['created_items'].append(d)
#    request.session['import_complete'] = True
#    redirect_url = request.GET.get('return_to', '/')
#    return HttpResponseRedirect(redirect_url)

@login_required
def update_zotero_info(request, username=None):
    if not username:
        user = request.user
    else:
        user = get_object_or_404(User, username=username)
    user.zotero_uid = request.POST.__getitem__('zotero-id')
    user.zotero_key = request.POST.__getitem__('zotero-key')
    user.save()
    redirect_url = request.GET.get('return_to', '/')
    return HttpResponseRedirect(redirect_url)

def zotero_template(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    item_type = request.GET.get('itemType')
    if item_type:
        item_template = utils.get_item_template(item_type)
        form = ZoteroForm(data={'zotero_data': item_template})
    else:
        form = ZoteroForm()
    return HttpResponse(form.as_p())

def get_blank_item(request):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    item_type = request.GET.get('itemType')
    blank_item = utils.get_item_template(item_type)
    form = ZoteroWidget()
    new_form = form.render('', blank_item)
    return HttpResponse(new_form, mimetype='text/plain')

def get_creator_types(request):
    if not request.is_ajax() or not request.GET.get('itemType', False):
        return HttpResponseBadRequest()
    item_type = request.GET.get('itemType')
    creators_json = utils.get_creator_types(item_type)
    return HttpResponse(creators_json, mimetype='application/json')

def zotero_json_to_csl(request):
    if not request.is_ajax() or not request.GET.get('zotero-json', False):
        return HttpResponseBadRequest()
    zotero_json = request.GET.get('zotero-json')
    csl = utils.as_csl(zotero_json, 'ITEM-1')
    return HttpResponse(csl, mimetype='application/json')

def archive_to_dict(archive):
    archive_dict = {}
    archive_dict['name'] = archive.name
    archive_dict['id'] = archive.id
    return archive_dict

def api_archives(request):
    q = request.GET.get('q', '')
    queryset = CachedArchive.objects.filter(
        name__icontains=q
    )
    archives = [ archive_to_dict(a) for a in queryset ]
    return HttpResponse(json.dumps(archives), mimetype='text/plain')
