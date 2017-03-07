# -*- coding: utf-8 -*-
"""
Set of unit tests for PHPExceptionsSource
"""
import unittest

from ..sources import PHPExceptionsSource


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
        assert self._source._filter({'@message': 'Foo', '@source_host': 'ap-s10'}) is True

        # PHP Fatal errors with the exception backtrace should be ignored
        assert self._source._filter({'@message': 'PHP Fatal error: Maximum execution', "@exception": {"class": "Exception"}, '@source_host': 'ap-s10'}) is False
