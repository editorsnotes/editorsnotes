from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from editorsnotes.main.models import Topic
from pprint import pformat
import RDF
import re
import json
import utils

excluded_predicates = re.compile(r'|'.join((
    r'^http://RDVocab\.info/ElementsGr2/identifierForThePerson$',
    r'^http://creativecommons\.org/ns#.+',
    r'^http://d-nb\.info/gnd/countryCodeForThePerson$',
    r'^http://data\.nytimes\.com/elements/(?!topicPage)',
    r'^http://dbpedia\.org/property/bgcolour$',
    r'^http://dbpedia\.org/property/hasPhotoCollection$',
    r'^http://dbpedia\.org/property/wikiPageUsesTemplate$',
    r'^http://rdf\.freebase\.com/ns/base\..+',
    r'^http://rdf\.freebase\.com/ns/common\.topic\.article$',
    r'^http://rdf\.freebase\.com/ns/people\.person\.places_lived$',
    r'^http://rdf\.freebase\.com/ns/type\.object\.key$',
    r'^http://rdf\.freebase\.com/ns/user\..+',
    r'^http://www\.w3\.org/1999/xhtml/vocab#license$',
    r'^http://www\.w3\.org/2002/07/owl#sameAs$',
    r'^http://www\.w3\.org/2004/02/skos/core#inScheme$',
)))

@login_required
def topic_facts(request, topic_slug):
    topic = get_object_or_404(Topic, slug=topic_slug)
    model = RDF.Model(utils.open_triplestore())
    candidates = utils.get_topic_context_node(topic)
    print candidates
    subjects = {}
    for statement in model.as_stream(candidates):
        p = str(statement.predicate.uri)
        if excluded_predicates.match(p):
            continue
        o = statement.object
        if o.is_blank():
            continue
        s = str(statement.subject.uri)
        if not s in subjects:
            subjects[s] = {}
        if not p in subjects[s]:
            subjects[s][p] = []
        subjects[s][p].append(o)
    o = {}
    o['topic'] = topic
    o['candidates'] = subjects
    return render_to_response(
        'topic-facts.html', o, context_instance=RequestContext(request))

