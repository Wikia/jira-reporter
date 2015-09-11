"""
Set of unit tests for KibanaSource
"""
import unittest

from ..sources.common import KibanaSource


class KibanaSourceTestClass(unittest.TestCase):
    """
    Unit tests for KibanaSource class
    """
    def setUp(self):
        self._source = KibanaSource()

    def test_format_kibana_url(self):
        # comma should be ignored - otherwise Kibana will create subqueries
        assert self._source.format_kibana_url('foo,bar') == self._source.format_kibana_url('foo bar')

        assert self._source.format_kibana_url('foo') == \
               'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=foo&from=6h&fields=@timestamp,@source_host,message'

        assert self._source.format_kibana_url('foo bar') == \
               'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=foo%20bar&from=6h&fields=@timestamp,@source_host,message'

        assert self._source.format_kibana_url('foo', ['@timestamp', 'name']) == \
               'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=foo&from=6h&fields=@timestamp,name'
