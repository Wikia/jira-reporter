import re

from reporter.sources.common import KibanaSource


class PHPLogsSource(KibanaSource):
    """
    Base class for Kibana-powered PHP logs
    """
    REPORT_TEMPLATE = """
{full_message}

*URL*: {url}
*Env*: {env}

{{code}}
@source_host = {source_host}

@context = {context_formatted}

@fields = {fields_formatted}
{{code}}
    """

    @staticmethod
    def _normalize_backtrace(trace):
        """ Remove release-specific path  """
        if trace is None:
            return 'n/a'

        # /usr/wikia/slot1/6875/src/includes/wikia/services/UserStatsService.class.php:452
        # /includes/wikia/services/UserStatsService.class.php:452
        trace = [re.sub(r'/usr/wikia/slot1/\d+/src', '', entry) for entry in trace]

        return '* ' + '\n* '.join(trace)
