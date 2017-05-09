from reporter.sources.common import KibanaSource


class MercuryLogsSource(KibanaSource):
    """
    Base class for Kibana-powered Mercury logs

    @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-2055
    """
    REPORT_TEMPLATE = """
h3. {full_message}
{error}

{{code}}
{details}
{{code}}
    """
