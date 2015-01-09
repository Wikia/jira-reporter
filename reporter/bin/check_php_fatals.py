#!/usr/bin/env python
import logging
from pprint import pprint

from reporter.reporters import Jira
from reporter.sources import PHPErrorsSource

logging.basicConfig(level=logging.INFO)

"""

{
  "@timestamp": "2015-01-07T06:49:41.849580+00:00",
  "@message": "PHP Fatal Error: Maximum execution time of 180 seconds exceeded in /usr/wikia/slot1/2996/src/includes/Linker.php on line 184",
  "@fields": {
    "db_name": "endcdatabase",
    "city_id": "2237",
    "url": "/wiki/Batman",
    "ip": "10.8.62.24",
    "http_method": "GET",
    "server": "dc.wikia.com",
    "referrer": "http://dc.wikia.com/wiki/Main_Page",
    "request_id": "mw54acd63eb58243.00710805"
  }
}

{
  "@timestamp": "2015-01-07T06:49:43.983157+00:00",
  "@message": "PHP Warning: Illegal string offset mtime in /usr/wikia/slot1/2996/src/includes/filerepo/backend/FileBackend.php on line 1106",
  "@fields": {
    "db_name": "military",
    "city_id": "104",
    "url": "/wiki/Cossacks?action=edit&section=3",
    "ip": "10.8.62.24",
    "http_method": "GET",
    "server": "military.wikia.com",
    "request_id": "mw54acd706e66399.30339928"
  }
}

{
  "@timestamp": "2015-01-08T09:23:00.091+00:00",
  "syslog_pid": "24705",
  "@message": "PHP Fatal error:  Call to a member function getText() on a non-object in /usr/wikia/slot1/3006/src/includes/wikia/services/ArticleService.class.php on line 187",
  "tags": [
    "message"
  ],
  "@source_host": "ap-s10",
  "severity": "notice",
  "facility": "user-level",
  "priority": "13",
  "program": "apache2",
  "@context": {}
}

{
  "@timestamp": "2015-01-09T09:50:24.822466+00:00",
  "@message": "PHP Fatal Error: Call to a member function getNamespace() on a non-object in /usr/wikia/slot1/2644/src/includes/Article.php on line 109",
  "@fields": {
    "db_name": "spinpasta",
    "city_id": "671024",
    "url": "/wikia.php?controller=MercuryApi&method=getArticle&title=Spinpasta_Wiki",
    "ip": "10.12.66.115",
    "http_method": "GET",
    "server": "spinpasta.wikia.com",
    "request_id": "mw54afa460bf79a5.05013646"
  }
}

"""

issue = Jira()._jira.issue('ER-5166')
pprint(issue.fields())

#source = PHPErrorsSource(period=3600)
source = PHPErrorsSource(period=3600*8)
source.LIMIT = 25000

#res = source.query("PHP Warning")
res = source.query("PHP Fatal Error", threshold=10)

reporter = Jira()

for report in res:
    reporter.report(report)

"""
for item in res:
    print '\n\nHash: {}\nCounter: {}'.format(item.get_unique_id(), item.get_counter())
    print item.get_summary() + "\n-----\n"
    print item.get_description()
"""
