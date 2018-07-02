"""
Set of unit tests for PHPErrorsSource
"""
import unittest

from ..sources import HeliosSource


class HeliosSourceTestClass(unittest.TestCase):
    """
    Unit tests for PandoraErrorsSource class
    """
    def setUp(self):
        self._source = HeliosSource()

    def test_filter(self):
        # prod
        assert self._source._filter({'kubernetes': {'namespace_name': 'prod'}}) is True
        assert self._source._filter({'kubernetes': {'namespace_name': 'dev'}}) is False

    def test_normalize(self):
        assert self._source._normalize({
            '@message': 'foo',
        }) == 'Helios-foo'
