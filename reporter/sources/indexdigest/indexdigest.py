import json

from reporter.sources.common import KibanaSource
from reporter.reports import Report


class IndexDigestSource(KibanaSource):
    """
    Get index-digest issues that are sent via syslog
    """
    REPORT_TEMPLATE = """
h1. {message}

*Linter*: {type}
*Table name*: {{{{{table}}}}}
*Database*: {{{{{database_name}}}}} ({database_version})
*Host*: {{{{{database_host}}}}}

h3. Table schema

{{code:sql}}
{schema}
{{code}}

h3. Context

{{code}}
{context}
{{code}}

h6. Reported by {version} - https://github.com/macbre/index-digest#checks
    """

    ELASTICSEARCH_INDEX_PREFIX = 'logstash-index-digest'

    # @see https://wikia-inc.atlassian.net/browse/SUS-3566
    # https://github.com/macbre/index-digest#syslog
    ELASTICSEARCH_QUERY = 'report.type: *'

    REPORT_LABEL = 'index-digest'

    def _get_entries(self, query):
        return self._kibana.query_by_string(query=self.ELASTICSEARCH_QUERY, limit=self.LIMIT)

    def _filter(self, entry):
        return True

    def _normalize(self, entry):
        """
        Normalize given entry
        """
        return 'index-digest-{}-{}-{}-{}'.format(
            entry.get('meta').get('database_name'),
            entry.get('report').get('type'),
            entry.get('report').get('table'),
            entry.get('report').get('message'),
        )

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        meta = entry.get('meta')
        report = entry.get('report')

        description = self.REPORT_TEMPLATE.format(
            message=report.get('message'),
            type=report.get('type'),
            table=report.get('table'),
            database_name=meta.get('database_name'),
            database_version=meta.get('database_version'),
            database_host=meta.get('database_host'),
            schema=report.get('context', {}).get('schema', '-- n/a'),
            version=meta.get('version'),
            context=json.dumps(report.get('context'), indent=True)
        ).strip()

        _report = Report(
            summary='{} | {}'.format(report.get('table'), report.get('message')),
            description=description,
            label=self.REPORT_LABEL
        )

        _report.add_label('index-digest-{}'.format(report.get('type')))

        return _report
