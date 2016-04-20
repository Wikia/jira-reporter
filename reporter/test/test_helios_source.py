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
        assert self._source._filter({'@source_host': 'auth-s1'}) is True
        assert self._source._filter({'@source_host': 'auth-r1'}) is True

        # dev - skip for now
        assert self._source._filter({'@source_host': 'dev-auth-s1'}) is False

    def test_normalize(self):
        assert self._source._normalize({
            '@message': 'foo',
        }) == 'Helios-foo'

        assert self._source._normalize({
            '@message': "Error 1062: Duplicate entry '27788246-112328095453510' for key 'user_id'"
        }) == "Helios-Error 1062: Duplicate entry 'X' for key 'X'"
