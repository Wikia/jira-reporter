import json

from reporter.sources.common import Source
from reporter.reports import Report

from .client import AnemometerClient


class AnemometerSource(Source):
    """
    Query Anenometer data and report queries with the worst performance
    """
    ANEMOMETER_URL = 'http://opstools-s1/anemometer'
    QUERY_TIME_SUM_THRESHOLD = 300  # do not report queries that take less than 250 sec (time sum over a day) [sec]
    QUERY_TIME_MEDIAN_THRESHOLD = 0.5  # do not report queries that take less than 0.25 sec (median time) [sec]

    REPORT_LABEL = 'Anemometer'

    FULL_MESSAGE_TEMPLATE = """
*The following query does not perform too well and can be optimized. [View this query details in Anemometer|{url}].*

{{noformat}}{query}{{noformat}}

*Median query time*: {median} sec
*Median rows examined*: {examined}
*Rows sent average*: {rows}
*DB server*: {server}
*Database*: {database}

h5. Example query
{{code}}
{example}
{{code}}

h5. Raw stats
{{code}}
{stats}
{{code}}
"""

    def _get_entries(self, query=''):
        return AnemometerClient(self.ANEMOMETER_URL).get_queries()

    def _filter(self, entry):
        if entry.get('Fingerprint') == 'mysqldump':
            return False

        # we do know that DPL is broken by design
        if 'DPLMain:dynamicPageList' in entry.get('snippet'):
            return False

        if float(entry.get('Query_time_sum')) > self.QUERY_TIME_SUM_THRESHOLD or \
           float(entry.get('Query_time_median')) > self.QUERY_TIME_MEDIAN_THRESHOLD:
            return True

        return False

    def _normalize(self, entry):
        return entry.get('checksum')  # Anenometer generates a hash for us

    def _get_report(self, entry):
        stats = {k: v for k, v in entry.iteritems() if '_avg' in k or '_sum' in k or '_median' in k}

        url = '{}/index.php?action=show_query&datasource=localhost&checksum={}'.format(self.ANEMOMETER_URL, entry.get('checksum'))

        report = Report(
            summary='[Anemometer] {} can be optimized'.format(entry.get('snippet')),
            description=self.FULL_MESSAGE_TEMPLATE.format(
                query=entry.get('Fingerprint'),
                server=entry.get('hostname_max'),
                database=entry.get('db_max'),
                median=float(entry.get('Query_time_median')),
                rows=int(entry.get('rows_sent_avg')),
                examined=float(entry.get('Rows_examined_median')),
                example=entry.get('sample').encode('utf8'),
                url=url,
                stats=json.dumps(stats, indent=True),
            ),
            label=self.REPORT_LABEL
        )

        report.add_label('database')
        report.add_label('performance')

        return report
