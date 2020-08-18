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
               "https://kibana5.wikia-inc.com/app/kibana#/discover?_g=(time:(from:now-6h,mode:quick,to:now))&_a=(columns:!('@timestamp','@source_host','@message'),index:'logstash-other-*',query:(query_string:(analyze_wildcard:!t,query:'foo')),sort:!('@timestamp',desc))"

        assert self._source.format_kibana_url('foo bar') == \
               "https://kibana5.wikia-inc.com/app/kibana#/discover?_g=(time:(from:now-6h,mode:quick,to:now))&_a=(columns:!('@timestamp','@source_host','@message'),index:'logstash-other-*',query:(query_string:(analyze_wildcard:!t,query:'foo%20bar')),sort:!('@timestamp',desc))"

        # TODO
        assert self._source.format_kibana_url('foo', ['@timestamp', 'name']) == \
              "https://kibana5.wikia-inc.com/app/kibana#/discover?_g=(time:(from:now-6h,mode:quick,to:now))&_a=(columns:!('@timestamp','name'),index:'logstash-other-*',query:(query_string:(analyze_wildcard:!t,query:'foo')),sort:!('@timestamp',desc))"

        assert self._source.format_kibana_url(
            query=r'@exception.class: "Wikia\Security\Exception" AND @context.transaction: "foo/bar"'
        ) == "https://kibana5.wikia-inc.com/app/kibana#/discover?_g=(time:(from:now-6h,mode:quick,to:now))&_a=(columns:!('@timestamp','@source_host','@message'),index:'logstash-other-*',query:(query_string:(analyze_wildcard:!t,query:'%40exception.class%3A%20%22Wikia%5C%5CSecurity%5C%5CException%22%20AND%20%40context.transaction%3A%20%22foo/bar%22')),sort:!('@timestamp',desc))"

        assert self._source.format_kibana_url(
            query=r'@exception.class: "Wikia\Util\AssertionException"'
        ) == "https://kibana5.wikia-inc.com/app/kibana#/discover?_g=(time:(from:now-6h,mode:quick,to:now))&_a=(columns:!('@timestamp','@source_host','@message'),index:'logstash-other-*',query:(query_string:(analyze_wildcard:!t,query:'%40exception.class%3A%20%22Wikia%5C%5CUtil%5C%5CAssertionException%22')),sort:!('@timestamp',desc))"

    def test_get_env_from_entry(self):
        # main DC (SJC)
        assert self._source._get_env_from_entry({'@source_host': 'ap-s32'}) is self._source.ENV_MAIN_DC
        assert self._source._get_env_from_entry({'@source_host': 'service-s32'}) is self._source.ENV_MAIN_DC

        # backup DC (Reston)
        assert self._source._get_env_from_entry({'@source_host': 'ap-r32'}) is self._source.ENV_BACKUP_DC
        assert self._source._get_env_from_entry({'@source_host': 'service-r1'}) is self._source.ENV_BACKUP_DC

        # preview / verify
        assert self._source._get_env_from_entry({'@source_host': 'staging-s1'}) is self._source.ENV_PREVIEW
        assert self._source._get_env_from_entry({'@source_host': 'staging-s2'}) is self._source.ENV_MAIN_DC

        # staging
        assert self._source._get_env_from_entry({'@fields': {'environment': 'staging'}}) is self._source.ENV_STAGING
