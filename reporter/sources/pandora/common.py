from reporter.sources.common import KibanaSource


class PandoraLogsSource(KibanaSource):
    """
    Base class for Kibana-powered Pandora logs

    @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-1420
    """
    REPORT_TEMPLATE = """
h3. {full_message}

*App name*: {{{{{app_name}}}}}
*Logger name*: {{{{{logger_name}}}}}
*Thread name*: {{{{{thread_name}}}}}

h3. Stacktrace

{{code}}
{stack_trace}
{{code}}
    """

    LIMIT = 10000
    ELASTICSEARCH_INDEX_PREFIX = 'logstash-*'
