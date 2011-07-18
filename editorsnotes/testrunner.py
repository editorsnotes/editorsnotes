from django.test import TestCase
from django.test.simple import DjangoTestSuiteRunner

# custom test runner only sets up test DB if necessary.
class CustomTestSuiteRunner(DjangoTestSuiteRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        self.setup_test_environment()
        suite = self.build_suite(test_labels, extra_tests)
        need_database = False
        for test in suite:
            if isinstance(test, TestCase):
                need_database = True
                break
        if need_database:
            old_config = self.setup_databases()
        result = self.run_suite(suite)
        if need_database:
            self.teardown_databases(old_config)
        self.teardown_test_environment()
        return self.suite_result(suite, result)

    
