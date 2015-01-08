#!/usr/bin/env python
import json
import logging
import re

from reporter.sources import KibanaSource
from reporter.report import Report

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

"""


class PHPErrorsSource(KibanaSource):
    def query(self, query):
        """
        Search for messages starting with "query"
        """
        return super(PHPErrorsSource, self).query({"@message": "/^" + query + ".*/"})

    def _filter(self, entry):
        message = entry.get('@message')
        host = entry.get('@source_host')

        # filter out by host
        # "@source_host": "ap-s10",
        if re.search(r'^(ap|task|cron|liftium)\-s', host) is None:
            return False

        # filter out errors without a clear context
        # on line 115
        if re.search(r'on line \d+', message) is None:
            return False

        return True

    def _normalize(self, entry):
        """
        Normalize given message by removing variables like server name
        to improve grouping of messages

        PHP Fatal Error: Call to a member function getText() on a non-object in /usr/wikia/slot1/3006/src/includes/api/ApiParse.php on line 20

        will become:

        Call to a member function getText() on a non-object in /includes/api/ApiParse.php on line 20
        """
        message = entry.get('@message')

        # remove the prefix
        # PHP Fatal error:
        message = re.sub(r'PHP (Fatal error|Warning):', '', message, flags=re.IGNORECASE).strip()

        # remove release-specific part
        # /usr/wikia/slot1/3006/src
        message = re.sub(r'/usr/wikia/slot1/\d+/src', '', message)

        #self._logger.info(message)

        return message

source = PHPErrorsSource(period=3600)
res = source.query("PHP Warning")
logging.info(json.dumps(res, indent=True))

res = source.query("PHP Fatal Error")
logging.info(json.dumps(res, indent=True))
