from django.core.management.base import BaseCommand

from ... import en_index

class Command(BaseCommand):
    help = 'Rebuild elasticsearch index'
    def handle(self, *args, **kwargs):
        for doc_type in en_index.document_types.values():
            ct = doc_type.model.objects.count()
            self.stdout.write(u'Creating {:,} "{}" documents'.format(ct, doc_type))
            doc_type.update_all()
