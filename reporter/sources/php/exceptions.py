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
            # DBQueryError exceptions are handled by DBQueryErrorsSource
            # and skip wfDebugLog calls from WikiFactory
            query='severity: "error" AND @exception.class: * AND -@exception.class: "DBQueryError" AND -@context.logGroup: "createwiki"',
            limit=self.LIMIT
        )

    def _filter(self, entry):
        # filter out by host
        # "@source_host": "ap-s10",
        host = entry.get('@source_host', '')
        if not is_production_host(host):
            return False

        # ignore PHP Fatal errors with backtrace here - they're handled by PHPErrorsSource
        message = entry.get('@message', '')
        if message.startswith('PHP Fatal '):
            return False

        return True

    def _normalize(self, entry):
        """ Normalize using the exception class and message """
        exception = entry.get('@exception', {})
        exception_class = exception.get('class')
        env = self._get_env_from_entry(entry)

        message = entry.get('@message', '')

        # use a message from the exception
        if exception_class == 'WikiaException':
            message = exception.get('message')

        message = message.encode('utf8')

        # Server #3 (10.8.38.41) is excessively lagged (126 seconds)
        message = re.sub(r'#\d+', '#X', message)
        message = re.sub(r'\d+ sec', 'X sec', message)

        # Remove release-specific part of a file path
        message = re.sub(r'/usr/wikia/slot\d/\d+/src', '', message)

        # master fallback on blobs20141/106563095
        message = re.sub(r'blobs\d+/\d+', 'blobsX', message)

        # master fallback on blobs20141/106563095
        message = re.sub(r'WikiaDataAccess could not obtain lock to generate data for: [A-Za-z0-9:]+', 'WikiaDataAccess could not obtain lock to generate data for: XXX', message)

        entry['@normalized_message'] = message

        return '{}-{}-{}'.format(env, exception_class or 'None', message)

    def _get_kibana_url(self, entry):
        """
        Get Kibana dashboard URL for a given entry

        It will be automatically added at the end of the report description
        """
        message = entry.get('@normalized_message')

        return self.format_kibana_url(
            query='"{}"'.format(message),
            columns=['@timestamp', '@source_host', '@message', '@exception.message', '@fields.db_name', '@fields.http_url']
        )

    def _get_description(self, entry):
        exception = entry.get('@exception', {})
        exception_class = exception.get('class')
        message = entry.get('@normalized_message')

        # format the report
        full_message = self.FULL_MESSAGE_TEMPLATE.format(
            exception=exception_class or 'Error',
            message=message,
            backtrace=self._get_backtrace_from_exception(exception)
        ).strip()

        description = self.REPORT_TEMPLATE.format(
            env=self._get_env_from_entry(entry),
            source_host=entry.get('@source_host', 'n/a'),
            context_formatted=json.dumps(entry.get('@context', {}), indent=True),
            fields_formatted=json.dumps(entry.get('@fields', {}), indent=True),
            full_message=full_message,
            url=self._get_url_from_entry(entry) or 'n/a'
        ).strip()

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
