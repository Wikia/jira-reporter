"""
Set of unit tests for PHPAssertionsSource
"""
import unittest

from ..sources import PHPAssertionsSource


class PHPAssertionsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPAssertionsSource class
    """
    def setUp(self):
        self._source = PHPAssertionsSource()

    def test_normalize(self):
        assert self._source._normalize({
            '@exception': {'message': 'API call to /5275700 timed out: a:26:{s:3:"url";s:8:"/5275700";s:12:"content_type";N;s:9:"http_code";i:0;s:11:"header_size";i:0;s:12:"request_size";i:0;s:8:"filetime";i:-1;s:17:"ssl_verify_result";i:0;s:14:"redirect_count";i:0;s:10:"total_time";d:0;s:15:"namelookup_time";d:0;s:12:"connect_time";d:0;s:16:"pretransfer_time";d:0;s:11:"size_upload";d:0;s:13:"size_download";d:0;s:14:"speed_download";d:0;s:12:"speed_upload";d:0;s:23:"download_content_length";d:-1;s:21:"upload_content_length";d:-1;s:18:"starttransfer_time";d:0;s:13:"redirect_time";d:0;s:12:"redirect_url";s:0:"";s:10:"primary_ip";s:0:"";s:8:"certinfo";a:0:{}s:12:"primary_port";i:0;s:8:"local_ip";s:0:"";s:10:"local_port";i:0;}'}
        }) == 'None-API call to /X timed out'

        assert self._source._normalize({
            '@exception': {'message': '{"title":"Attribute UserProfilePagesV3_birthday not found for user 26816594","status":404}'}
        }) == 'None-{"title":"Attribute X not found for user N","status":404}'
