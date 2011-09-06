from django.core.management.base import LabelCommand, CommandError
from django.db import transaction
from django.conf import settings
from google.refine import refine
from editorsnotes.main.models import Topic
from editorsnotes.refine.models import TopicCluster
from urllib2 import URLError
import json

class Command(LabelCommand):
    args = '<object label>'
    label = 'type of object to be clustered'
    help = 'Clusters topics in the database using Google Refine'
    
    def handle_label(self, target_model, **options):
        acceptable_models = ['topics']
        if target_model not in acceptable_models:
            raise CommandError('Only the following model objects can be clustered: %s\n' % ', '.join(acceptable_models))
        try:
            refine.REFINE_HOST = settings.GOOGLE_REFINE_HOST
            refine.REFINE_PORT = settings.GOOGLE_REFINE_PORT
        except AttributeError:
            raise CommandError('Assign values GOOGLE_REFINE_HOST and GOOGLE_REFINE_PORT in settings')
        self.cluster(target_model)
        
    def cluster(self, target_model):
        
        #Make sure Google Refine server is reachable
        try:
            server = refine.RefineServer()
            refine_instance = refine.Refine(server)
            server.get_version()
        except URLError:
            raise CommandError('Google Refine server is not reachable.')
        
        #Create text file of all topics, to be fed into Refine
        topic_list = []
        for topic in Topic.objects.all():
            topic_list.append(u'\t'.join(
                [str(topic.id),
                topic.as_text()]) +
                '\n')
        output = open('topics-list.txt', 'w')
        for record in topic_list:
           output.write(record.encode('utf-8'))
        output.close()

        #Start a new Refine project
        refine_project = refine_instance.new_project(
            project_file='topics-list.txt',
            project_name='editorsnotes-topics',
            header_lines=0
            )

        #Set up cluster parameters & create clusters in Refine
        refine_project.clusterer_defaults['cologne'] = {
            'column': 'Column2',
            'type' : 'binning',
            'params' : {},
            'function' : 'cologne-phonetic'
            }
        refine_project.clusterer_defaults['metaphone3'] = {
            'type' : 'binning',
            'function' : 'metaphone3',
            'column' : 'Column2',
            'params' : {}
            }
        
        #Statistics
        cluster_count = 0
        all_objects = []
        
        #Delete old clusters
        for x in TopicCluster.objects.all():
            x.delete()
        
        def create_clusters(column, method):
            return refine_project.compute_clusters(column, method)
        
        for method in refine_project.clusterer_defaults:
            self.stderr.write('Clustering using method %s... ' % method)
            cluster_count += self.write_clusters(create_clusters('Column2', method), all_objects)
            
        #Delete Refine project
        refine_project.delete()
        self.stderr.write('\nRefine process successful. %s total clusters created\n\n' % str(cluster_count))
        
    @transaction.commit_on_success
    def write_clusters(self, cluster_list, all_objects):
        new_clusters = 0
        for cluster in filter(lambda x: len(x) < 5, cluster_list):
            topics = []
            for name in cluster:
            
                #Get topic object from name value in refine record
                topic = Topic.objects.filter(preferred_name=name['value'])[0]
                
                if topic not in all_objects:
                    #Clusters are not added to the database if they involve a topic
                    #already present in another cluster (to avoid confusion).
                    #Skipped clusters should be picked up in future passes.
                    topics.append(topic)
                    all_objects.append(topic)
                    unique_cluster_set = True
                else:
                    unique_cluster_set = False
                    break
            
            #Create & save clusters in database
            if unique_cluster_set:
                new_cluster_object = TopicCluster.objects.create()
                for cluster_part in topics:
                    new_cluster_object.clustered_topics.add(cluster_part)
                    new_cluster_object.save()
                new_clusters += 1
        self.stderr.write('%s clusters created.\n' % str(new_clusters))
        return new_clusters
