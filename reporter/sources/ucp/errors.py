import re
import urllib.parse

from reporter.reports import Report
from reporter.sources.common import KibanaSource

"""Reports PHP errors, fatals and uncaught exceptions from Unified Community Platform (UCP)"""
class UCPErrorsSource(KibanaSource):

    REPORT_TEMPLATE = """
{full_message}

*URL*: {url}
*Env*: {env}

*Stack trace:*
{{code}}
{stack_trace}
{{code}}
    """

    ELASTICSEARCH_INDEX_PREFIX = 'logstash-mediawiki-unified-platform'
    ERRORS_MAP = {
        'fatal': {'id': '9'}, #P2
        'error': {'id': '8'}, #P3
        'exception': {'id': '6'} #Minor - team grooming
    }

    def _get_entries(self, query):
        return self._kibana.query_by_string(
            query='NOT @message:"Wikimedia\\\\Rdbms" AND (event.type:"error" OR event.type:"fatal" OR event.type:"exception")',
            limit=self.LIMIT
        )

    def _filter(self, entry):
        # Ignore Reston for now
        return entry.get('datacenter') != 'RES'

    def _get_kibana_url(self, entry):
        message = entry.get('@message')

        columns = ['@timestamp', '@message', '@fields.http_url_domain', '@fields.http_url_path']

        return self.KIBANA_URL.format(
            query=urllib.parse.quote('@message: "{message}"'.format(message=message)),
            columns="'{}'".format("','".join(columns)),
            index=self.ELASTICSEARCH_INDEX_PREFIX
        )


    def _get_env_from_entry(self, entry):
            app = entry.get('kubernetes',{}).get('labels', {}).get('app')
            dc = entry.get('datacenter')

            if app == 'mediawiki-preview-ucp':
                return self.ENV_PREVIEW

            if app is not None and re.match(r'^mediawiki-sandbox-', app):
                return self.ENV_STAGING

            if dc == 'RES':
                return self.ENV_BACKUP_DC

            return self.ENV_MAIN_DC

    def _normalize(self, entry):
        """
        Normalize given message by removing variables like server name
        to improve grouping of messages

        PHP Fatal Error: Call to a member function getText() on a non-object in /usr/wikia/slot1/3006/src/includes/api/ApiParse.php on line 20

        will become:

        Call to a member function getText() on a non-object in /includes/api/ApiParse.php on line 20
        """
        message = entry.get('@message')
        message = message.replace('\n', '')

        # remove HTTP adresses
        # Missing or invalid pubid from http://dragonball.wikia.com/__varnish_liftium/config in /var/www/liftium/delivery/config.php on line 17
        message = re.sub(r'https?://[^\s]+', '<URL>', message)

        # remove long backtraces from some error messages (they are already logged in separate field)
        message = re.sub(r'\s?Stack trace:(.*)\{main\}\s?', '', message, flags=re.MULTILINE)

        # remove index name / offset from notices
        message = re.sub(r'Undefined index: [^\s]+ in', 'Undefined index: X in', message)
        message = re.sub(r'Undefined offset: \d+ in', 'Undefined offset: N in', message)
        message = re.sub(r'Could not resolve cluster for DB name: (.*)', 'Could not resolve cluster for DB name: X', message)

        entry['@message_normalized'] = message

        env = self._get_env_from_entry(entry)

        return 'PHP-{}-{}'.format(message, env)

    @staticmethod
    def _has_all_required_fields(entry):
        fields = entry.get('@fields', {})
        return fields.get('http_url_path') is not None and fields.get('http_url_domain') is not None \
            and entry.get('stack_trace') is not None

    def _get_url_from_entry(self, entry):
        fields = entry.get('@fields', {})

        return 'https://' + fields.get('http_url_domain') + fields.get('http_url_path')

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        description = self.REPORT_TEMPLATE.format(
            env=self._get_env_from_entry(entry),
            full_message=entry.get('@message'),
            url=self._get_url_from_entry(entry) or 'n/a',
            stack_trace=entry.get('stack_trace')
        ).strip()

        priority = ERRORS_MAP[entry.get('event,type').replace("\"","")]
        report = Report(
            summary=entry.get('@message_normalized'),
            description=description,
            priority=priority
        )

        report.add_label('unified-platform')

        return report
