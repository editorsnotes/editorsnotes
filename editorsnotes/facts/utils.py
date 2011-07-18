import RDF
import json
import re
import logging
import unicodedata
from urllib import urlencode, quote, quote_plus
from urllib2 import urlopen, HTTPError, URLError
from urlparse import urlparse, urlunparse
from django.conf import settings

rdfs = RDF.NS('http://www.w3.org/2000/01/rdf-schema#')
skos = RDF.NS('http://www.w3.org/2004/02/skos/core#')
fb = RDF.NS('http://rdf.freebase.com/ns/')
gnd = RDF.NS('http://d-nb.info/gnd/')
dcterms = RDF.NS('http://purl.org/dc/terms/')
labels_context = RDF.Node(RDF.Uri('http://editorsnotes.org/labels/'))

def redland_error_handler(*args):
    if args[1] > 4:
        logging.warning(args[3][1:-1])

def load_statements(uri):
    statements = RDF.Model()
    #parser = RDF.Parser(name="guess")
    #parser.set_feature(
    #    'http://feature.librdf.org/raptor-wwwTimeout', 
    #    RDF.Node(literal="5"))
    #parser.parse_into_model(statements, uri, handler=redland_error_handler)
    statements.load(uri, handler=redland_error_handler)
    return statements

def open_triplestore(name=None):
    options = { 'dsn': settings.TRIPLESTORE_DSN,
                'user': settings.TRIPLESTORE_USER,
                'password': settings.TRIPLESTORE_PASSWORD }
    return RDF.Storage(
        storage_name=settings.TRIPLESTORE_ENGINE,
        name=(name or settings.TRIPLESTORE_NAME),
        options_string=','.join([ "%s='%s'" % i for i in options.items() ]))

def get_topic_context_node(topic, context='candidates'):
    return RDF.Node(RDF.Uri('http://editorsnotes.org%s%s/'
                            % (topic.get_absolute_url(), context)))

def get_source_uri(uri):
    return '%s://%s/' % urlparse(uri)[0:2]

def get_source_context_node(uri):
    return RDF.Node(RDF.Uri(get_source_uri(uri)))

def count_statements(model, context, where_clause):
    query = RDF.Query('SELECT (COUNT(*) AS ?count) '
                      + 'FROM <%s> ' % context
                      + where_clause,
                      query_language='vsparql')
    for result in model.execute(query):
        return int(result['count'].literal_value['string'])
    return 0

def count_all_statements(model, context):
    return count_statements(model, context, 'WHERE { ?s ?p ?o }')

def normalize_topic_name(name):
    name = unicodedata.normalize('NFC', name)
    name = re.sub(r'\([^\)]*\)|\d{4}', '', name)
    name = ' '.join(reversed([ part.strip() for part in name.split(',')[:2] ]))
    name = name.replace(u'\u201c', '"').replace(u'\u201d', '"')
    return name.strip()

def find_possible_uris(name, normalize=True):
    if normalize:
        name = normalize_topic_name(name)
    url = 'http://sameas.org/json?q=%s' % quote_plus(name.encode('utf-8'))
    logging.info(url.decode('UTF-8'))
    sets = []
    try:
        for uri_set in json.load(urlopen(url)):
            sets.append([ encode_uri(uri) for uri in uri_set['duplicates'] ])
    except ValueError:
        logging.warning(u'Bad JSON from %s' % url.decode('UTF-8'))
    except IOError:
        logging.warning(u'Network error connecting to %s' % url.decode('UTF-8'))
    return sets

def find_best_uris(model, name, normalize=True):
    sources_whitelist = [
        'http://d-nb.info/',
        'http://data.nytimes.com/',
        'http://dbpedia.org/',
        'http://rdf.freebase.com/',
        'http://viaf.org/',
        ]
    if normalize:
        name = normalize_topic_name(name)
    good_uris = []
    for uri_set in find_possible_uris(name, False):
        if len(uri_set) > 30: # probably bogus if we get this many
            continue
        for uri in uri_set:
            if not get_source_uri(uri) in sources_whitelist:
                continue
            labels = [ l[0] for l in get_labels(model, uri) ]
            if name in labels:
                good_uris = uri_set
                break
    best_uris = []
    for uri in good_uris:
        source_uri = get_source_uri(uri)
        if source_uri in sources_whitelist:
            best_uris.append(uri)
        else:
            logging.info(u'Rejecting source: %s' % source_uri.decode('UTF-8'))
    return best_uris

def encode_uri(uri):
    if not type(uri) is unicode:
        raise Exception('Expecting unicode URI')
    o = urlparse(uri.encode('utf-8'))
    return urlunparse(
        (o.scheme, o.netloc, quote(o.path), o.params, o.query, o.fragment))

def find_dbpedia_labels(uri):
    if type(uri) is unicode:
        raise Exception('URI must be UTF-8 encoded')
    query = 'SELECT ?label WHERE { <%s> <%s> ?label }' % (uri, rdfs.label)
    url = 'http://dbpedia.org/sparql?%s' % urlencode({ 
                'default-graph-uri': 'http://dbpedia.org',
                'query': query,
                'format': 'application/sparql-results+json' })
    labels = []
    try:
        result = json.load(urlopen(url))
        labels = [ (b['label']['value'], b['label']['xml:lang']) 
                   for b in result['results']['bindings'] ]
    except URLError as e:
        logging.warning(
            u'Finding DBpedia labels for <%s> failed: %s' % (
                uri.decode('UTF-8'), e))
    except HTTPError as e:
        logging.warning(
            u'Finding DBpedia labels for <%s> failed: %s' % (
                uri.decode('UTF-8'), e))
    except ValueError as e:
        logging.warning(
            u'Finding DBpedia labels for <%s> failed: %s' % (
                uri.decode('UTF-8'), e))
    return labels

labels_blacklist = [
    'http://upload.wikimedia.org/',
    'http://en.wikipedia.org/wiki/',
    'http://www4.wiwiss.fu-berlin.de/flickrwrappr/',
    ]
def find_labels(uri):
    label_properties = [ 
        rdfs.label, 
        fb['type.object.name'], 
        skos.prefLabel,
        gnd.preferredNameForThePerson,
        dcterms.title ]
    if type(uri) is unicode:
        raise Exception('URI must be UTF-8 encoded')
    for prefix in labels_blacklist:
        if uri.startswith(prefix):
            return []
    if uri.startswith('http://dbpedia.org/resource/'):
        return find_dbpedia_labels(uri)
    if uri.startswith(fb._prefix): # freebase
        identifier = uri[len(fb._prefix):]
        if '/' in identifier:
            # the URI should use 'dot notation'
            # see http://wiki.freebase.com/wiki/RDF
            uri = str(fb[identifier.replace('/', '.')])
    labels = []
    subject = RDF.Node(RDF.Uri(uri))
    statements = load_statements(uri)
    for statement in statements:
        if (statement.subject == subject and
            statement.predicate in label_properties and
            statement.object.is_literal()):
            labels.append((statement.object.literal[0],
                           statement.object.literal[1]))
    return labels

def check_object_literal_language(statement):
    if (statement.object.is_literal() and
        statement.object.literal[1] is None):
        # virtuoso needs a language, see http://bit.ly/kC0nfQ
        return RDF.Statement(
            statement.subject, statement.predicate,
            RDF.Node(literal=statement.object.literal[0], language='en'))
    return statement

def label_statement(uri, label, lang=None):
    if lang is not None:
        lang = str(lang) # virtuoso barfs on unicode lang strings
    return check_object_literal_language(
        RDF.Statement(
            RDF.Uri(uri), rdfs.label,
            RDF.Node(literal=label, language=lang)))

def add_label(model, uri, label, lang=None):
    model.append(label_statement(uri, label, lang), labels_context)

def cache_labels(model, uri, labels):
    for label, lang in labels:
        add_label(model, uri, label, lang)

def remove_cached_labels(model, uri):
    if type(uri) is unicode:
        raise Exception('URI must be UTF-8 encoded')
    template = '<%s> <%s> ?label' % (uri, rdfs.label)
    query = RDF.Query('DELETE FROM <%s> { %s } WHERE { %s}' 
                      % (labels_context, template, template), 
                      query_language='vsparql')
    model.execute(query)

def remove_statements_with_context(model, context):
    template = '?s ?p ?o'
    query = RDF.Query('DELETE FROM <%s> { %s } WHERE { %s }' 
                      % (context, template, template), 
                      query_language='vsparql')
    model.execute(query)

def get_cached_labels(model, uri):
    labels = []
    query = RDF.Statement(RDF.Uri(uri), rdfs.label, None)
    for statement in model.find_statements(query, labels_context):
        labels.append((statement.object.literal[0],
                       statement.object.literal[1]))
    return labels

def get_labels(model, uri):
    if type(uri) is RDF.Node or type(uri) is RDF.Uri:
        uri = str(uri)
    labels = []
    try:
        labels = get_cached_labels(model, uri)
    except RDF.RedlandError as e:
        logging.warning(u'Bogus URI: <%s>' % uri.decode('UTF-8'))
        return labels
    if len(labels) == 0:
        labels = find_labels(uri)
        cache_labels(model, uri, labels)
    return labels

def get_cached_label(model, uri, lang=None):
    if type(uri) is unicode:
        raise Exception('URI must be UTF-8 encoded')
    source_context = get_source_context_node(uri)
    queryfilter = ''
    if lang: queryfilter = "FILTER langMatches(lang(?label), '%s')" % lang
    sparql = '''DEFINE input:same-as "yes"
SELECT ?label 
FROM <%s> 
FROM <%s>
WHERE { 
<%s> <%s> ?label %s
} LIMIT 1''' % (labels_context, source_context, uri, rdfs.label, queryfilter)
    query = RDF.Query(sparql, query_language='vsparql')
    for result in model.execute(query):
        return result['label'].literal_value['string']
    return None

def load_triples(model, context, uri, reject=lambda s: False, source=None):
    if type(uri) is unicode:
            raise Exception('URI must be UTF-8 encoded')
    primary_subject = RDF.Node(RDF.Uri(uri))
    logging.info(u'<%s>' % primary_subject)
    if source is None:
        source = get_source_context_node(uri)
    count = 0
    predicate_uris = set()
    object_uris = set()
    statements = load_statements(uri)
    for statement in statements:
        statement = check_object_literal_language(statement)
        predicate_uris.add(statement.predicate.uri)
        if statement.object.is_resource():
            object_uris.add(statement.object.uri)
        model.add_statement(statement, source)
        if statement.subject == primary_subject and not reject(statement):
            model.add_statement(statement, context)
            count += 1
    logging.info('Loaded %s statements.' % count)
    return count, predicate_uris, object_uris
