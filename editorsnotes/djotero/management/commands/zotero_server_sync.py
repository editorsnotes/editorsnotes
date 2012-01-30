from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import datetime
import urllib2
import json
from editorsnotes.djotero.models import ZoteroLink

url = 'https://api.zotero.org/groups/46844/items?key=r0KBtuDLU0Jh2s1jAPVLZymn'

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-n',
                    '--no-write',
                    action='store_true',
                    default=False,
                    dest='no_write',
                    help='Show what documents would be written'),
    )
    def handle(self, *args, **options):
        to_sync = [z for z in ZoteroLink.objects.all()
                   if not z.last_synced or z.last_synced < z.modified]
        self.stdout.write('Processing %s records...\n' % len(to_sync))
        
        def items_to_dict(item_list):
            data = {}
            data['items'] = [json.loads(z.zotero_data) for z in item_list]
            return json.dumps(data)

        def write_data(data):
            req = urllib2.Request(url, data, {'Content-Type' :
                                              'application/json'}) 
            f = urllib2.urlopen(req)
            code = f.code
            response = f.read()
            f.close()
            return code, response

        if options['no_write']:
            self.stdout.write(items_to_dict(to_sync))
        else:
            while len(to_sync) > 0:
                ITEMS_PER_REQUEST = 10
                data = items_to_dict(to_sync[:ITEMS_PER_REQUEST])
                written = write_data(data)
                if written[0] == 201:
                    now = datetime.datetime.now()
                    for item in to_sync[:ITEMS_PER_REQUEST]:
                        item.modified = now
                        item.last_synced = now
                        item.save()
                    print 'ok!'
                else:
                    print str(written[0])
                to_sync[:ITEMS_PER_REQUEST] = []
