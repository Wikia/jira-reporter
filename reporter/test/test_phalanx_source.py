"""
Set of unit tests for PHPErrorsSource
"""
import unittest

from ..sources import PhalanxSource


class PhalanxSourceTestClass(unittest.TestCase):
    """
    Unit tests for PandoraErrorsSource class
    """
    def setUp(self):
        self._source = PhalanxSource()

    def test_normalize(self):
        assert self._source._normalize({
            '@message': 'foo',
            'logger_name': 'logger'
        }) == 'Phalanx-logger-foo'

        assert self._source._normalize({
            '@message': 'Could not notify node phalanx-r4: com.twitter.util.TimeoutException: 10.seconds',
            'logger_name': 'sendNotify'
        }) == 'Phalanx-sendNotify-Could not notify node phalanx-*: com.twitter.util.TimeoutException: 10.seconds'
