"""
Set of unit tests for PHPErrorsSource
"""
import unittest

from ..sources import PandoraErrorsSource


class PandoraErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PandoraErrorsSource class
    """
    def setUp(self):
        self._source = PandoraErrorsSource()

    def test_normalize(self):
        assert self._source._normalize({
            'rawMessage': 'foo',
            'logger_name': 'service.foo'
        }) == 'Pandora-foo-service.foo'

        assert self._source._normalize({
            'rawMessage': 'foo 123',
            'logger_name': 'service.foo'
        }) == 'Pandora-foo N-service.foo'

        assert self._source._normalize({
            'rawMessage': 'Exception purging https://services.wikia.com/user-attribute/user/5430694',
            'logger_name': 'service.foo'
        }) == 'Pandora-Exception purging <URL>-service.foo'

        assert self._source._normalize({
            'rawMessage': 'Exception purging http://example.com',
            'logger_name': 'service.foo'
        }) == 'Pandora-Exception purging <URL>-service.foo'

        assert self._source._normalize({
            'rawMessage': 'error while sending: {"args":{"prevRevision":false,"revision":66213},"is_main_page":false}',
            'logger_name': 'service.foo'
        }) == 'Pandora-error while sending: {json here}-service.foo'

        assert self._source._normalize({
            'rawMessage': 'too much data after closed for HttpChannelOverHttp@276b8295{r=1,c=false,a=IDLE,uri=-}',
            'logger_name': 'service.foo'
        }) == 'Pandora-too much data after closed for HttpChannelOverHttp@HASH{json here}-service.foo'
