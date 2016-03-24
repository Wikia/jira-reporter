import json

from reporter.reports import Report

from common import MercuryLogsSource


class MercuryFatalsSource(MercuryLogsSource):
    """ Get Mercury fatals from elasticsearch """
    REPORT_LABEL = 'MercuryFatals'

    def _get_entries(self, query):
        """ Return matching entries by given prefix """
        return self._kibana.query_by_string(
            query='severity: "fatal" AND name: "mercury" AND @source_host: /mercury-(s|r).*/',
            limit=self.LIMIT
        )

    def _filter(self, entry):
        return True

    def _get_kibana_url(self, entry):
        """
        Get the link to Kibana dashboard showing the provided error log entry
        """
        message = entry.get('msg')
        if not message:
            return None

        return self.format_kibana_url(
            query='name: "mercury" AND "{message}"'.format(
                message=message.encode('utf8')
            ),
            columns=['@timestamp', 'namespace', 'msg', 'error', 'severity']
        )

    def _normalize(self, entry):
        """
        Normalize given entry
        """
        return 'Mercury-{}={}'.format(
            entry.get('namespace'),
            entry.get('msg').encode('utf8')
        )

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        message = entry.get('msg').encode('utf8')
        namespace = entry.get('namespace')

        description = self.REPORT_TEMPLATE.format(
            full_message=message,
            details=json.dumps(entry, indent=True)
        ).strip()

        # eg. [infobox-builder] Translation not found
        summary = '[{}] {}'.format(namespace, message)

        report = Report(
            summary=summary,
            description=description,
            label=self.REPORT_LABEL
        )

        # eg. mercury-infobox-builder
        report.add_label('mercury-{}'.format(namespace))

        return report
