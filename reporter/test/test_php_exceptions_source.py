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

        # UTF handling
        assert self._source._normalize({'@message': u'ąźć', '@exception': {'class': 'Exception'}}) == 'Production-Exception-ąźć'
        assert self._source._normalize({'@message': 'Foo', '@exception': {'class': 'WikiaException', 'message': u'ąźć'}}) == 'Production-WikiaException-ąźć'
