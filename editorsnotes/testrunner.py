from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

from pyelasticsearch.exceptions import IndexAlreadyExistsError

# custom test changes elasticsearch index name
class CustomTestSuiteRunner(DjangoTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        super(CustomTestSuiteRunner, self).setup_test_environment(**kwargs)

        test_index_name = 'test-' + settings.ELASTICSEARCH_INDEX_NAME

        from editorsnotes.search import en_index
        en_index.name = settings.ELASTICSEARCH_INDEX_NAME = test_index_name

        for doctype in en_index.document_types.values():
            doctype.index_name = test_index_name

        try:
            en_index.create()
        except IndexAlreadyExistsError:
            en_index.delete()
            en_index.create()

    def teardown_test_environment(self, **kwargs):
        super(CustomTestSuiteRunner, self).teardown_test_environment(**kwargs)

        from editorsnotes.search import en_index
        z = en_index.delete()
