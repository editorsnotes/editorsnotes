from django.core.management.base import BaseCommand, CommandError
from editorsnotes.facts import utils
import RDF

class Command(BaseCommand):
    args = '<graph> <turtle_file>'
    help = 'Loads arbitrary statements to the specified graph.'
    def handle(self, *args, **options):
        if not len(args) == 2:
            raise CommandError('Usage: loadfacts %s' % self.args)
        facts = RDF.Model()
        context = RDF.Node(RDF.Uri(args[0]))
        turtle_file = args[1]
        def handler(*args):
            raise CommandError(
                'Failed to load %s: %s' % (turtle_file, args[3]))
        facts.load('file:%s' % turtle_file, name='turtle', handler=handler)
        model = RDF.Model(utils.open_triplestore())
        for statement in facts:
            model.append(statement, context)
        self.stderr.write(
            'Loaded %s facts into <%s>.\n' % (len(facts), context))

