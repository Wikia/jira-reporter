"""
Set of unit tests for PHPErrorsSource
"""
import unittest

from reporter.sources import DBQueryErrorsSource, PHPErrorsSource


class PHPErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPErrorsSource class
    """
    def setUp(self):
        self._source = PHPErrorsSource(period=3600)
        self._source._query = 'PHP Fatal Error'

    def test_filter(self):
        assert self._source._filter({'@message': 'PHP Fatal Error: bar on line 22', '@source_host': self._source.PREVIEW_HOST}) is True
        assert self._source._filter({'@message': 'PHP Fatal Error: bar on line 22', '@source_host': 'ap-s32'}) is True
        assert self._source._filter({'@message': 'PHP Fatal Error: bar on line 22', '@source_host': 'ap-r32'}) is False  # reston DC
        assert self._source._filter({}) is False  # empty message

    def test_normalize(self):
        # normalize file path
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /usr/wikia/slot1/2996/src/includes/Linker.php on line 184'
        }) == 'PHP-PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /includes/Linker.php on line 184-Production'

        # remove URLs
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Missing or invalid pubid from http://dragonball.wikia.com/__varnish_liftium/config in /var/www/liftium/delivery/config.php on line 17'
        }) == 'PHP-PHP Fatal Error: Missing or invalid pubid from <URL> in /var/www/liftium/delivery/config.php on line 17-Production'

        # normalize "Tag figure invalid in Entity, line: 286" part
        assert self._source._normalize({
            '@message': 'PHP Warning: DOMDocument::loadHTML(): Tag figure invalid in Entity, line: 286 in /includes/wikia/InfoboxExtractor.class.php on line 53'
        }) == 'PHP-PHP Warning: DOMDocument::loadHTML(): Tag X invalid in Entity, line: N in /includes/wikia/InfoboxExtractor.class.php on line 53-Production'

        # normalize popen() logs
        assert self._source._normalize({
            '@message': "PHP Warning: popen(/usr/bin/diff -u '/tmp/merge-old-8JOqT1' '/tmp/merge-your-BGuKlc',r): Cannot allocate memory in /includes/GlobalFunctions.php on line 3134"
        }) == "PHP-PHP Warning: popen(X): Cannot allocate memory in /includes/GlobalFunctions.php on line 3134-Production"

        # normalize failed forks
        assert self._source._normalize({
            '@message': "PHP Warning: exec(): Unable to fork [/var/lib/gems/1.8/bin/sass /extensions/wikia/WikiaMobile/css/404.scss /tmp/X --scss -t nested -I   --cache-location /tmp/X -r /extensions/wikia/SASS/wikia_sass.rb background-dynamic=1 background-image=/skins/oasis/images/themes/carbon.png background-image-height=800 background-image-width=2000 color-body=\#1a1a1a color-body-middle=\#1a1a1a color-buttons=\#012e59 color-header=\#012e59 color-links=\#b0e0e6 color-page=\#474646 page-opacity=100 widthType=2 2&gt;&amp;1] in /includes/wikia/services/sass/Compiler/ExternalRubyCompiler.class.php on line 55"
        }) == "PHP-PHP Warning: exec(): Unable to fork [X] in /includes/wikia/services/sass/Compiler/ExternalRubyCompiler.class.php on line 55-Production"

        # normalize /tmp/AMInu3uOpA paths
        assert self._source._normalize({
            '@message': "PHP Warning: shell_exec(): Unable to execute 'cat /tmp/AMInu3uOpA | /lib/vendor/jsmin' in /extensions/wikia/AssetsManager/builders/AssetsManagerBaseBuilder.class.php on line 110"
        }) == "PHP-PHP Warning: shell_exec(): Unable to execute 'cat /tmp/X | /lib/vendor/jsmin' in /extensions/wikia/AssetsManager/builders/AssetsManagerBaseBuilder.class.php on line 110-Production"

        # error from preview
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /usr/wikia/slot1/2996/src/includes/Linker.php on line 184',
            '@source_host': 'staging-s3'
        }) == 'PHP-PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /includes/Linker.php on line 184-Preview'

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
        assert report.get_summary() == 'PHP Fatal Error:  Call to a member function getText() on a non-object in /includes/wikia/services/ArticleService.class.php on line 187'

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


class DBErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPErrorsSource class
    """
    def setUp(self):
        self._source = DBQueryErrorsSource()

    def test_generalize_sql(self):
        assert DBQueryErrorsSource._generalize_sql("UPDATE  `category` SET cat_pages = cat_pages + 1,cat_files = cat_files + 1 WHERE cat_title = 'foo'") ==\
            "UPDATE `category` SET cat_pages = cat_pages + N,cat_files = cat_files + N WHERE cat_title = X"

        assert DBQueryErrorsSource._generalize_sql("SELECT  entity_key  FROM `wall_notification_queue`  WHERE (wiki_id = ) AND (event_date > '20150105141012')") ==\
            "SELECT entity_key FROM `wall_notification_queue` WHERE (wiki_id = ) AND (event_date > X)"

        assert DBQueryErrorsSource._generalize_sql("UPDATE  `user` SET user_touched = '20150112143631' WHERE user_id = '25239755'") ==\
            "UPDATE `user` SET user_touched = X"

        # multiline query
        sql = """
SELECT page_title
    FROM page
    WHERE page_namespace = '10'
    AND page_title COLLATE LATIN1_GENERAL_CI LIKE '%{{Cata%'
        """

        assert DBQueryErrorsSource._generalize_sql(sql) ==\
            "SELECT page_title FROM page WHERE page_namespace = X AND page_title COLLATE LATINN_GENERAL_CI LIKE X"

    def test_get_context_from_entry(self):
        context = DBQueryErrorsSource._get_context_from_entry({
            "@exception": {
                "message": "A database error has occurred.  Did you forget to run maintenance/update.php after upgrading?  See: https://www.mediawiki.org/wiki/Manual:Upgrading#Run_the_update_script\nQuery: SELECT  DISTINCT `page`.page_namespace AS page_namespace,`page`.page_title AS page_title,`page`.page_id AS page_id, `page`.page_title  as sortkey FROM `page` WHERE 1=1  AND `page`.page_namespace IN ('6') AND `page`.page_is_redirect=0 AND 'Hal Homsar Solo' = (SELECT rev_user_text FROM `revision` WHERE `revision`.rev_page=page_id ORDER BY `revision`.rev_timestamp ASC LIMIT 1) ORDER BY page_title ASC LIMIT 0, 500\nFunction: DPLMain:dynamicPageList\nError: 1317 Query execution was interrupted (10.8.38.37)\n"
            },
            "@context": {
                "errno": 1317,
                "err": "Query execution was interrupted (10.8.38.37)"
            },
        })

        assert context.get('function') == 'DPLMain:dynamicPageList'
        assert context.get('query') == "SELECT  DISTINCT `page`.page_namespace AS page_namespace,`page`.page_title AS page_title,`page`.page_id AS page_id, `page`.page_title  as sortkey FROM `page` WHERE 1=1  AND `page`.page_namespace IN ('6') AND `page`.page_is_redirect=0 AND 'Hal Homsar Solo' = (SELECT rev_user_text FROM `revision` WHERE `revision`.rev_page=page_id ORDER BY `revision`.rev_timestamp ASC LIMIT 1) ORDER BY page_title ASC LIMIT 0, 500"
        assert context.get('error') == '1317 Query execution was interrupted (10.8.38.37)'

        assert DBQueryErrorsSource._get_context_from_entry({}) is None

    def test_filter(self):
        assert self._source._filter({'@source_host': self._source.PREVIEW_HOST}) is True
        assert self._source._filter({'@source_host': 'ap-s32'}) is True
        assert self._source._filter({'@source_host': 'ap-r32'}) is False  # reston DC
        assert self._source._filter({}) is False  # empty message
