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

    # use MediaWiki-specific index
    ELASTICSEARCH_INDEX_PREFIX = 'logstash-mediawiki'

    @staticmethod
    def _normalize_trace(trace):
        """
        Remove release-specific part of file paths

        /usr/wikia/slot1/6875/src/includes/wikia/services/UserStatsService.class.php:452
        /includes/wikia/services/UserStatsService.class.php:452
        """
        return [re.sub(r'/usr/wikia/slot1/\d+/src', '', entry) for entry in trace]

    @staticmethod
    def _get_backtrace_from_exception(exception, offset=0):
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

        trace = PHPLogsSource._normalize_trace(trace)
        trace = trace[offset:]

        return '* ' + '\n* '.join(trace)

    @staticmethod
    def _get_wikia_caller_from_exception(exception):
        """
        Get the a first trace's line that is Wikia code, i.e. comes from /extensions/wikia/...
        """
        if exception is None:
            return None

        trace = exception.get('trace')
        if trace is None:
            return None

        trace = PHPLogsSource._normalize_trace(trace)

        for entry in trace:
            if '/extensions/wikia/Security' in entry:
                continue

            if re.search(r'/includes/wikia/api/|/skins/oasis/modules/|/extensions/wikia/|/extensions/VisualEditor/wikia/', entry):
                return entry

        return None
