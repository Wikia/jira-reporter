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
