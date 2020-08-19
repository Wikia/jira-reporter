# -*- coding: utf-8 -*-
"""
Set of unit tests for PHPExceptionsSource
"""
import unittest

from ..sources import PHPExceptionsSource, PHPTypeErrorsSource


class PHPExceptionsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPExceptionsSource class
    """
    def setUp(self):
        self._source = PHPExceptionsSource()

    def test_normalize(self):
        assert self._source._normalize({'@message': 'Foo'}) == 'Production-None-Foo'
        assert self._source._normalize({'@message': 'Server #3 (10.8.38.41) is excessively lagged (126 seconds)'}) == 'Production-None-Server #X (10.8.38.41) is excessively lagged (X seconds)'
        assert self._source._normalize({'@message': 'Template file not found: /usr/wikia/slot1/6969/src/extensions/wikia/Rail/templates/RailController_LazyForAnons.php'}) == 'Production-None-Template file not found: /extensions/wikia/Rail/templates/RailController_LazyForAnons.php'
        assert self._source._normalize({'@message': 'ExternalStoreDB::fetchBlob master fallback on blobs20141/106563095'}) == 'Production-None-ExternalStoreDB::fetchBlob master fallback on blobsX'

        assert self._source._normalize({'@message': 'Foo', '@exception': {'class': 'Exception'}}) == 'Production-Exception-Foo'
        assert self._source._normalize({'@message': 'Foo', '@exception': {'class': 'Exception', 'message': 'Bar'}}) == 'Production-Exception-Foo'
        assert self._source._normalize({'@message': 'Foo', '@exception': {'class': 'WikiaException', 'message': 'Bar'}}) == 'Production-WikiaException-Bar'
        assert self._source._normalize({
            '@message': 'Foo',
            '@exception': {'class': 'WikiaException', 'message': 'Template file not found: /usr/wikia/slot1/6969/src/extensions/wikia/Rail/templates/RailController_LazyForAnons.php'}
        }) == 'Production-WikiaException-Template file not found: /extensions/wikia/Rail/templates/RailController_LazyForAnons.php'

        assert self._source._normalize({
            '@message': 'WikiaDispatcher::dispatch - Exception - MWException - WikiaDataAccess could not obtain lock to generate data for: wikicities:datamart:toparticles:4:1241752:200:cfcd208495d565ef66e7dff9f98764da::current',
            '@exception': {'class': 'MWException', 'message': 'WikiaDataAccess could not obtain lock to generate data for: wikicities:datamart:toparticles:4:1241752:200:cfcd208495d565ef66e7dff9f98764da::current'}
        }) == 'Production-MWException-WikiaDispatcher::dispatch - Exception - MWException - WikiaDataAccess could not obtain lock to generate data for: XXX'

        # SUS-1768: MediaWiki handled Error exceptions
        assert self._source._normalize({
            '@message': 'MWExceptionHandler::report',
            '@exception': {'class': 'Error', 'message': 'Call to a member function getRevisionFetched() on boolean'}
        }) == 'Production-Error-Call to a member function getRevisionFetched() on boolean'

        # UTF handling
        assert self._source._normalize({'@message': u'ąźć', '@exception': {'class': 'Exception'}}) == 'Production-Exception-ąźć'
        assert self._source._normalize({'@message': 'Foo', '@exception': {'class': 'WikiaException', 'message': u'ąźć'}}) == 'Production-WikiaException-ąźć'

    def test_filter(self):
        assert self._source._filter({'@message': 'Foo', '@fields': {'environment': 'prod'}}) is True

        # PHP Fatal errors with the exception backtrace should be ignored
        assert self._source._filter({'@message': 'PHP Fatal error: Maximum execution', "@exception": {"class": "Exception"}, '@fields': {'environment': 'prod'}}) is False

        assert self._source._filter({'@message': 'MWExceptionHandler::report', "@exception": {"class": "BadTitleError"}, '@fields': {'environment': 'prod'}}) is False
        assert self._source._filter({'@message': 'MWExceptionHandler::report', "@exception": {"class": "PermissionsError"}, '@fields': {'environment': 'prod'}}) is False


class PHPTypeErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPTypeErrorsSource class
    """
    def setUp(self):
        self._source = PHPTypeErrorsSource()

        self.message = 'Argument 1 passed to DesignSystemCommunityHeaderModel::formatLocalNavData() must be ' \
            'of the type array, null given, called in /usr/wikia/slot1/23746/src/includes/wikia/' \
            'models/DesignSystemCommunityHeaderModel.class.php on line 140'

        self.entry = {
            '@exception': {
                'error': 'TypeError',
                'message': self.message,
            },
            '@source_host': 'cron-s1',
        }

    def test_report(self):
        report = self._source._get_report(self.entry)

        assert self.message in report.get_description()

        assert self._source._normalize(self.entry) == 'Production-None-Argument 1 passed to ' \
            'DesignSystemCommunityHeaderModel::formatLocalNavData() ' \
            'must be of the type array, null given, called in ' \
            '/includes/wikia/models/DesignSystemCommunityHeaderModel.class.php on line 140'

        assert report.get_summary() == 'Argument 1 passed to DesignSystemCommunityHeaderModel::formatLocalNavData() ' \
                                       'must be of the type array, null given'
