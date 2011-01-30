from django.core.management.base import LabelCommand, CommandError
from django.utils.encoding import smart_str
from django.db import transaction
from lxml import etree
from lxml.html.builder import P, BR
from os import path
from difflib import ndiff
from optparse import make_option
from itertools import chain
from main.models import User, Document, Transcript, Topic, TopicAssignment

NS = { 'fmp': 'http://www.filemaker.com/fmpxmlresult' }

class Command(LabelCommand):
    args = '<xml_filename xml_filename ...>'
    label = 'XML filename'
    help = 'Imports the specified XML files.'
    option_list = LabelCommand.option_list + (
        make_option('-u',
                    '--username',
                    action='store',
                    default='ryanshaw',
                    help='username that will create/update documents'),
        make_option('-f',
                    '--force-update',
                    action='store_true',
                    default=False,
                    help='update documents whether or not they have changed'),
        )
    def handle_label(self, filename, **options):
        if not path.isfile(filename):
            raise CommandError('%s is not a file.' % filename)
        try:
            doc = etree.parse(filename)
        except etree.LxmlError as e:
            raise CommandError('could not parse %s:\n  %s' % (filename, e))
        root = doc.getroot()
        if root.tag == '{%s}FMPXMLRESULT' % NS['fmp']:
            self.handle_filemaker(doc, **options)
        else:
            raise CommandError('unknown XML schema: %s' % root)

    @transaction.commit_on_success
    def handle_filemaker(self, root, **options):

        # Prefix to append to import IDs.
        ID_PREFIX = 'inglis:'

        # Load user to create/update documents as.
        try:
            user = User.objects.get(username=options['username'])
        except User.DoesNotExist:
            raise CommandError('unknown user: %s' % options['username'])

        # Verify that we have the fields we expect.
        f = expected_fields = [ 'CardID',
                                'CardHeading',
                                'Transcription',
                                'CardType',
                                'CardFormat',
                                'Language',
                                'ContributorJoin::Contributors',
                                'SubjectJoin::Subject',
                                'OrganizationJoin::Organizations',
                                'Citation',
                                'CatalogLink',
                                'ResourceLink',
                                'AdditionalNotes',
                                'DateEntered' ]
        fields = root.xpath('./fmp:METADATA/fmp:FIELD/@NAME', namespaces=NS)
        if not fields == expected_fields:
            new_fields = [ f for f in fields if not f in expected_fields ]
            missing_fields = [ f for f in expected_fields if not f in fields ]
            message = 'fields have changed:\n'
            message += '\n'.join(ndiff(expected_fields, fields)) + '\n\n'
            if missing_fields:
                message += ('Missing fields:\n  ' + '\n  '.join(missing_fields))
            if new_fields:
                message += ('Unexpected fields:\n  ' + '\n  '.join(new_fields))
            raise CommandError(message)

        # Utility functions for accessing XML data.
        def text(e):
            text = e.text or ''
            for child in e:
                if not child.tag == '{%s}BR' % NS['fmp']:
                    raise CommandError('Unexpected element: %s' % child)
                text += ('\n%s' % (child.tail or ''))
            return text.strip()
        def values(row, field):
            return list(set(
                    [ v for v in [ text(e) for e in row[f.index(field)] ] if v ]))
        def value(row, field):
            v = values(row, field)
            if len(v) == 0:
                return None
            elif len(v) == 1:
                return v[0]
            else:
                raise CommandError('multiple values for %s in record %s'
                                   % (field, row.get('RECORDID')))
        def row_to_dict(row):
            d = {}
            for field in f:
                if 'Join::' in field:
                    d[field] = values(row, field)
                else:
                    d[field] = value(row, field)
            return d

        # Statistics.
        created_count = topics_created_count = changed_count = unchanged_count = skipped_count = 0

        for row in root.xpath('./fmp:RESULTSET/fmp:ROW', namespaces=NS):
            try:
                md = row_to_dict(row)
                for field in [ 'CardID', 'CardHeading', 'CardType' ]:
                    if md[field] is None:
                        raise CommandError('missing %s value in record %s'
                                           % (field, row.get('RECORDID')))
            except CommandError as e:
                self.stderr.write(self.style.ERROR('Warning: %s\n' % e))
                skipped_count += 1
                continue

            description = P('%s -- %s -- Agnes Inglis card #%s'
                            % (md['CardHeading'], md['CardType'], md['CardID']))
            document, created = Document.objects.get_or_create(
                import_id=(ID_PREFIX + md['CardID']),
                defaults={ 'description': description,
                           'creator': user, 'last_updater': user })
            document.description = description
            document.language = md['Language']
            document.save()

            # Set document topics.
            for topic_assignment in document.topics.all():
                topic_assignment.delete()
            def assign_topic(document, user, topic_name, topic_type=''):
                topic, topic_created = Topic.objects.get_or_create(
                    slug=Topic.make_slug(topic_name),
                    defaults={ 'preferred_name': topic_name,
                               'creator': user, 'last_updater': user })
                topic.type = topic_type
                topic.save()
                TopicAssignment.objects.create(
                    content_object=document, topic=topic, creator=user)
                if topic_created:
                    return 1
                else:
                    return 0
            for topic_name in md['ContributorJoin::Contributors']:
                topics_created_count += assign_topic(
                    document, user, topic_name, 'PER')
            for topic_name in md['OrganizationJoin::Organizations']:
                topics_created_count += assign_topic(
                    document, user, topic_name, 'ORG')
            for topic_name in md['SubjectJoin::Subject']:
                topics_created_count += assign_topic(
                    document, user, topic_name)

            # Set document links.
            for link in document.links.all():
                link.delete()
            for url in [ md['CatalogLink'], md['ResourceLink'] ]:
                if url is not None:
                    document.links.create(url=url, creator=user)

            # Set document metadata.
            changed = document.set_metadata(md, user)

            # Create or update document transcript.
            transcript_html = P(*list(chain.from_iterable(
                        ( (line, BR()) for line 
                          in md['Transcription'].split('\n') )))[:-1])
            if created:
                Transcript.objects.create(
                    document=document, 
                    content=transcript_html,
                    creator=user, last_updater=user)
                created_count += 1
            elif changed or options['force_update']:
                document.transcript.content = transcript_html
                document.transcript.last_updater = user
                document.transcript.save()
                document.last_updater = user
                document.save()
                changed_count += 1
            else:
                unchanged_count += 1
        
        self.stderr.write('%s records skipped.\n' % skipped_count)
        self.stderr.write('%s new documents created.\n' % created_count)
        self.stderr.write('%s new topics created.\n' % topics_created_count)
        self.stderr.write('%s documents updated.\n' % changed_count)
        self.stderr.write('%s documents unchanged.\n' % unchanged_count)







