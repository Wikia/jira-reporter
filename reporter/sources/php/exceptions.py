import json
import re

from reporter.helpers import is_production_host
from reporter.reports import Report

from common import PHPLogsSource


class PHPExceptionsSource(PHPLogsSource):
    """
    Report errors and exceptions logged via WikiaLogger
    """
    REPORT_LABEL = 'PHPExceptions'

    FULL_MESSAGE_TEMPLATE = """
h1. {exception}

{message}

h5. Backtrace
{backtrace}
"""

    def _get_entries(self, query):
        """ Return errors and exceptions reported via WikiaLogger with error severity """
        return self._kibana.query_by_string(
            query='severity:"^error" AND program: "apache2" AND -@exception.class: "DBConnectionError"',
            limit=self.LIMIT
        )

    def _filter(self, entry):
        # filter out by host
        # "@source_host": "ap-s10",
        host = entry.get('@source_host', '')
        if not is_production_host(host):
            return False

        return True

    def _normalize(self, entry):
        """ Normalize using the exception class and message """
        exception = entry.get('@exception', {})
        exception_class = exception.get('class')
        env = self._get_env_from_entry(entry)

        message = entry.get('@message', '')

        # Server #3 (10.8.38.41) is excessively lagged (126 seconds)
        message = re.sub(r'#\d+', '#X', message)
        message = re.sub(r'\d+ sec', 'X sec', message)

        # Remove release-specific part of a file path
        message = re.sub(r'/usr/wikia/slot\d/\d+/src', '', message)

        # use a message from the exception
        if exception_class == 'WikiaException':
            message = exception.get('message')

        entry['@normalized_message'] = message

        return '{}-{}-{}'.format(env, exception_class or 'None', message)

    def _get_description(self, entry):
        exception = entry.get('@exception', {})
        exception_class = exception.get('class')
        message = entry.get('@normalized_message')

        # format the report
        full_message = self.FULL_MESSAGE_TEMPLATE.format(
            exception=exception_class or 'Error',
            message=message,
            backtrace=self._normalize_backtrace(exception.get('trace'))
        ).strip()

        description = self.REPORT_TEMPLATE.format(
            env=self._get_env_from_entry(entry),
            source_host=entry.get('@source_host', 'n/a'),
            context_formatted=json.dumps(entry.get('@context', {}), indent=True),
            fields_formatted=json.dumps(entry.get('@fields', {}), indent=True),
            full_message=full_message,
            url=self._get_url_from_entry(entry) or 'n/a'
        ).strip()

        # format URL to the custom Kibana dashboard
        description += '\n\n*Still valid?* Check [Kibana dashboard|{url}]'.format(
            url=self.format_kibana_url(
                query='"{}"'.format(message),
                columns=['@timestamp', '@source_host', '@message', '@exception.message', '@fields.db_name', '@fields.url']
            )
        )

        return description

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        exception = entry.get('@exception', {})
        exception_class = exception.get('class')
        message = entry.get('@normalized_message')

        report = Report(
            summary='[{exception}] {message}'.format(
                exception=exception_class or 'Error',
                message=message
            ),
            description=self._get_description(entry),
            label=self.REPORT_LABEL
        )

        # add a custom, per exception class label
        if exception_class is not None:
            report.add_label('PHP{}'.format(exception_class))

        return report
