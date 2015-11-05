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

        assert self._source.format_kibana_url(
            query='@exception.class: "Wikia\Security\Exception" AND @context.transaction: "foo/bar"'
        ) == 'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=%40exception.class%3A%20%22Wikia%5C%5CSecurity%5C%5CException%22%20AND%20%40context.transaction%3A%20%22foo/bar%22&from=6h&fields=@timestamp,@source_host,message'

        assert self._source.format_kibana_url(
            query='@exception.class: "Wikia\Util\AssertionException"'
        ) == 'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=%40exception.class%3A%20%22Wikia%5C%5CUtil%5C%5CAssertionException%22&from=6h&fields=@timestamp,@source_host,message'
