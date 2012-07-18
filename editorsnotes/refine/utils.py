from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import transaction
from django.db.models import get_models, Model
from editorsnotes.main.models import Topic, Alias
from lxml import etree
import re

def get_preferred_topic_name(topics):
    """
    Returns a tuple of (Preferred name, [rest of names])
    """
    topics = sorted(topics, key=lambda t: t.created)
    PREFERRED_NAME_FMT = re.compile('.*?\d{4}-(?:\d{4})?.?$')

    preferred_name = ''
    rest_of_names = [t.preferred_name for t in topics]

    for topic in topics:
        if not preferred_name and re.match(
            PREFERRED_NAME_FMT, topic.preferred_name):
            preferred_name = topic.preferred_name
    if not preferred_name:
        preferred_name = topics[0].preferred_name
    rest_of_names.remove(preferred_name)

    return preferred_name, rest_of_names

def get_combined_article(topics):
    """
    Returns combined topic articles, separated by <hr />
    """
    article = ''
    combined = False
    for topic in topics:
        if topic.has_summary():
            article += '<hr />' if article else ''
            combined = True if article else False
            article += etree.tostring(topic.summary)

    # If multiple articles were combined, to be valid xhtml they must have a
    # single root node
    article = '<div>%s</div>' % article if combined else article

    return etree.fromstring(article) if article else None

@transaction.commit_on_success
def merge_topics(topics, user):
    """
    Given a list of topics, blah
    """
    if len(topics) < 2:
        return

    topics = sorted(topics, key=lambda t: t.created)

    # Topic with the oldest creation date will be the one merged into
    merged_topic = topics[0]

    # Get preferred & alternate names for the new topic, to be saved later.
    preferred_name, alternate_names = get_preferred_topic_name(topics)

    # New topic article & article citations
    combined_article = get_combined_article(topics)
    merged_topic.summary = etree.tostring(
        combined_article) if combined_article else None

    # Changed references for topic assignments
    for topic in topics:
        for ta in topic.assignments.all():
            ta.topic = merged_topic
            ta.save()
        for alias in topic.aliases.all():
            alias.topic = merged_topic
            alias.save()

    # Delete all old topics
    topics.remove(merged_topic)
    for topic_to_remove in topics:
        topic_to_remove.delete()

    for new_alias in alternate_names:
        Alias.objects.create(topic=merged_topic, name=new_alias, creator=user)

    # Give the merged topic a new slug & save
    merged_topic.preferred_name = preferred_name
    merged_topic.slug = Topic.make_slug(topic.preferred_name)
    merged_topic.save()

    return merged_topic
