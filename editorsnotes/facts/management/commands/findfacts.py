from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from editorsnotes.facts import utils
from editorsnotes.main.models import Topic
from time import sleep
from urllib import urlencode
from urllib2 import urlopen, URLError
import RDF
import json
import logging
import os
import re
import signal
import sys

pause = 0.5 # seconds
logging.basicConfig(
    level=logging.INFO, format='%(message)s', stream=sys.stdout)

class Command(NoArgsCommand):
    help = 'Loads statements about topics from the linked data cloud.'
    def load_labels(self, model, uris):
        for uri in uris:
            labels = utils.get_labels(model, uri)
            if len(labels) == 0:
                logging.debug('No labels for <%s>' % uri)
            sleep(pause)
    def load_triples(self, model, topic):
        def reject(statement):
            if statement.object.is_literal():
                return (not statement.object.literal[1].startswith('en'))
            return False
        logging.info('\n' + ('-' * 80))
        logging.info(u'%s: %s' % (topic.id, topic))
        logging.info('-' * 80)
        context = utils.get_topic_context_node(topic)
        count = utils.count_all_statements(model, context)
        if count > 0:
            logging.info('%s statements already loaded.' % count)
        else: 
            for uri in utils.find_best_uris(model, topic.preferred_name):
                try:
                    count, predicate_uris, object_uris = utils.load_triples(
                        model, context, uri, reject)
                    self.load_labels(
                        model, list(predicate_uris) + list(object_uris))
                    sleep(pause)
                except RDF.RedlandError as e:
                    logging.debug('Failed to parse <%s>: %s' % (uri, e))
        if count > 0:
            topic.has_candidate_facts = True
            topic.save()
    def signal_handler(self, signal, frame):
        logging.info('Quitting...')
        self.quit = True
    def handle_noargs(self, **options):
        start_id = None
        if os.path.exists('start-from-topic-id.txt'):
            with open('start-from-topic-id.txt') as f:
                start_id = int(f.read())
        self.quit = False
        signal.signal(signal.SIGINT, self.signal_handler)
        model = RDF.Model(utils.open_triplestore())
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
            self.load_triples(model, topic)
        if not self.quit:
            if os.path.exists('start-from-topic-id.txt'):
                os.remove('start-from-topic-id.txt')
                

                

        
        
