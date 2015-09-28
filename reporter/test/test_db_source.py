"""
Set of unit tests for DBQueryErrorsSource
"""
import unittest

from ..sources.php.db import DBQueryErrorsSource


class DBQueryErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPLogsSource DBQueryErrorsSource
    """
    def test_filter(self):
        source = DBQueryErrorsSource()

        # filter by source host
        assert source._filter({'@source_host': 'ap-s20'}) is True
        assert source._filter({'@source_host': 'dev-foo'}) is False

        # filter by MySQL error codes
        assert source._filter({'@source_host': 'ap-s20', '@context': {'errno': 1200}}) is True
        assert source._filter({'@source_host': 'ap-s20', '@context': {'errno': 1205}}) is False
        assert source._filter({'@source_host': 'ap-s20', '@context': {'errno': 1213}}) is False

    def test_get_context_from_entry(self):
        entry = {
            '@exception': {
                'message': 'A database error has occurred.  Did you forget to run maintenance/update.php after upgrading?  See: https://www.mediawiki.org/wiki/Manual:Upgrading#Run_the_update_script\n' +
                    "Query: SELECT foo FROM bar\n" +
                    "Function: DPLMain:dynamicPageList\n" +
                    "Error: 1317 Query execution was interrupted (10.8.38.37)"
            },
            '@context': {
                'errno': 42,
                'err': 'Foo'
            }
        }

        context = DBQueryErrorsSource._get_context_from_entry(entry)
        print context

        assert context.get('error') == '42 Foo'
        assert context.get('function') == 'DPLMain:dynamicPageList'
        assert context.get('query') == 'SELECT foo FROM bar'

    def test_normalize(self):
        source = DBQueryErrorsSource()
        exception = {
            'message': 'Foo\nQuery: SELECT foo FROM bar'
        }

        assert source._normalize({}) is None

        assert source._normalize({'@exception': exception, '@context': {'errno': 42, 'err': 'Err'}}) == 'SELECT foo FROM bar-42'
