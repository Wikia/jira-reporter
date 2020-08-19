"""
Report issues from Helios service

@see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/Helios%20errors
"""
import json

from reporter.reports import Report
from reporter.helpers import is_from_production_host
from reporter.sources.common import KibanaSource


class HeliosSource(KibanaSource):
    REPORT_LABEL = 'Helios'

    REPORT_TEMPLATE = """
h3. {message}

{{code}}
{context}
{{code}}
    """

    LIMIT = 10000

    # use Helios-specific index
    ELASTICSEARCH_INDEX_PREFIX = 'logstash-helios'

    def _get_entries(self, query):
        return self._kibana.query_by_string(
                query='level:"error"',
                limit=self.LIMIT)

    def _filter(self, entry):
        return is_from_production_host(entry)

    def _normalize(self, entry):
        message = entry.get('@message')

        return '{}-{}'.format(self.REPORT_LABEL, message)

    def _get_kibana_url(self, entry):
        """
        Get the link to Kibana dashboard showing the provided error log entry
        """
        return self.format_kibana_url(
            query='@message: "{message}"'.format(
                message=entry.get('@message')
            ),
            columns=['@timestamp', '@message']
        )

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        # format the report
        description = self.REPORT_TEMPLATE.format(
            message=entry.get('@message'),
            context=json.dumps(entry, indent=True)
        ).strip()

        return Report(
            summary='[Helios] {message}'.format(message=entry.get('@message')),
            description=description,
            label=self.REPORT_LABEL
        )
