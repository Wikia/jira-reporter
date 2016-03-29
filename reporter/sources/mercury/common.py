from reporter.sources.common import KibanaSource


class MercuryLogsSource(KibanaSource):
    """
    Base class for Kibana-powered Mercury logs

    @see https://kibana.wikia-inc.com/#/dashboard/temp/AVOjc8W-tlVOnUfDvyCL
    """
    REPORT_TEMPLATE = """
h3. {full_message}

{{code}}
{details}
{{code}}
    """

    LIMIT = 10000
