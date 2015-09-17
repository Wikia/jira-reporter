import json
import re
import urllib

from reporter.helpers import is_production_host
from reporter.reports import Report

from common import PHPLogsSource


class PHPErrorsSource(PHPLogsSource):
    """ Get PHP errors from elasticsearch """
    REPORT_LABEL = 'PHPErrors'

    def _get_entries(self, query):
        """ Return matching entries by given prefix """
        return self._kibana.query_by_string(query='@message:"^{}"'.format(query), limit=self.LIMIT)

    def _filter(self, entry):
        """ Remove log entries that are not coming from main DC or lack key information """
        message = entry.get('@message', '')
        host = entry.get('@source_host', '')

        # filter out by host
        # "@source_host": "ap-s10",
        if not is_production_host(host):
            return False

        # filter out errors without a clear context
        # on line 115
        if re.search(r'on line \d+', message) is None:
            return False

        return True

    def _get_kibana_url(self, entry):
        """
        Get the link to Kibana dashboard showing the provided error log entry
        """
        message = entry.get('@message')
        if not message:
            return None

        # match appropriate hosts
        # ap-s42:  ap-s*
        # task-s1: task-s*
        host = entry.get('@source_host')
        if host is not None:
            host_regexp = host.split('-')[0] + '-s*'
        else:
            host_regexp = 'ap-s*'

        # split the message
        # PHP Warning: Invalid argument supplied for foreach() in /usr/wikia/slot1/3823/src/extensions/wikia/PhalanxII/templates/PhalanxSpecial_main.php on line 141
        matches = re.match(r'^(.*) in /usr/wikia/slot1/\d+(.*)$', message)

        if not matches:
            return None

        return self.KIBANA_URL.format(
            query=urllib.quote('@source_host: {host} AND "{message}" AND "{file}"'.format(
                host=host_regexp, message=matches.group(1).replace(',', ''), file=matches.group(2)
            )),
            fields=','.join(['@timestamp', '@message', '@fields.url', '@source_host'])
        )

    def _normalize(self, entry):
        """
        Normalize given message by removing variables like server name
        to improve grouping of messages

        PHP Fatal Error: Call to a member function getText() on a non-object in /usr/wikia/slot1/3006/src/includes/api/ApiParse.php on line 20

        will become:

        Call to a member function getText() on a non-object in /includes/api/ApiParse.php on line 20
        """
        message = entry.get('@message')

        # remove exception prefix
        # Exception from line 141 of /includes/wikia/nirvana/WikiaView.class.php:
        message = re.sub(r'Exception from line \d+ of [^:]+:', 'Exception:', message)

        # remove HTTP adresses
        # Missing or invalid pubid from http://dragonball.wikia.com/__varnish_liftium/config in /var/www/liftium/delivery/config.php on line 17
        message = re.sub(r'https?://[^\s]+', '<URL>', message)

        # remove release-specific part
        # /usr/wikia/slot1/3006/src
        message = re.sub(r'/usr/wikia/slot1/\d+/src', '', message)

        # remove XML parsing errors details
        # Tag figure invalid in Entity, line: 286
        # Tag X invalid in Entity, line: N
        message = re.sub(r'Tag \w+ invalid in Entity, line: \d+', 'Tag X invalid in Entity, line: N', message)

        # remove popen() arguments
        message = re.sub(r'popen\([^\)]+\)', 'popen(X)', message)

        # remove exec arguments
        message = re.sub(r'Unable to fork \[[^\]]+\]', 'Unable to fork [X]', message)

        # normalize /tmp paths
        message = re.sub(r'/tmp/\w+', '/tmp/X', message)

        # normalize "17956864 bytes"
        message = re.sub(r'\d+ bytes', 'N bytes', message)

        # normalize preg_match() related warnings
        message = re.sub(r'Unknown modifier \'\w+\'', 'Unknown modifier X', message)
        message = re.sub(r'Compilation failed: unmatched parentheses at offset \d+',
                         'Compilation failed: unmatched parentheses at offset N', message)

        # normalize fatals (PLATFORM-1463)
        message = re.sub(r'PHP Fatal Error:\s+', 'PHP Fatal Error: ', message, flags=re.IGNORECASE)

        # update the entry
        entry['@message_normalized'] = message

        # production or preview?
        env = self._get_env_from_entry(entry)

        return 'PHP-{}-{}'.format(message, env)

    @staticmethod
    def _has_all_required_fields(entry):
        # @fields.url is required
        # see PLATFORM-1162
        return entry.get('@fields', {}).get('url') is not None

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        description = self.REPORT_TEMPLATE.format(
            env=self._get_env_from_entry(entry),
            source_host=entry.get('@source_host', 'n/a'),
            context_formatted=json.dumps(entry.get('@context', {}), indent=True),
            fields_formatted=json.dumps(entry.get('@fields', {}), indent=True),
            full_message=entry.get('@message'),
            url=self._get_url_from_entry(entry) or 'n/a'
        ).strip()

        kibana_url = self._get_kibana_url(entry)
        if kibana_url:
            description += '\n\n*Still valid?* Check [Kibana dashboard|{url}]'.format(url=kibana_url)

        return Report(
            summary=entry.get('@message_normalized'),
            description=description,
            label=self.REPORT_LABEL
        )