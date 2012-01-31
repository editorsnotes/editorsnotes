from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import datetime
import urllib2
import json
from django.conf import settings
from editorsnotes.djotero.models import ZoteroLink

try:
    url = 'https://api.zotero.org/%s/items?key=%s' % (
        settings.ZOTERO_LIBRARY, settings.ZOTERO_API_KEY)
except:
    raise CommandError, 'Set ZOTERO_LIBRARY and ZOTERO_API_KEY in settings.'

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-n',
                    '--no-write',
                    action='store_true',
                    default=False,
                    help='Show what documents would be written'),
        make_option('-c',
                    '--count',
                    action='store',
                    type=int,
                    default=15,
                    help='Number of records to sort with each request to server (1-50)'
                   ),
    )
    def handle(self, *args, **options):
        def items_to_dict(item_list):
            data = {}
            data['items'] = [json.loads(z.zotero_data) for z in item_list]
            return json.dumps(data)
        def write_data(data):
            req = urllib2.Request(url, data, {'Content-Type' : 'application/json'})
            f = urllib2.urlopen(req)
            code = f.code
            response = f.read()
            f.close()
            return code, response
        
        # Zotero server API allows up to 50 items at a time
        ITEMS_PER_REQUEST = options.get('count', 15)
        if not 1 <= ITEMS_PER_REQUEST <= 50:
            i = ITEMS_PER_REQUEST
            raise CommandError, '''
Number of items per request must be between 1 and 50. Value given: %s''' % i

        # Get all items which have not been synced before their last update
        to_sync = [z for z in ZoteroLink.objects.all()
                   if not z.last_synced or z.last_synced < z.modified]
        self.stdout.write('Processing %s records...\n' % len(to_sync))

        if options['no_write']:
            self.stdout.write(items_to_dict(to_sync))
        else:
            while len(to_sync) > 0:
                data = items_to_dict(to_sync[:ITEMS_PER_REQUEST])
                code, response = write_data(data)
                if code == 201:
                    now = datetime.datetime.now()
                    for item in to_sync[:ITEMS_PER_REQUEST]:
                        item.modified = now
                        item.last_synced = now
                        item.save(update_modified=False)
                    print 'ok!'
                else:
                    print 'Server sync failed with code %s' % str(code)
                to_sync[:ITEMS_PER_REQUEST] = []
