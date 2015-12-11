# -*- coding: utf-8 -*-
"""
Set of unit tests for PHPErrorsSource
"""
import unittest

from ..sources import DBQueryErrorsSource, PHPErrorsSource


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
        assert self._source._filter({'@message': 'PHP Fatal Error: bar', '@source_host': 'ap-s32'}) is False  # no context
        assert self._source._filter({'@message': 'PHP Fatal Error: bar on line 22', '@source_host': 'ap-r32'}) is True  # we do serve production traffic from Reston
        assert self._source._filter({}) is False  # empty message

        assert self._source._filter({'@message': 'PHP Fatal Error: Allowed memory size of 536870912 bytes exhausted on line 42', '@source_host': 'ap-s32'}) is False  # do not report OOM errors

    def test_normalize(self):
        # normalize file path
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /usr/wikia/slot1/2996/src/includes/Linker.php on line 184'
        }) == 'PHP-PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /includes/Linker.php on line 184-Production'

        assert self._source._normalize({
            '@message': 'PHP Warning: strlen() expects parameter 1 to be string, array given in /usr/wikia/slot1/8325/foo/Bar.class.php on line 32'
        }) == 'PHP-PHP Warning: strlen() expects parameter 1 to be string, array given in /foo/Bar.class.php on line 32-Production'

        assert self._source._normalize({
            '@message': 'PHP Warning: include(/data/deploytools/build/wikia.foo/src/extensions/wikia/ArticleNavigation/ArticleNavigation.i18n.php): failed to open stream: No such file or directory in /data/deploytools/build/wikia.foo/src/includes/LocalisationCache.php on line 461'
        }) == 'PHP-PHP Warning: include(/extensions/wikia/ArticleNavigation/ArticleNavigation.i18n.php): failed to open stream: No such file or directory in /includes/LocalisationCache.php on line 461-Production'

        # remove URLs
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Missing or invalid pubid from http://dragonball.wikia.com/__varnish_liftium/config in /var/www/liftium/delivery/config.php on line 17'
        }) == 'PHP-PHP Fatal Error: Missing or invalid pubid from <URL> in /var/www/liftium/delivery/config.php on line 17-Production'

        # normalize "Tag figure invalid in Entity, line: 286" part
        assert self._source._normalize({
            '@message': 'PHP Warning: DOMDocument::loadHTML(): Tag figure invalid in Entity, line: 286 in /includes/wikia/InfoboxExtractor.class.php on line 53'
        }) == 'PHP-PHP Warning: DOMDocument::loadHTML(): X, line: N in /includes/wikia/InfoboxExtractor.class.php on line 53-Production'

        assert self._source._normalize({
            '@message': 'PHP Warning: DOMDocument::loadHTML(): Unexpected end tag : p in Entity, line: 82 in /usr/wikia/slot1/8696/src/includes/wikia/parser/templatetypes/handlers/DataTables.class.php on line 81'
        }) == 'PHP-PHP Warning: DOMDocument::loadHTML(): X, line: N in /includes/wikia/parser/templatetypes/handlers/DataTables.class.php on line 81-Production'

        assert self._source._normalize({
            '@message': 'PHP Warning: DOMDocument::loadHTML(): Opening and ending tag mismatch: td and tr in Entity, line: 46 in /includes/wikia/parser/templatetypes/handlers/DataTables.class.php on line 81'
        }) == 'PHP-PHP Warning: DOMDocument::loadHTML(): X, line: N in /includes/wikia/parser/templatetypes/handlers/DataTables.class.php on line 81-Production'

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

        # OOM, remove "n bytes"
        assert self._source._normalize({
            '@message': 'PHP Fatal error: Allowed memory size of 536870912 bytes exhausted (tried to allocate 17956864 bytes) in /usr/wikia/slot1/3853/src/skins/oasis/modules/templates/Body_Index.php on line 127',
        }) == 'PHP-PHP Fatal Error: Allowed memory size of N bytes exhausted (tried to allocate N bytes) in /skins/oasis/modules/templates/Body_Index.php on line 127-Production'

        # remove regex modifiers details
        assert self._source._normalize({
            '@message': 'PHP Warning: preg_match(): Unknown modifier \'d\' in /usr/wikia/slot1/3967/src/extensions/DynamicPageList/DynamicPageListInclude.php on line 629',
        }) == 'PHP-PHP Warning: preg_match(): Unknown modifier X in /extensions/DynamicPageList/DynamicPageListInclude.php on line 629-Production'

        assert self._source._normalize({
            '@message': 'PHP Warning: preg_match(): Compilation failed: unmatched parentheses at offset 330 in /usr/wikia/slot1/4182/src/extensions/AbuseFilter/AbuseFilter.parser.php on line 219',
        }) == 'PHP-PHP Warning: preg_match(): Compilation failed: unmatched parentheses at offset N in /extensions/AbuseFilter/AbuseFilter.parser.php on line 219-Production'

        # DFS warnings (PLATFORM-1735)
        assert self._source._normalize({
            '@message': 'PHP Warning: fopen(/images/f/fallout/ru/images/lockdir/glhnpfrdy6whq8huspvtijr1bruag2p.lock): failed to open stream: No such file or directory in /includes/filerepo/backend/lockmanager/FSLockManager.php on line 89',
        }) == 'PHP-PHP Warning: fopen(/images/X): failed to open stream: No such file or directory in /includes/filerepo/backend/lockmanager/FSLockManager.php on line 89-Production'

        assert self._source._normalize({
            '@message': 'PHP Warning: mwstore://swift-backend/sonicstory/de/images/3/32/Temp_565db37342e7c0.04269745 was not stored with SHA-1 metadata. in /includes/filerepo/backend/SwiftFileBackend.php on line 574',
        }) == 'PHP-PHP Warning: mwstore://swift-backend/X was not stored with SHA-1 metadata. in /includes/filerepo/backend/SwiftFileBackend.php on line 574-Production'

        # fatals normalization (PLATFORM-1463)
        assert self._source._normalize({
            '@message': 'PHP Fatal Error: Maximum execution',
        }) == 'PHP-PHP Fatal Error: Maximum execution-Production'

        assert self._source._normalize({
            '@message': 'PHP Fatal error:  Maximum execution',
        }) == 'PHP-PHP Fatal Error: Maximum execution-Production'

        assert self._source._normalize({
            '@message': 'PHP Fatal error: Maximum execution',
        }) == 'PHP-PHP Fatal Error: Maximum execution-Production'

        # normalize PHP fatal errors with a full backtrace
        assert self._source._normalize({
            '@message': "PHP Fatal Error: Uncaught exception 'DBConnectionError' with message 'DB connection error: Unknown MySQL server host 'slave.db-sharedb.service.consul' (2) (slave.db-sharedb.service.consul)' in /usr/wikia/slot1/8369/src/includes/db/Database.php:825\nStack trace:\n#0 /usr/wikia/slot1/8369/src/includes/db/LoadBalancer.php(774): DatabaseBase->reportConnectionError('Unknown error (...')\n#1 /usr/wikia/slot1/8369/src/includes/db/LoadBalancer.php(530): LoadBalancer->reportConnectionError(Object(DatabaseMysqli))\n#2 /usr/wikia/slot1/8369/src/includes/GlobalFunctions.php(3640): LoadBalancer->getConnection(-1, Array, 'wikicities')\n#3 /usr/wikia/slot1/8369/src/extensions/wikia/WikiFactory/WikiFactory.php(169): wfGetDB(-1, Array, 'wikicities')\n#4 /usr/wikia/slot1/8369/src/extensions/wikia/WikiFactory/WikiFactory.php(2722): WikiFactory::db(-1)\n#5 /usr/wikia/slot1/8369/src/extensions/wikia/WikiFactory/WikiFactory.php(2676): WikiFactory::getCategories('530', true)\n#6 /usr/wikia/slot1/8369/config/CommonExtensions.php(94): WikiFactory::getCategory('530')\n#7 /usr/wikia/slot1/8369/config/LocalSettings.php(119): require_once('/usr/wikia/slot...')\n#8 /usr/wikia/slot1/8369/src/LocalSettings.php(4): require('/usr/wikia/slot...')\n#9 /usr/wikia/slot1/8369/src/includes/WebStart.php(141): require_once('/usr/wikia/slot...')\n#10 /usr/wikia/slot1/8369/src/wikia.php(13): require('/usr/wikia/slot...')\n#11 {main}\n  thrown in /usr/wikia/slot1/8369/src/includes/db/Database.php on line 825",
        }) == "PHP-PHP Fatal Error: Uncaught exception 'DBConnectionError' with message 'DB connection error: Unknown MySQL server host 'slave.db-sharedb.service.consul' (2) (slave.db-sharedb.service.consul)' in /includes/db/Database.php:825 thrown in /includes/db/Database.php on line 825-Production"

    def test_get_kibana_url(self):
        assert self._source._get_kibana_url({
            '@message': 'PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /usr/wikia/slot1/2996/src/includes/Linker.php on line 184'
        }) == 'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=%40source_host%3A%20ap-s%2A%20AND%20%22PHP%20Fatal%20Error%3A%20Maximum%20execution%20time%20of%20180%20seconds%20exceeded%22%20AND%20%22/src/includes/Linker.php%20on%20line%20184%22&from=6h&fields=@timestamp,@message,@fields.url,@source_host'

        assert self._source._get_kibana_url({
            '@message': 'PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /usr/wikia/slot1/2996/src/includes/Linker.php on line 184',
            '@source_host': 'task-s2'
        }) == 'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=%40source_host%3A%20task-s%2A%20AND%20%22PHP%20Fatal%20Error%3A%20Maximum%20execution%20time%20of%20180%20seconds%20exceeded%22%20AND%20%22/src/includes/Linker.php%20on%20line%20184%22&from=6h&fields=@timestamp,@message,@fields.url,@source_host'

        assert self._source._get_kibana_url({
            '@message': 'PHP Fatal error: Call to undefined method Block::getPermissionsError() in /usr/wikia/slot1/3866/src/extensions/VisualEditor/ApiVisualEditor.php on line 449'
        }) == 'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=%40source_host%3A%20ap-s%2A%20AND%20%22PHP%20Fatal%20error%3A%20Call%20to%20undefined%20method%20Block%3A%3AgetPermissionsError%28%29%22%20AND%20%22/src/extensions/VisualEditor/ApiVisualEditor.php%20on%20line%20449%22&from=6h&fields=@timestamp,@message,@fields.url,@source_host'

        assert self._source._get_kibana_url({
            '@message': 'PHP Catchable fatal error: Argument 1 passed to ArticleService::getContentFromParser() must be an instance of ParserOutput, boolean given, called in /usr/wikia/slot1/4610/src/includes/wikia/services/ArticleService.class.php on line 192'
        }) == 'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query=%40source_host%3A%20ap-s%2A%20AND%20%22PHP%20Catchable%20fatal%20error%3A%20Argument%201%20passed%20to%20ArticleService%3A%3AgetContentFromParser%28%29%20must%20be%20an%20instance%20of%20ParserOutput%20boolean%20given%20called%22%20AND%20%22/src/includes/wikia/services/ArticleService.class.php%20on%20line%20192%22&from=6h&fields=@timestamp,@message,@fields.url,@source_host'

        assert self._source._get_kibana_url({}) is None

        assert self._source._get_kibana_url({
            '@message': 'PHP Fatal Error: foo bar'
        }) is None

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
        print report  # print out to stdout, pytest will show it in case of a failure

        # report should be sent with a normalized summary set
        assert report.get_summary() == 'PHP Fatal Error: Call to a member function getText() on a non-object in /includes/wikia/services/ArticleService.class.php on line 187'

        # the full message should be kept in the description
        assert entry.get('@message') in report.get_description()

        # URL should be extracted
        assert '*URL*: http://zh.asoiaf.wikia.com/wikia.php?controller=GameGuides&method=renderpage&page=%E5%A5%94%E6%B5%81%E5%9F%8E' in report.get_description()
        assert '*Env*: Production' in report.get_description()

        # a proper label should be set
        assert report.get_labels() == ['PHPErrors']

    def test_get_url_from_entry(self):
        assert self._source._get_url_from_entry({
            "@fields": {
                "server": "zh.asoiaf.wikia.com",
                "url": "/wikia.php?controller=Foo&method=bar",
            }
        }) == 'http://zh.asoiaf.wikia.com/wikia.php?controller=Foo&method=bar'

        assert self._source._get_url_from_entry({
            "@fields": {
                "server": "zh.asoiaf.wikia.com",
                "url": u"/wiki/Ąźć",
            }
        }) == 'http://zh.asoiaf.wikia.com/wiki/Ąźć'

        assert self._source._get_url_from_entry({}) is False

    def test_get_env_from_entry(self):
        # main DC (SJC)
        assert self._source._get_env_from_entry({'@source_host': 'ap-s32'}) is self._source.ENV_MAIN_DC
        assert self._source._get_env_from_entry({'@source_host': 'service-s32'}) is self._source.ENV_MAIN_DC

        # backup DC (Reston)
        assert self._source._get_env_from_entry({'@source_host': 'ap-r32'}) is self._source.ENV_BACKUP_DC
        assert self._source._get_env_from_entry({'@source_host': 'service-r1'}) is self._source.ENV_BACKUP_DC

        # preview / verify
        assert self._source._get_env_from_entry({'@source_host': 'staging-s3'}) is self._source.ENV_PREVIEW
        assert self._source._get_env_from_entry({'@source_host': 'staging-s4'}) is self._source.ENV_MAIN_DC


class DBErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPErrorsSource class
    """
    def setUp(self):
        self._source = DBQueryErrorsSource()
        self._entry = {
            "@exception": {
                "message": "A database error has occurred.  Did you forget to run maintenance/update.php after upgrading?  See: https://www.mediawiki.org/wiki/Manual:Upgrading#Run_the_update_script\nQuery: SELECT  DISTINCT `page`.page_namespace AS page_namespace,`page`.page_title AS page_title,`page`.page_id AS page_id, `page`.page_title  as sortkey FROM `page` WHERE 1=1  AND `page`.page_namespace IN ('6') AND `page`.page_is_redirect=0 AND 'Hal Homsar Solo' = (SELECT rev_user_text FROM `revision` WHERE `revision`.rev_page=page_id ORDER BY `revision`.rev_timestamp ASC LIMIT 1) ORDER BY page_title ASC LIMIT 0, 500\nFunction: DatabaseBase::sourceFile( /usr/wikia/slot1/3690/src/maintenance/cleanupStarter.sql )\nError: 1317 Query execution was interrupted (10.8.38.37)\n"
            },
            "@context": {
                "errno": 1317,
                "err": "Query execution was interrupted (10.8.38.37)",
                "server": "10.8.38.37"
            },
        }

    def test_get_context_from_entry(self):
        context = DBQueryErrorsSource._get_context_from_entry(self._entry)

        assert context.get('function') == 'DatabaseBase::sourceFile( /maintenance/cleanupStarter.sql )'
        assert context.get('query') == "SELECT  DISTINCT `page`.page_namespace AS page_namespace,`page`.page_title AS page_title,`page`.page_id AS page_id, `page`.page_title  as sortkey FROM `page` WHERE 1=1  AND `page`.page_namespace IN ('6') AND `page`.page_is_redirect=0 AND 'Hal Homsar Solo' = (SELECT rev_user_text FROM `revision` WHERE `revision`.rev_page=page_id ORDER BY `revision`.rev_timestamp ASC LIMIT 1) ORDER BY page_title ASC LIMIT 0, 500"
        assert context.get('error') == '1317 Query execution was interrupted (10.8.38.37)'

        assert DBQueryErrorsSource._get_context_from_entry({}) is None

    def test_filter(self):
        assert self._source._filter({'@source_host': self._source.PREVIEW_HOST}) is True
        assert self._source._filter({'@source_host': 'ap-s32'}) is True
        assert self._source._filter({'@source_host': 'ap-r32'}) is True
        assert self._source._filter({}) is False  # empty message

        assert self._source._filter({'@source_host': 'ap-s32', '@context': {"errno": 1213, "err": "Deadlock found when trying to get lock; try restarting transaction (10.8.44.31)"}}) is False  # deadlock
        assert self._source._filter({'@source_host': 'ap-s32', '@context': {"errno": 1205, "err": "Lock wait timeout exceeded; try restarting transaction (10.8.62.66)"}}) is False  # lock wait timemout
        assert self._source._filter({'@source_host': 'ap-s32', '@context': {"errno": 1317, "err": "Query execution was interrupted (10.8.62.57)"}}) is True

    def test_get_report(self):
        self._source._normalize(self._entry)

        report = self._source._get_report(self._entry)
        print report  # print out to stdout, pytest will show it in case of a failure

        assert 'DB error 1317 Query execution was interrupted' in report.get_summary()
        assert 'DatabaseBase::sourceFile' in report.get_summary()
        assert '10.8.38.37' not in report.get_summary()  # database IP should be removed from the ticket summary

        assert '*DB server*: 10.8.38.37' in report.get_description()

        assert report.get_labels() == ['DBQueryErrors']
