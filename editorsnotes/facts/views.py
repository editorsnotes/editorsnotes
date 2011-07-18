from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from editorsnotes.main.models import Topic
from editorsnotes.main.utils import alpha_columns
from pprint import pformat
from urlparse import urlparse
import RDF
import re
import json
import utils

excluded_sources = [
    'http://sw.opencyc.org/',
    'http://www4.wiwiss.fu-berlin.de/',
]

excluded_predicates = re.compile(r'|'.join((
    r'^http://RDVocab\.info/ElementsGr2/identifierForThePerson$',
    r'^http://creativecommons\.org/ns#.+',
    r'^http://d-nb\.info/gnd/countryCodeForThePerson$',
    r'^http://d-nb\.info/gnd/invalidIdentifierForThePerson$',
    r'^http://data\.nytimes\.com/elements/(?!topicPage)',
    r'^http://dbpedia\.org/property/bgcolour$',
    r'^http://dbpedia\.org/property/hasPhotoCollection$',
    r'^http://dbpedia\.org/property/wikiPageUsesTemplate$',
    r'^http://rdf\.freebase\.com/ns/base\..+',
    r'^http://rdf\.freebase\.com/ns/common\.topic\.article$',
    r'^http://rdf\.freebase\.com/ns/people\.person\.places_lived$',
    r'^http://rdf\.freebase\.com/ns/type\.object\.key$',
    r'^http://rdf\.freebase\.com/ns/user\..+',
    r'^http://sw\.cyc\.com/CycAnnotations_v1#.+',
    r'^http://sw\.opencyc\.org/2009/04/07/concept/Mx4rBVVEokNxEdaAAACgydogAg$',
    r'^http://sw\.opencyc\.org/2009/04/07/concept/en/quotedIsa$',
    r'^http://sw\.opencyc\.org/concept/Mx4rBVVEokNxEdaAAACgydogAg$',
    r'^http://www\.w3\.org/1999/xhtml/vocab#license$',
    r'^http://www\.w3\.org/2002/07/owl#sameAs$',
    r'^http://www\.w3\.org/2004/02/skos/core#inScheme$',
    r'^http://dbpedia\.org/ontology/individualisedPnd$',
)))

@login_required
def topic_facts(request, topic_slug):
    topic = get_object_or_404(Topic, slug=topic_slug)
    model = RDF.Model(utils.open_triplestore())
    candidates = utils.get_topic_context_node(topic)
    sources = {}
    excluded_subjects = set()
    #predicate_objects_by_source = {}
    for statement in model.as_stream(candidates):
        p = str(statement.predicate.uri)
        if excluded_predicates.match(p):
            continue
        o = statement.object
        if o.is_blank():
            continue
        s = str(statement.subject.uri)
        if p == 'http://dbpedia.org/ontology/wikiPageRedirects':
            excluded_subjects.add(s)
        source = '%s://%s/' % urlparse(s)[0:2]
        if source in excluded_sources:
            continue
        #if (p,o) in predicate_objects_by_source.get(source, []):
        #    continue
        if not source in sources:
            sources[source] = {}
            #predicate_objects_by_source[source] = []
        if not s in sources[source]:
            sources[source][s] = {}
        if s in excluded_subjects:
            del sources[source][s]
            continue
        if not p in sources[source][s]:
            sources[source][s][p] = []
        sources[source][s][p].append(o)
        #predicate_objects_by_source[source].append((p,o))
    o = {}
    o['topic'] = topic
    o['candidates'] = sources
    return render_to_response(
        'topic-facts.include', o, context_instance=RequestContext(request))

@login_required
def dashboard(request, project_slug=None):
    o = {}
    if 'type' in request.GET:
        o['type'] = request.GET['type']
        template = 'topic-columns.include'
    else:
        o['type'] = 'candidates'
        template = 'facts-dashboard.html'
    if project_slug:
        o['project'] = get_object_or_404(Project, slug=project_slug)
        if o['type'] == 'candidates':
            query_set = set(
                [ ta.topic for ta in TopicAssignment.objects.filter(
                        creator__userprofile__affiliation=o['project'],
                        topic__has_candidate_facts=True) ])
        else:
            query_set = set(
                [ ta.topic for ta in TopicAssignment.objects.filter(
                        creator__userprofile__affiliation=o['project'],
                        topic__has_accepted_facts=True) ])
    else:
        if o['type'] == 'candidates':
            query_set = Topic.objects.filter(has_candidate_facts=True)
        else:
            query_set = Topic.objects.filter(has_accepted_facts=True)
    [o['topics_1'], o['topics_2'], o['topics_3']] = alpha_columns(
        query_set, 'slug', itemkey='topic')
    return render_to_response(
        template, o, context_instance=RequestContext(request))
    
