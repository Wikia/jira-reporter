from reporter.helpers import is_production_host
from reporter.reports import Report
from common import PHPLogsSource


class PHPExecutionTimeoutSource(PHPLogsSource):
    """
    Source of PHP execution timeouts.
    Since this problem is commonly caused by extremely large articles,
    reports should be sent to Community Support.
    """

    REPORT_LABEL = "php-timeout"

    REPORT_TEMPLATE = """
The below URL is taking too much time to render. This is usually caused by extremely large articles.

*URL*: {url}
    """

    def _get_entries(self, query):
        """ Returns PHP timeout errors """
        return self._kibana.query_by_string(
            query='"PHP Fatal Error: Maximum execution time"',
            limit=self.LIMIT
        )

    def _filter(self, entry):
        return is_production_host(entry.get('@source_host', ''))

    def _normalize(self, entry):
        url = self._get_url_from_entry(entry)

        return '{}-php-timeout'.format(url)

    def _get_report(self, entry):
        url = self._get_url_from_entry(entry)

        return Report(
            summary='Timeout error: {}'.format(url),
            description=self.REPORT_TEMPLATE.format(url=url),
            label=self.REPORT_LABEL
        )

    def _get_kibana_url(self, entry):
        url = self._get_url_from_entry(entry)

        return self.format_kibana_url(
            query='"PHP Fatal Error: Maximum execution time" AND @fields.http_url:"{}"'.format(url),
            columns=['@timestamp', '@fields.http_url']
        )
