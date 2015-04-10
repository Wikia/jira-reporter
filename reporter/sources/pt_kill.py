"""
Report slow queries killed by pt-kill script
"""

import json

from common import KibanaSource

from reporter.helpers import generalize_sql, get_method_from_query
from reporter.reports import Report


class KilledDatabaseQueriesSource(KibanaSource):
    """ Get database queries killed by pt-kill script """
    REPORT_LABEL = 'pt-kill'

    FULL_MESSAGE_TEMPLATE = """
The following database query was killed by {{{{pt-kill}}}} script, because it was taking too long to complete.

*Database name*: {db}
*Database host*: {host}
*Client IP*: {client}
*Query time*: {query_time} seconds
*Method*: {{{{{method}}}}}

This query is dead. This query is no more.

{{noformat}}
{query}
{{noformat}}

*More details*:

{{code}}
{entry}
{{code}}
"""

    LIMIT = 1000

    def _get_entries(self, query):
        """ pt-kill log """
        # @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/drozdo.pt-kill
        return self._kibana.query_by_string(
            query='program: "pt-kill"', limit=self.LIMIT)

    def _filter(self, entry):
        # must have "query" field set
        if 'query' not in entry:
            return False

        return True

    def _normalize(self, entry):
        """ Normalize the entry using the controller and method names """
        sql = generalize_sql(entry.get('query'))
        return '{}-{}'.format(self.REPORT_LABEL, sql)

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        method = get_method_from_query(entry.get('query'))

        # format the report
        description = self.FULL_MESSAGE_TEMPLATE.format(
            db=entry.get('db', 'n/a'),
            host=entry.get('@source_host'),
            client=entry.get('client', 'n/a'),
            query_time=entry.get('query_time', 'n/a'),
            method=method,
            query=entry.get('query'),
            entry=json.dumps(entry, indent=True),
        ).strip()

        return Report(
            summary='[{method}] Long running query was killed by pt-kill'.format(method=method),
            description=description,
            label=self.REPORT_LABEL
        )
