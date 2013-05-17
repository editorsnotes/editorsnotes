import os
import re
from itertools import chain
from random import randint
from urllib import urlopen
from PIL import Image, ImageFont, ImageDraw

from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseRedirect)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.base import RedirectView

import reversion
from django_browserid.views import Verify
from haystack.query import SearchQuerySet, EmptySearchQuerySet

import utils
import forms as main_forms
import models as main_models
from editorsnotes.djotero.utils import as_readable, type_map
from editorsnotes.refine.models import TopicCluster

def _sort_citations(instance):
    cites = { 'all': [] }
    for c in main_models.Citation.objects.filter(
        content_type=ContentType.objects.get_for_model(instance), 
        object_id=instance.id):
        cites['all'].append(c)
    cites['all'].sort(key=lambda c: c.ordering)
    return cites

# Proxy for cross-site AJAX requests. For development only.
def proxy(request):
    url = request.GET.get('url')
    if url is None:
        return HttpResponseBadRequest()
    if not url.startswith('http://cache.zoom.it/'):
        return HttpResponseForbidden()
    return HttpResponse(urlopen(url).read(), mimetype='application/xml')


# ------------------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------------------

@reversion.create_revision()
def create_invited_user(email):
    invitation = main_models.ProjectInvitation.objects.filter(email=email)
    if not invitation:
        return None

    project = invitation[0].project

    username = re.sub(r'[^\w\-.]', '', email[:email.rindex('@')])[:29]
    if User.objects.filter(username=username).exists():
        existing_names = [
            u.username[len(username):] for u in
            User.objects.filter(username__startswith=username)]
        username += str([
            i for i in range(0, 10) if str(i) not in existing_names][0])

    new_user = User(username=username, email=email)
    new_user.set_unusable_password()
    new_user.save()
    profile = main_models.UserProfile.objects.create(user=new_user)
    project.members.add(profile)

    invitation[0].delete()

    return new_user

class CustomBrowserIDVerify(Verify):
    failure_url = '/accounts/login/'
    def get_success_url(self):
        return self.request.user.get_profile().get_absolute_url()

def user_logout(request):
    auth.logout(request)
    return render_to_response(
        'logout.html', context_instance=RequestContext(request))

def user(request, username=None):
    o = {}
    if not username:
        user = request.user
        o['own_profile'] = True
    else:
        user = get_object_or_404(User, username=username)
        o['own_profile'] = user == request.user

    o['profile'] = main_models.UserProfile.get_for(user)
    o['log_entries'], ignored = main_models.UserProfile.get_activity_for(user, max_count=20)
    o['affiliation'] = o['profile'].affiliation
    o['project_role'] = (o['profile'].get_project_role(o['affiliation'])
                         if o['affiliation'] else None)

    if ['own_profile']:
        o['zotero_status'] = True if (o['profile'].zotero_key and
                                      o['profile'].zotero_uid) else False
        if (o['affiliation'] and o['project_role'] == 'editor') or user.is_superuser:
            if user.is_superuser:
                o['clusters'] = TopicCluster.objects.all()
            else:
                o['clusters'] = TopicCluster.objects.filter(
                    topics__affiliated_projects=o['profile'].affiliation)
    return render_to_response(
        'user.html', o, context_instance=RequestContext(request))


# ------------------------------------------------------------------------------
# Basic navigation
# ------------------------------------------------------------------------------

def index(request):
    o = {}
    return render_to_response(
        'index.html', o, context_instance=RequestContext(request))

def browse(request):
    max_count = 6
    o = {}
    for model in [main_models.topics.TopicNode, main_models.Note, main_models.Document]:
        model_name = model._meta.module_name
        listname = '%s_list' % model_name
        query_set = model.objects.order_by('-last_updated')

        items = list(query_set[:max_count])
        o[listname] = items
    o['projects'] = main_models.Project.objects.all().order_by('name')
    return render_to_response(
        'browse.html', o, context_instance=RequestContext(request))

reel_numbers = re.compile(r'(\S+):(\S+)')
ignored_punctuation = '!#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

def search(request):
    query = ''
    results = EmptySearchQuerySet()

    if request.GET.get('q'):
        query = request.GET.get('q')
        match = reel_numbers.search(query)
        if match:
            # so we can match reel numbers exactly
            query = reel_numbers.sub(r'"\1 \2"', query)
        def filter(c):
            if c in ignored_punctuation: return ' '
            return c
        query = ''.join([filter(c) for c in query])
        if len(query) > 0:
            results = SearchQuerySet().auto_query(query).load_all()
        if match:
            # restore the original form of the query so highlighting works
            query = query.replace('"%s %s"' % match.group(1,2), match.group(0))

    o = {
        'results': results,
        'query': query,
    }
    
    return render_to_response(
        'search.html', o, context_instance=RequestContext(request))

def about_test(request):
    x, y = (100, 38)
    img = Image.new('RGBA', (x, y), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(
        os.path.join(settings.STATIC_ROOT, 'style', 'DejaVuSans-Bold.ttf'), 24)
    i, s, j = (randint(10, 20), ('+', '-')[randint(0, 1)], randint(1, 9))
    text = '%s %s %s' % (i, s, j)

    result = i + j if s == '+' else i - j

    draw.text((9, 5), text, (50,50,50), font=font)

    for i in xrange(0, 500):
        draw.point((randint(0, x), randint(0, y)),
                   [(x, x, x) for x in (randint(100,180),)][0])

    request.session['test_answer'] = result

    response = HttpResponse(mimetype="image/png")
    img.save(response, 'PNG')

    return response

def about(request):
    o = {}

    if request.method == 'POST':

        bad_answers = request.session.setdefault('bad_answers', 0)
        if bad_answers > 3:
            return HttpResponseForbidden(
                'Too many failed attempts. Try again later.')

        o['form'] = main_forms.FeedbackForm(request.POST)
        if o['form'].is_valid():

            test_answer = request.POST.get('testanswer', '')
            if test_answer.isdigit() and int(test_answer) == request.session['test_answer']:
                request.session.pop('bad_answers')

                choice = o['form'].cleaned_data['purpose']
                subj = '(%s) %s' % (
                    dict(o['form'].fields['purpose'].choices)[choice],
                    o['form'].cleaned_data['name'])
                msg = 'reply to: %(email)s\n\n%(message)s' % o['form'].cleaned_data
                mail_admins(subj, msg, fail_silently=True)
                messages.add_message(
                    request, messages.SUCCESS,
                    'Thank you. Your feedback has been submitted.')
                return HttpResponseRedirect('/about/')
            else:
                request.session['bad_answers'] = bad_answers + 1
                o['bad_answer'] = True
                return render_to_response(
                    'about.html', o, context_instance=RequestContext(request))
    else:
        o['form'] = main_forms.FeedbackForm()
    return render_to_response(
        'about.html', o, context_instance=RequestContext(request))

# ------------------------------------------------------------------------------
# Individual instances of models
# ------------------------------------------------------------------------------

def project(request, project_slug):
    o = {}
    o['project'] = get_object_or_404(main_models.Project, slug=project_slug)
    o['log_entries'], ignored = main_models.Project.get_activity_for(o['project'], max_count=10)
    if request.user.is_authenticated():
        o['can_change'] = o['project'].attempt('change', request.user)
        o['project_role'] = request.user.get_profile().get_project_role(o['project'])
    return render_to_response(
        'project.html', o, context_instance=RequestContext(request))

class LegacyTopicRedirectView(RedirectView):
    permanent = True
    query_string = True
    def get_redirect_url(self, topic_slug):
        legacy_topic = get_object_or_404(main_models.topics.Topic, slug=topic_slug)
        return reverse('topicnode_view', args=(legacy_topic.merged_into_id,))

def topic(request, topic_slug):
    o = {}
    o['topic'] = get_object_or_404(main_models.Topic, slug=topic_slug)
    o['contact'] = { 'name': settings.ADMINS[0][0], 
                     'email': settings.ADMINS[0][1] }
    o['related_topics'] = o['topic'].related_topics.all()
    o['summary_cites'] = _sort_citations(o['topic'])

    notes = o['topic'].related_objects(main_models.Note)
    note_topics = [ [ ta.topic for ta in n.topics.exclude(topic=o['topic']).select_related('topic') ] for n in notes ]
    note_sections = main_models.NoteSection.objects.filter(note__in=[n.id for n in notes])

    o['notes'] = zip(notes, note_topics)

    o['documents'] = set(chain(
        o['topic'].related_objects(main_models.Document),
        main_models.Document.objects.filter(notesection__in=note_sections)))

    o['thread'] = { 'id': 'topic-%s' % o['topic'].id, 'title': o['topic'].preferred_name }
    o['alpha'] = (request.user.groups.filter(name='Alpha').count() == 1)

    return render_to_response(
        'topic.html', o, context_instance=RequestContext(request))

def topicnode(request, topicnode_id):
    o = {}
    empty_qs = main_models.topics.TopicNode.objects\
            .select_related(
                'creator__userprofile',
                'last_updater__userprofile',
                'names__project',
                'summaries__citations__document'
            ).prefetch_related(
                'related_topics__topic',
                'summaries__project',
                'summaries__citations__document'
            )
    o['topic'] = topic = get_object_or_404(empty_qs, id=topicnode_id)
    o['notes'] = topic.related_objects(main_models.Note)\
            .prefetch_related('topics__topic')
    o['documents'] = set(chain(
        topic.related_objects(main_models.Document),
        main_models.Document.objects.prefetch_related('citationns_set')\
            .filter(citationns__note_id__in=[n.id for n in o['notes']])))
    return render_to_response(
        'topic2.html', o, context_instance=RequestContext(request))

def note(request, note_id):
    o = {}
    o['note'] = get_object_or_404(main_models.Note, id=note_id)
    o['history'] = reversion.get_unique_for_object(o['note'])
    o['topics'] = [ ta.topic for ta in o['note'].topics.all() ]
    o['cites'] = main_models.Citation.objects.get_for_object(o['note'])

    o['can_edit'] = request.user.is_authenticated() and \
            request.user.has_project_perm(o['note'].project, 'main.change_note')

    return render_to_response(
        'note.html', o, context_instance=RequestContext(request))

def footnote(request, footnote_id):
    o = {}
    o['footnote'] = get_object_or_404(main_models.Footnote, id=footnote_id)
    o['thread'] = { 'id': 'footnote-%s' % o['footnote'].id, 
                    'title': o['footnote'].footnoted_text() }
    return render_to_response(
        'footnote.html', o, context_instance=RequestContext(request))

def document(request, document_id):
    o = {}
    o['document'] = get_object_or_404(main_models.Document, id=document_id)
    o['topics'] = (
        [ ta.topic for ta in o['document'].topics.all() ] +
        [ c.content_object for c in o['document'].citations.filter(
                content_type=ContentType.objects.get_for_model(main_models.Topic)) ])
    o['scans'] = o['document'].scans.all()
    o['domain'] = Site.objects.get_current().domain

    notes = [ns.note for ns in main_models.notes.CitationNS.objects\
            .select_related('note')\
            .filter(document=o['document'])]
    note_topics = [ [ ta.topic for ta in n.topics.all() ] for n in notes ]
    o['notes'] = zip(notes, note_topics)

    if o['document'].zotero_link():
        o['zotero_data'] = as_readable(o['document'].zotero_link().zotero_data)
        o['zotero_url'] = o['document'].zotero_link().zotero_url
        o['zotero_date_information'] = o['document'].zotero_link().date_information
    return render_to_response(
        'document.html', o, context_instance=RequestContext(request))


# ------------------------------------------------------------------------------
# Aggregations of models
# ------------------------------------------------------------------------------

def all_topics(request, project_slug=None):
    o = {}
    if project_slug:
        o['project'] = get_object_or_404(main_models.Project, slug=project_slug)
    if 'type' in request.GET:
        o['type'] = request.GET['type']
        o['fragment'] = ''
        template = 'topic-columns.include'
    else:
        o['type'] = 'PER'
        template = 'all-topics.html'
    query_set = main_models.topics.TopicNode.objects.filter(type=o['type'])
    [o['topics_1'], o['topics_2'], o['topics_3']] = utils.alpha_columns(
        query_set, 'preferred_name', itemkey='topic')
    return render_to_response(
        template, o, context_instance=RequestContext(request))

def all_documents(request, project_slug=None):
    o = {}
    template = 'all-documents.html'
    o['filtered'] = False

    if request.GET.get('filter'):
        template = 'filtered-documents.html'
        o['filtered'] = True

    # Narrow search query according to GET parameters
    qs = SearchQuerySet().models(main_models.Document)

    query = []
    params = [p for p in request.GET.keys() if p[-2:] == '[]']
    for param in params:
        this_query = [ '%s:"%s"' % (param[:-2], val)
                      for val in request.GET.getlist(param) ]
        query += [' AND '.join(this_query)]
    qs = qs.narrow(' AND '.join(query)) if query else qs

    # Facet results
    valid_facets = (
        'project_id',
        'related_topic_id',
        'archive',
        'publicationTitle',
        'itemType',
        'creators',
        'representations'
    )
    for f in valid_facets:
        qs = qs.facet(f)

    # Pass facets to template
    o['facets'] = {}
    facet_counts = qs.facet_counts()['fields'] 
    for facet in facet_counts:

        # Leave out facets with no more than one choice that are not selected
        if len(facet_counts[facet]) == 1 and \
           facet_counts[facet][0][0] == None and \
           facet not in params:
            continue
        
        # Sort results & limit to 30
        sorted_facets = sorted(facet_counts[facet],
                               key=lambda x: x[1],
                               reverse=True)
        sorted_facets = sorted_facets[:30]

        # Specific actions for individual facets.
        # Tuple represents one input: value, label, count
        if facet == 'project_id':
            o['facets']['project_id'] = [ (p_id, main_models.Project.objects.get(id=p_id), count)
                                      for p_id, count in sorted_facets ]
        elif facet == 'related_topic_id':
            o['facets']['related_topic_id'] = \
                    [ (t_id, main_models.Topic.objects.get(id=t_id), count)
                     for t_id, count in sorted_facets ]
        elif facet =='itemType':
            o['facets']['itemType'] = [ (item, type_map['readable'].get(item), count)
                                       for item, count in sorted_facets ]
        else:
            o['facets'][facet] = [ (f, f, count)
                                  for f, count in sorted_facets if f ]

    o['documents'] = qs
    o['query'] = query
    return render_to_response(
        template, o, context_instance=RequestContext(request))

def all_notes(request, project_slug=None):
    o = {}
    template = 'all-notes.html'
    o['filtered'] = False

    if request.GET.get('filter'):
        template = 'filtered-notes.html'
        o['filtered'] = True

    qs = SearchQuerySet().models(main_models.Note)
    query = []
    if request.GET.get('topic'):
        query += [ ' AND '.join([ 'related_topic_id:%s' % topic for topic
                                in request.GET.get('topic').split(',') ]) ]
    if request.GET.get('project'):
        query += [ ' AND '.join([ 'project_id:%s' % project for project
                                in request.GET.get('project').split(',') ]) ]
    qs = qs.narrow(' AND '.join(query)) if query else qs

    qs = qs.facet('related_topic_id').facet('project_id')
    facet_fields = qs.facet_counts()['fields']
    topic_facets = sorted(facet_fields['related_topic_id'],
                          key=lambda t: t[1], reverse=True)
    project_facets = sorted(facet_fields['project_id'],
                            key=lambda p: p[1], reverse=True)

    topic_facets = [ (main_models.Topic.objects.get(id=t_id), t_count)
                         for t_id, t_count in topic_facets[:16] ]
    o['topic_facets_1'] = topic_facets[:8]
    o['topic_facets_2'] = topic_facets[8:] if (len(topic_facets) > 8) else []

    o['project_facets'] = [ (main_models.Project.objects.get(id=p_id), p_count)
                           for p_id, p_count in project_facets ]
    o['notes'] = qs

    return render_to_response(
        template, o, context_instance=RequestContext(request)) 
