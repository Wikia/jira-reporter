import json
import re

from reporter.sources.common import KibanaSource
from reporter.helpers import is_production_host, generalize_sql
from reporter.reports import Report


class BackendSource(KibanaSource):
    """
    Get Perl backend script errors from elasticsearch
    """
    REPORT_TEMPLATE = """
h3. The Camel says "{{{{{full_message}}}}}"

{error}

{{code:sql}}
{sql}
{{code}}

{{code}}
{details}
{{code}}
    """

    ELASTICSEARCH_INDEX_PREFIX = 'logstash-backend'
    LIMIT = 150000

    # @see https://wikia-inc.atlassian.net/browse/SUS-3449
    ELASTICSEARCH_QUERY = '@message: "LB::error" AND @context.error: *'

    REPORT_LABEL = 'BackendErrors'

    def _get_entries(self, query):
        return self._kibana.query_by_string(query=self.ELASTICSEARCH_QUERY, limit=self.LIMIT)

    def _filter(self, entry):
        """ Remove log entries that are not coming from production servers """
        host = entry.get('@source_host', '')

        # errors will most likely come from job-s1
        if not is_production_host(host):
            return False

        return True

    def _get_kibana_url(self, entry):
        """
        Get the link to Kibana dashboard showing the provided error log entry
        """
        message = entry.get('@message')
        if not message:
            return None

        return self.format_kibana_url(
            query='@message: "{message}"'.format(
                message=message.encode('utf8')
            ),
            columns=['@timestamp', '@fields.script_name', '@message', '@context.error']
        )

    def _normalize(self, entry):
        """
        Normalize given entry
        """
        return 'Backend-{}-{}-{}'.format(
            entry.get('@message'),
            entry.get('@fields', {}).get('script_name', 'n/a'),
            generalize_sql(entry.get('@context', {}).get('error', 'n/a'))
        )

    @staticmethod
    def extract_error_and_sql(error):
        """
        :type error str
        :rtype: (str, str)
        """
        matches = re.match(r'DBD::mysql::db do failed: (.*) \[for Statement "(.*)"\]', error)

        err = matches.group(1) if matches else None
        sql = matches.group(2) if matches else None

        if err and sql:
            return err, sql.strip()
        else:
            return error, None

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        script = entry.get('@fields').get('script_name', '')
        message = entry.get('@message').encode('utf8')
        error = entry.get('@context').get('error', 'n/a').encode('utf8')

        # extract SQL from the error
        (error, sql) = self.extract_error_and_sql(error)

        description = self.REPORT_TEMPLATE.format(
            full_message=message,
            error=error,
            sql=sql,
            details=json.dumps(entry, indent=True)
        ).strip()

        report = Report(
            summary='{} - {}'.format(script, message),
            description=description,
            label=self.REPORT_LABEL
        )

        return report
