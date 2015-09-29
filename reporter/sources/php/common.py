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
    def _get_backtrace_from_exception(exception):
        """ Get the PHP backtrace from the exception object and remove release-specific path  """
        if exception is None:
            return 'n/a'

        trace = exception.get('trace')

        if trace is None:
            return 'n/a'

        # add a line from which exception was thrown
        # e.g. /usr/wikia/slot1/7211/src/extensions/wikia/UserProfilePageV3/UserProfilePageController.class.php:334
        file_entry = exception.get('file')

        if file_entry is not None:
            trace = [file_entry] + trace

        # /usr/wikia/slot1/6875/src/includes/wikia/services/UserStatsService.class.php:452
        # /includes/wikia/services/UserStatsService.class.php:452
        trace = [re.sub(r'/usr/wikia/slot1/\d+/src', '', entry) for entry in trace]

        return '* ' + '\n* '.join(trace)
