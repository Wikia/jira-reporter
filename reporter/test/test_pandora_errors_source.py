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

        assert self._source._normalize({
            'rawMessage': 'Read timed out reading GET http://dailylifewithamonstergirl.wikia.com/wiki/Centorea_Shianus?action=raw',
            'logger_name': 'service.foo'
        }) == 'Pandora-Read timed out reading GET <URL>-service.foo'

        assert self._source._normalize({
            'rawMessage': 'Site/Shard map invalid or missing entry for site 831',
            'logger_name': 'service.foo'
        }) == 'Pandora-Site/Shard map invalid or missing entry for site N-service.foo'

        assert self._source._normalize({
            'rawMessage': "Context property 'correlation ID' is missing from the Rabbit message, falling back to 'c2faca50-9106-4b7d-bfd3-5c3fd27e83b9'",
            'logger_name': 'service.foo'
        }) == "Pandora-Context property 'correlation ID' is missing from the Rabbit message, falling back to 'HASH'-service.foo"

    def test_kibana_url(self):
        source = PandoraErrorsSource()

        entry = {
            'appname': 'event-logger',
            'rawMessage': 'ga is not defined'
        }

        assert source._get_kibana_url(entry) == "https://kibana5.wikia-inc.com/app/kibana#/discover?_g=(time:(from:now-6h,mode:quick,to:now))&_a=(columns:!('@timestamp','rawLevel','logger_name','rawMessage','thread_name'),index:'logstash-*',query:(query_string:(analyze_wildcard:!t,query:'appname%3A%20%22event-logger%22%20AND%20rawMessage%3A%20%22ga%20is%20not%20defined%22')),sort:!('@timestamp',desc))"
