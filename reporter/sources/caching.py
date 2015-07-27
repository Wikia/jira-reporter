"""
Report caching related problems
"""

from common import KibanaSource

from reporter.helpers import is_production_host
from reporter.reports import Report


class NotCachedWikiaApiResponsesSource(KibanaSource):
    """ Get wikia.php API responses that are not cached """
    REPORT_LABEL = 'APIResponsesNotCached'

    FULL_MESSAGE_TEMPLATE = """
The following wikia.php API response can probably be cached on CDN layer (and invalidated when required)
to decrease the load on the backend servers.

*Nirvana controller*: {controller}
*Method name*: {method}

To debug the request run the following command:

{{noformat}}
curl -svo /dev/null "{url}"
{{noformat}}
"""

    LIMIT = 100000  # ~1.8mm entries daily => 75k an hour

    def _get_entries(self, query):
        """ Return matching not cached responses log entries """
        # @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/wikia.php%20caching%20disabled
        return self._kibana.query_by_string(
            query='@message: "wikia-php.caching-disabled" AND @fields.http_method: "GET"', limit=self.LIMIT)

    def _filter(self, entry):
        """ Remove log entries that are not coming from main DC Apache servers """
        # filter out by host
        # "@source_host": "ap-s10",
        host = entry.get('@source_host', '')
        if not host.startswith('ap-') or not is_production_host(host):
            return False

        return True

    def _normalize(self, entry):
        """ Normalize the entry using the controller and method names """
        context = entry.get('@context', dict())
        return '{}-{}-{}'.format(self.REPORT_LABEL, context.get('controller'), context.get('method'))

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        context = entry.get('@context')

        # format the report
        description = self.FULL_MESSAGE_TEMPLATE.format(
            url=self._get_url_from_entry(entry) or 'n/a',
            controller=context.get('controller'),
            method=context.get('method')
        ).strip()

        return Report(
            summary='Consider caching {controller}::{method} wikia.php API responses'.format(
                controller=context.get('controller'), method=context.get('method')),
            description=description,
            label=self.REPORT_LABEL
        )
