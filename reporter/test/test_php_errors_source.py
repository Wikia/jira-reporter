"""
Set of unit tests for PHPErrorsSource
"""
import unittest

from reporter.sources import PHPErrorsSource


class PHPErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPErrorsSource class
    """
    def setUp(self):
        self._source = PHPErrorsSource(period=3600)
        self._source._query = 'PHP Fatal Error'

    def test_filter(self):
        # message needs to to begin with "foo" (our current query)
        assert self._source._filter({'@message': 'PHP Fatal Error: bar on line 22', '@source_host': self._source.PREVIEW_HOST}) is True
        assert self._source._filter({'@message': 'PHP Fatal Error: bar on line 22', '@source_host': 'ap-s32'}) is True
        assert self._source._filter({'@message': 'PHP Fatal Error: bar on line 22', '@source_host': 'ap-r32'}) is False  # reston DC
        assert self._source._filter({'@message': 'bar on line 22', '@source_host': self._source.PREVIEW_HOST}) is False  # no prefix
        assert self._source._filter({}) is False  # empty message

    def test_normalize(self):
        # normalize file path
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /usr/wikia/slot1/2996/src/includes/Linker.php on line 184'
        }) == 'PHP-PHP Fatal Error-Maximum execution time of 180 seconds exceeded in /includes/Linker.php on line 184-Production'

        # remove URLs
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Missing or invalid pubid from http://dragonball.wikia.com/__varnish_liftium/config in /var/www/liftium/delivery/config.php on line 17'
        }) == 'PHP-PHP Fatal Error-Missing or invalid pubid from <URL> in /var/www/liftium/delivery/config.php on line 17-Production'

        # error from preview
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /usr/wikia/slot1/2996/src/includes/Linker.php on line 184',
            '@source_host': 'staging-s3'
        }) == 'PHP-PHP Fatal Error-Maximum execution time of 180 seconds exceeded in /includes/Linker.php on line 184-Preview'

    def test_get_report(self):
        entry = {
            "@timestamp": "2015-01-08T09:23:00.091+00:00",
            "syslog_pid": "24705",
            "@message": "PHP Fatal Error:  Call to a member function getText() on a non-object in /usr/wikia/slot1/3006/src/includes/wikia/services/ArticleService.class.php on line 187",
            "tags": [
                "message"
            ],
            "@source_host": "ap-s10",
            "severity": "notice",
            "facility": "user-level",
            "priority": "13",
            "program": "apache2",
            "@context": {},
            "@fields": {
                "city_id": "475988",
                "ip": "10.8.66.62",
                "server": "zh.asoiaf.wikia.com",
                "url": "/wikia.php?controller=GameGuides&method=renderpage&page=%E5%A5%94%E6%B5%81%E5%9F%8E",
                "db_name": "zhasoiaf",
                "http_method": "GET",
                "request_id": "mw54af96dd0b63e1.13192431"
            }
        }

        self._source._normalize(entry)

        report = self._source._get_report(entry)
        print report.get_description()  # print out to stdout, pytest will show it in case of a failure

        # report should be sent with a normalized summary set
        assert report.get_summary() == 'PHP Fatal Error: Call to a member function getText() on a non-object in /includes/wikia/services/ArticleService.class.php on line 187'

        # the full message should be kept in the description
        assert entry.get('@message') in report.get_description()

        # URL should be extracted
        assert 'URL: http://zh.asoiaf.wikia.com/wikia.php?controller=GameGuides&method=renderpage&page=%E5%A5%94%E6%B5%81%E5%9F%8E' in report.get_description()
        assert 'Env: Production' in report.get_description()

        # a proper label should be set
        assert report.get_label() == 'PHPErrors'

    def test_get_url_from_entry(self):
        entry = {
            "@fields": {
                "server": "zh.asoiaf.wikia.com",
                "url": "/wikia.php?controller=Foo&method=bar",
            }
        }

        assert self._source._get_url_from_entry(entry) == 'http://zh.asoiaf.wikia.com/wikia.php?controller=Foo&method=bar'
        assert self._source._get_url_from_entry({}) is False

    def test_get_env_from_entry(self):
        assert self._source._get_env_from_entry({'@source_host': 'ap-s32'}) is self._source.ENV_PRODUCTION
        assert self._source._get_env_from_entry({'@source_host': 'ap-r32'}) is self._source.ENV_PRODUCTION
        assert self._source._get_env_from_entry({'@source_host': 'service-s32'}) is self._source.ENV_PRODUCTION

        # preview / verify
        assert self._source._get_env_from_entry({'@source_host': 'staging-s3'}) is self._source.ENV_PREVIEW
        assert self._source._get_env_from_entry({'@source_host': 'staging-s4'}) is self._source.ENV_PRODUCTION
