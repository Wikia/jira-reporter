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

        assert self._source._normalize({
            '@message': 'Request("GET /foo", from /10.14.30.130:48933)',
            'logger_name': 'UnknownRequestPath'
        }) == 'Phalanx-UnknownRequestPath-Request("GET /foo", from /x.x.x.x:x)'

        # strip X-Request-Id from normalized message
        assert self._source._normalize({
            '@message': 'user 3180ms Request("POST /match", from /10.8.76.50:43957) ' +
                        'X-Request-Id: 61e173bc-21a7-479a-b52d-6fbf00c5e75a',
            'logger_name': 'NewRelic'
        }) == 'Phalanx-NewRelic-user Nms Request("POST /match", from /x.x.x.x:x)'

    def test_get_trace_id(self):
        assert self._source._get_trace_id({
            '@message': 'user 3180ms Request("POST /match", from /10.8.76.50:43957) ' +
                        'X-Request-Id: 61e173bc-21a7-479a-b52d-6fbf00c5e75a',
        }) == '61e173bc-21a7-479a-b52d-6fbf00c5e75a'

        assert self._source._get_trace_id({
            '@message': 'user 3180ms Request("POST /match", from /10.8.76.50:43957)',
        }) is None
