# -*- coding: utf-8 -*-
"""
Set of unit tests for DBQueryErrorsSource
"""
import unittest

from ..sources.php.db import DBQueryErrorsSource


class DBQueryErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for DBQueryErrorsSource
    """
    def test_filter(self):
        source = DBQueryErrorsSource()

        # filter by source host
        assert source._filter({'@fields': {'environment': 'prod'}}) is True

        # filter by MySQL error codes
        assert source._filter({'@fields': {'environment': 'prod'}, '@context': {'errno': 1200}}) is True
        assert source._filter({'@fields': {'environment': 'prod'}, '@context': {'errno': 1205}}) is False
        assert source._filter({'@fields': {'environment': 'prod'}, '@context': {'errno': 1213}}) is False

        # filter out "Query execution was interrupted" errors coming from SMW and DPL
        cases = (
            ('FooClass::getBar', 1317, True),
            ('FooClass::SMW', 1317, True),
            ('DPLMain:dynamicPageList', 1317, False),  # ER-5948
            ('SMWSQLStore2::getSMWPageIDandSort', 1317, False),  # ER-5360
            ('SMW::getQueryResult', 1317, False),  # ER-7901
            ('SMW::getQueryResult', 2013, False),  # ER-7901
            ('SMW::getQueryResult', 42, True),
        )

        for (function, err_no, expected) in cases:
            self._check_is_filtered_out(function, err_no, expected)

    @staticmethod
    def _check_is_filtered_out(function, err_no, expected):
        assert DBQueryErrorsSource()._filter({
            '@fields': {'environment': 'prod'},
            '@context': {'errno': err_no},
            '@exception': {'message': 'Foo\nQuery: SELECT foo FROM bar\nFunction: {}'.format(function)}
        }) is expected

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
        print(context)

        assert context.get('error') == '42 Foo'
        assert context.get('function') == 'DPLMain:dynamicPageList'
        assert context.get('query') == 'SELECT foo FROM bar'

    def test_kibana_url(self):
        source = DBQueryErrorsSource()

        entry = {
            '@context': {
                'function': 'DWDimensionApiController::getWikiImagesData'
            }
        }

        assert source._get_kibana_url(entry) == "https://kibana5.wikia-inc.com/app/kibana#/discover?_g=(time:(from:now-6h,mode:quick,to:now))&_a=(columns:!('@timestamp','@source_host','@context.errno','@context.err','@fields.db_name','@fields.http_url'),index:'logstash-mediawiki-*',query:(query_string:(analyze_wildcard:!t,query:'%40exception.class%3A%20%22DBQueryError%22%20AND%20%40exception.message%3A%20%22DWDimensionApiController%3A%3AgetWikiImagesData%22')),sort:!('@timestamp',desc))"

    def test_normalize(self):
        source = DBQueryErrorsSource()

        assert source._normalize({}) is None

        assert source._normalize({
            '@exception': {'message': 'Foo\nQuery: SELECT foo FROM bar\nFunction: FooClass::getBar'},
            '@context': {'errno': 42}
        }) == 'SELECT foo FROM bar-42'

        assert source._normalize({
            '@exception': {'message': u'Foo\nQuery: SELECT foo FROM bar WHERE ąść\nFunction: FooClass::getBar'},
            '@context': {'errno': 42}
        }) == 'SELECT foo FROM bar WHERE ąść-42'

        # SQL syntax errors (error #1064) are normalized a bit differently - PLATFORM-1512
        assert source._normalize({
            '@exception': {'message': 'Foo\nQuery: SELECT foo FROM bar\nFunction: FooClass::getBar'},
            '@context': {'errno': 1064}  # SQL syntax error code
        }) == 'FooClass::getBar-1064'

        # properly encode UTF characters and prevent UnicodeEncodeError
        assert source._normalize({
            '@exception': {'message': 'Foo\nQuery: SELECT foo FROM bar\nFunction: FooClass::getBar'},
            '@context': {'errno': 1064, 'err': u'ąęź'}  # SQL syntax error code
        }) == 'FooClass::getBar-1064'
