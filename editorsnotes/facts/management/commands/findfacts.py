from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from editorsnotes.main.models import Topic
from urllib import urlopen, urlencode
from urlparse import urlparse
from time import sleep
import json
import RDF
import re
import signal
import os

pause = 0.5 # seconds
rdfs = RDF.NS('http://www.w3.org/2000/01/rdf-schema#')

def open_triplestore(name=None):
    options = { 'dsn': settings.TRIPLESTORE_DSN,
                'user': settings.TRIPLESTORE_USER,
                'password': settings.TRIPLESTORE_PASSWORD }
    return RDF.Storage(
        storage_name=settings.TRIPLESTORE_ENGINE,
        name=(name or settings.TRIPLESTORE_NAME),
        options_string=','.join([ "%s='%s'" % i for i in options.items() ]))

class Command(NoArgsCommand):
    help = 'Loads statements about topics from the linked data cloud.'
    def log(self, message):
        self.stdout.write('%s\n' % message)
        self.stdout.flush()
    def topic_context_node(self, topic):
        return RDF.Node(RDF.Uri('http://editorsnotes.org%scandidates/'
                                % topic.get_absolute_url()))
    def load_triples(self, model, topic, uri):
        try:
            self.log('<%s>' % RDF.Uri(uri))
            source = RDF.Node(RDF.Uri('%s://%s/' % urlparse(uri)[0:2]))
            context = self.topic_context_node(topic)
            count = 0
            parser = RDF.Parser(name='rdfxml')
            for statement in parser.parse_as_stream(uri):
               model.add_statement(statement, source)
               model.add_statement(statement, context)
               count += 1
            self.log('Loaded %s statements.' % count)
            sleep(pause)
        except RDF.RedlandError as e:
            if re.search(r'Connect failed', str(e)):
                raise CommandError(e)
            self.log('Load failed.')
        except ValueError as e:
            self.log('Load failed: %s' % e)
    def sparql_query(self, query, endpoint='http://dbpedia.org/sparql', 
                 default_graph='http://dbpedia.org',
                 format='application/sparql-results+json'):
        url = '%s?%s' % (endpoint, urlencode({ 
                    'default-graph-uri': default_graph, 'query': query,
                    'format': format }))
        try:
            return json.load(urlopen(url))
        except ValueError:
            self.log('Bad JSON from %s' % url)
        except IOError:
            self.log('Network error connecting to %s' % url)
        return None
    def get_dbpedia_labels(self, uri):
        query = 'SELECT ?label WHERE { <%s> <%s> ?label }' % (uri, rdfs.label)
        result = self.sparql_query(query)
        if result is None:
            return set()
        else:
            return set(
                [ b['label']['value'] for b in result['results']['bindings'] ])
    def get_labels(self, uri):
        if uri.startswith('http://dbpedia.org/resource/'):
            return self.get_dbpedia_labels(uri)
        labels = set()
        try:
            parser = RDF.Parser(name='rdfxml')
            for statement in parser.parse_as_stream(uri):
                if (statement.predicate == rdfs.label and 
                    statement.object.is_literal()):
                    labels.add(statement.object.literal[0])
        except RDF.RedlandError, ValueError:
            self.log('Failed to parse <%s>' % uri)
        return labels
    def is_reasonable(self, name, uris):
        for uri in uris:
            if name in self.get_labels(uri):
                return True
            sleep(pause)
        return False
    def normalize_topic_name(self, name):
        name = re.sub(r',?\s*\(no dates\)', '', name)
        name = re.sub(r',?\s*\(?(b\.\s)?\d{4}-?(\d{4})?\)?', '', name)
        name = ' '.join(reversed([ part.strip() for part in name.split(',') ]))
        name = filter(lambda x: x.isalpha() 
                      or x.isspace() or x in ['.','-'], name)
        return name.strip().encode('utf-8')
    def find_uris(self, topic):
        name = self.normalize_topic_name(topic.preferred_name)
        url = 'http://sameas.org/json?%s' % urlencode({ 'q': name })
        self.log(url)
        try:
            response = json.load(urlopen(url))
            for uri_set in response:
                if int(uri_set['numDuplicates']) > 30:
                    continue # probably bad data if we get this many
                uris = uri_set['duplicates']
                if self.is_reasonable(name, uris):
                    return uris
        except ValueError:
            self.log('Bad JSON from %s' % url)
        except IOError:
            self.log('Network error connecting to %s' % url)
        return []
    def count_statements(self, model, topic):
        query = RDF.Query('SELECT (COUNT(*) AS ?count) '
                          + 'FROM <%s> where { ?s ?p ?o }' 
                          % self.topic_context_node(topic), 
                          query_language='vsparql')
        for result in model.execute(query):
            return int(result['count'].literal_value['string'])
        return 0
    def signal_handler(self, signal, frame):
        self.log('Quitting...')
        self.quit = True
    def handle_noargs(self, **options):
        model = RDF.Model(open_triplestore())
        start_id = None
        if os.path.exists('start-from-topic-id.txt'):
            with open('start-from-topic-id.txt') as f:
                start_id = int(f.read())
        self.quit = False
        signal.signal(signal.SIGINT, self.signal_handler)
        for topic in Topic.objects.exclude(type=''):
            if start_id is not None:
                if topic.id == start_id:
                    start_id = None
                else:
                    continue
            if self.quit:
                with open('start-from-topic-id.txt', 'w') as f:
                    f.write(str(topic.id))
                break
            self.log('\n--------------------------------------------------------------------------------')
            self.log('%s: %s' % (topic.id, topic))
            self.log('--------------------------------------------------------------------------------')
            count = self.count_statements(model, topic)
            if count > 0:
                self.log('%s statements already loaded.' % count)
            else: 
                for uri in self.find_uris(topic):
                    self.load_triples(model, topic, uri)
                

                

        
        
