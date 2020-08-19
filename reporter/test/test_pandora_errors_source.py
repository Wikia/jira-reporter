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
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == 'Pandora-foo-lib.foo-Service'

        assert self._source._normalize({
            'rawMessage': 'foo 123',
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == 'Pandora-foo N-lib.foo-Service'

        assert self._source._normalize({
            'rawMessage': 'Exception purging https://services.wikia.com/user-attribute/user/5430694',
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == 'Pandora-Exception purging <URL>-lib.foo-Service'

        assert self._source._normalize({
            'rawMessage': 'Exception purging http://example.com',
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == 'Pandora-Exception purging <URL>-lib.foo-Service'

        assert self._source._normalize({
            'rawMessage': 'error while sending: {"args":{"prevRevision":false,"revision":66213},"is_main_page":false}',
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == 'Pandora-error while sending: {json here}-lib.foo-Service'

        assert self._source._normalize({
            'rawMessage': 'too much data after closed for HttpChannelOverHttp@276b8295{r=1,c=false,a=IDLE,uri=-}',
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == 'Pandora-too much data after closed for HttpChannelOverHttp@HASH{json here}-lib.foo-Service'

        assert self._source._normalize({
            'rawMessage': 'Read timed out reading GET http://dailylifewithamonstergirl.wikia.com/wiki/Centorea_Shianus?action=raw',
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == 'Pandora-Read timed out reading GET <URL>-lib.foo-Service'

        assert self._source._normalize({
            'rawMessage': 'Site/Shard map invalid or missing entry for site 831',
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == 'Pandora-Site/Shard map invalid or missing entry for site N-lib.foo-Service'

        assert self._source._normalize({
            'rawMessage': "Context property 'correlation ID' is missing from the Rabbit message, falling back to 'c2faca50-9106-4b7d-bfd3-5c3fd27e83b9'",
            'logger_name': 'lib.foo',
            'appname': 'Service'
        }) == "Pandora-Context property 'correlation ID' is missing from the Rabbit message, falling back to 'HASH'-lib.foo-Service"

    def test_kibana_url(self):
        source = PandoraErrorsSource()

        entry = {
            'appname': 'event-logger',
            'rawMessage': 'ga is not defined'
        }

        assert source._get_kibana_url(entry) == "https://kibana.wikia-inc.com/app/kibana#/discover?_g=(time:(from:now-6h,mode:quick,to:now))&_a=(columns:!('@timestamp','rawLevel','logger_name','rawMessage','thread_name'),index:'logstash-*',query:(query_string:(analyze_wildcard:!t,query:'appname%3A%20%22event-logger%22%20AND%20rawMessage%3A%20%22ga%20is%20not%20defined%22')),sort:!('@timestamp',desc))"
