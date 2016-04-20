"""
Report issues with thumbnail sizing from Vignette
"""

from reporter.sources.common import KibanaSource
from reporter.reports import Report

class VignetteThumbVerificationSource(KibanaSource):


    REPORT_TEMPLATE = """
h3. {full_message}

*App name*: {{{{{app_name}}}}}
*Source host*: {{{{{source_host}}}}}
*Thumb map*: {{{{{thumb_map}}}}}
*Estimated*: {{{{{estimated}}}}}
*Actual*: {{{{{actual}}}}}

    """

    LIMIT = 1000

    LOGGER = 'vignette.util.thumb-verifier'

    KIBANA_QUERY = 'appname: "vignette" AND logger_name: "{}" AND level: "ERROR"'.format(LOGGER)

    def _get_entries(self, query):
        return self._kibana.query_by_string(
            query=self.KIBANA_QUERY,
            limit=self.LIMIT
        )

    def _filter(self, entry):
        return True

    def _normalize(self, entry):
        message = entry.get('@message')
        logger_name = entry.get('logger_name')
        return 'Vignette-{}-{}'.format(logger_name, message)

    def _get_kibana_url(self, entry):
        return self.format_kibana_url(
            query=self.KIBANA_QUERY,
            columns=['@timestamp', '@source_host', '@message', 'thumb-map', 'estimated', 'actual']
        )

    def _get_report(self, entry):
        message = entry.get('@message')
        app_name = entry.get('appname')
        description = self.REPORT_TEMPLATE.format(
            full_message='{}: {}'.format(entry.get('level'), message),
            app_name=app_name,
            source_host=entry.get('@source_host'),
            thumb_map=entry.get('thumb-map'),
            estimated=entry.get('estimated'),
            actual=entry.get('actual')
        ).strip()

        return Report(
            summary='[{}] {}'.format(app_name, message),
            description=description,
            label=app_name
        )
