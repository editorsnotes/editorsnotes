from django.core.management.base import BaseCommand, CommandError
from editorsnotes.facts import utils
from time import sleep
import RDF
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG, format='%(message)s', stream=sys.stdout)

class Command(BaseCommand):
    args = '<uris_file> [<start_index>]'
    help = 'Loads labels for every uri in the specified file.'
    def handle(self, *args, **options):
        if not len(args) in [1,2]:
            raise CommandError('Usage: loadlabels %s' % self.args)
        model = RDF.Model(utils.open_triplestore())
        try:
            with open(args[0]) as f:
                if len(args) == 2:
                    start_index = int(args[1])
                else:
                    start_index = 0
                for i, line in enumerate(f):
                    if i < start_index:
                        continue
                    print >> sys.stderr, '%s' % i
                    uri = line.strip()
                    labels = utils.get_labels(model, uri)
                    if len(labels) == 0:
                        logging.debug(
                            u'%s: No labels found for <%s>' 
                            % (i, uri.decode('UTF-8')))
                    sleep(0.25)
        except IOError as e:
            raise CommandError(e)
        except ValueError as e:
            raise CommandError(e)
