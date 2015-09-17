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

        assert self._source._normalize({'@message': 'Foo', '@exception': {'class': 'Exception'}}) == 'Production-Exception-Foo'
        assert self._source._normalize({'@message': 'Foo', '@exception': {'class': 'Exception', 'message': 'Bar'}}) == 'Production-Exception-Foo'
        assert self._source._normalize({'@message': 'Foo', '@exception': {'class': 'WikiaException', 'message': 'Bar'}}) == 'Production-WikiaException-Bar'
