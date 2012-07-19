from django.core.management.base import LabelCommand, CommandError
from django.db import transaction
from django.conf import settings
from editorsnotes.main.models import Topic, Document
from editorsnotes.refine.models import TopicCluster, DocumentCluster
from google.refine import refine
from urllib2 import URLError
import datetime
import json
import os

class Command(LabelCommand):
    args = '<object label>'
    label = 'type of object to be clustered'
    help = 'Clusters topics in the database using Google Refine'
    
    def handle_label(self, target_model, **options):
        acceptable_models = ['topic', 'document']
        if target_model not in acceptable_models:
            raise CommandError(
                'Only the following models can be clustered: %s\n' % (
                    ', '.join(acceptable_models)))
        self.cluster(target_model)

    def connect(self):
        try:
            refine.REFINE_HOST = settings.GOOGLE_REFINE_HOST
            refine.REFINE_PORT = settings.GOOGLE_REFINE_PORT
        except AttributeError:
            raise CommandError(
                'Set GOOGLE_REFINE_HOST and GOOGLE_REFINE_PORT in settings')
        try:
            server = refine.RefineServer()
            refine_instance = refine.Refine(server)
            server.get_version()
        except URLError:
            raise CommandError('Google Refine server is not reachable.')
        return refine_instance

    def cluster(self, target_model):

        def dump_objects(model):
            if model == 'topic':
                obj_list = [ ( str(t.id), t.as_text() )
                             for t in Topic.objects.all() ]
            elif model == 'document':
                obj_list = [ ( str(d.id), d.as_text() )
                             for d in Document.objects.all() ]
            output_filename = '%s-list.txt' % model
            output = open(output_filename, 'w')
            for record in obj_list:
                output.write(('\t'.join(record) + '\n').encode('utf-8'))
            output.close()
            return output_filename

        # Statistics
        cluster_count = 0

        # Start a new Refine project
        refine_instance = self.connect()
        object_dump_filename = dump_objects(target_model)
        refine_project = refine_instance.new_project(
            project_file=object_dump_filename,
            header_lines=0,
            project_name='editorsnotes-%s-%s' % (
                target_model, datetime.datetime.now().strftime('%Y%m%d')))

        # Set up cluster parameters
        refine_project.clusterer_defaults['cologne'] = {
            'column': 'Column2',
            'type' : 'binning',
            'function' : 'cologne-phonetic',
            'params' : {}
        }
        refine_project.clusterer_defaults['metaphone3'] = {
            'column' : 'Column2',
            'type' : 'binning',
            'function' : 'metaphone3',
            'params' : {}
        }
        
        for method in refine_project.clusterer_defaults:
            self.stderr.write('Clustering using method %s... ' % method)
            cluster_list = refine_project.compute_clusters('Column2', method)
            cluster_count += self.write_clusters(target_model, cluster_list)
            
        #Delete Refine project
        refine_project.delete()
        self.stderr.write(
            '\nRefine process successful. %s total clusters created\n\n' % str(cluster_count))
        
    @transaction.commit_on_success
    def write_clusters(self, model_name, cluster_list):
        new_cluster_count = 0

        for cluster in filter(lambda x: len(x) < 5, cluster_list):
            unique_cluster_set = True

            if model_name == 'topic':
                potential_cluster = [ Topic.objects.get(
                    preferred_name=match['value']) for match in cluster ]
            elif model_name == 'document':
                potential_cluster = [ document.objects.get(
                    name=match['value']) for match in cluster ]

            # Clusters will not be created from objects which are already in
            # another cluster, to avoid confusion. They can be picked up in
            # later passes.
            if any(map(lambda x: x.in_cluster.count(), potential_cluster)):
                continue

            if model_name == 'topic':
                new_cluster_object = TopicCluster.objects.create()
                for t in potential_cluster:
                    new_cluster_object.topics.add(t)
            if model_name == 'document':
                new_cluster_object = DocumentCluster.objects.create()
                for d in potential_cluster:
                    new_cluster_object.documents.add(d)

            new_cluster_object.message = 'Created automatically'
            new_cluster_object.save()
            new_cluster_count += 1

        self.stderr.write('%s clusters created.\n' % str(new_cluster_count))
        return new_cluster_count
