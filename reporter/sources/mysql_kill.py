"""
Report slow queries killed by mysql-killer script

@see SUS-5511
"""

import json

from .common import KibanaSource

from reporter.helpers import generalize_sql
from reporter.reports import Report


class KilledDatabaseQueriesSource(KibanaSource):
    """ Get database queries killed by mysql-killer script """
    REPORT_LABEL = 'mysql-killer'

    ELASTICSEARCH_INDEX_PREFIX = 'logstash-other'

    FULL_MESSAGE_TEMPLATE = """
The following database query was killed by {{{{mysql-killer}}}} script, because it was taking too long to complete.

*Database name*: {db}
*Database host*: {host}
*Client IP*: {client}
*Query time*: {query_time} seconds
*Method*: {{{{{method}}}}}

This query is dead. This query is no more.

{{code:sql}}
{query}
{{code}}

*More details*:

{{code}}
{entry}
{{code}}
"""

    LIMIT = 1000

    FIELDS = ['@source_host', 'query', 'query_class', 'query_client', 'query_time', 'db', 'client']

    def _get_entries(self, query):
        """ mysql-kill log """
        # @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/drozdo.pt-kill
        return self._kibana.query_by_string(
            query='program:"mysql-killer" AND query:*',
            limit=self.LIMIT,
            fields=self.FIELDS
        )

    def _filter(self, entry):
        return True

    def _normalize(self, entry):
        """ Normalize the entry using the controller and method names """
        sql = generalize_sql(entry.get('query'))
        return '{}-{}-{}'.format(self.REPORT_LABEL, sql, entry.get('query_class'))

    def _get_kibana_url(self, entry):
        """
        Get the link to Kibana dashboard showing the provided error log entry
        """
        return self.format_kibana_url(
            query='program: "mysql-killer" AND query_class:"{}"'.format(entry.get('query_class')),
            columns=self.FIELDS
        )

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        # format the report
        description = self.FULL_MESSAGE_TEMPLATE.format(
            db=entry.get('db', 'n/a'),
            host=entry.get('@source_host'),
            client=entry.get('client', 'n/a'),
            query_time=entry.get('query_time', 'n/a'),
            method=entry.get('query_class'),
            query=entry.get('query'),
            entry=json.dumps(entry, indent=True),
        ).strip()

        # add a fake path to the class, to that we will try to make classifier attach a proper component
        class_name = entry.get('query_class', '').split(':')[0]
        description += '\n\nPossible source file:\n* /extensions/wikia/{}:1'.format(class_name)

        return Report(
            summary='[{method}] Long running query was killed by mysql-killer'.format(method=entry.get('query_class')),
            description=description,
            label=self.REPORT_LABEL
        )
