import json

from reporter.helpers import is_production_host
from reporter.reports import Report

from .common import PHPLogsSource


class PHPTriggeredSource(PHPLogsSource):
    """
    Report messages logged from PHP code with "@context.jira_reporter: 1"

    So far used to:
     * SUS-3469 | to report outdated video providers
    """
    REPORT_LABEL = 'PHPTriggered'

    def _get_entries(self, query):
        return self._kibana.query_by_string(query='@context.jira_reporter: 1 AND @context.tags: *', limit=self.LIMIT)

    def _filter(self, entry):
        return True

    def _normalize(self, entry):
        """ Normalize using the message """
        return entry.get('@message')

    def _get_kibana_url(self, entry):
        """
        Get Kibana dashboard URL for a given entry

        It will be automatically added at the end of the report description
        """
        return None

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        context = entry.get('@context', {})
        message = entry.get('@message')

        # labels to add a report
        report = Report(
            summary=message,
            description=context.get('body'),
            label=self.REPORT_LABEL
        )

        # add report specific labels
        [report.add_label(label) for label in context.get('tags', [])]

        return report
