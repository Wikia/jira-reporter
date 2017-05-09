from reporter.sources.common import KibanaSource
from reporter.reports import Report
import json
import time


class ChatLogsSource(KibanaSource):
    """
    Get Chat server errors from elasticsearch

    @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/Chat%20Server%20errors
    """
    REPORT_TEMPLATE = """
h3. {full_message}
{error}

{{code}}
{details}
{{code}}
    """

    REPORT_LABEL = 'ChatServerErrors'

    def _get_entries(self, query):
        """ Return entries matching given query """
        return self._kibana.query_by_string(
            query='@fields.app_name:chat AND severity:error AND @source_host:chat-s* AND @message:*{}*'.format(query),
            limit=self.LIMIT
        )

    def _filter(self, entry):
        return True

    def _get_kibana_url(self, entry):
        """
        Get the link to Kibana dashboard showing the provided error log entry
        """
        message = entry.get('@message')
        if not message:
            return None

        return self.format_kibana_url(
            query='@source_host:chat-s* AND "{message}"'.format(
                message=message.encode('utf8')
            ),
            columns=['@timestamp', '@message']
        )

    def _normalize(self, entry):
        """
        Normalize given entry
        """
        return 'Chat-{}-{}'.format(
            entry.get('@message').encode('utf8'),
            self._get_env_from_entry(entry)
        )

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        message = entry.get('@message').encode('utf8')

        description = self.REPORT_TEMPLATE.format(
            full_message=message,
            error=entry.get('error', 'n/a'),
            details=json.dumps(entry, indent=True)
        ).strip()

        report = Report(
            summary=message,
            description=description,
            label=self.REPORT_LABEL
        )

        return report
