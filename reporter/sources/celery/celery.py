import json

from reporter.sources.common import KibanaSource
from reporter.reports import Report


class CeleryLogsSource(KibanaSource):
    """
    Get Celery worker logs from elasticsearch

    @see https://github.com/Wikia/celery-workers
    @see https://kibana.wikia-inc.com/goto/913d8072c075be08be388b3a7d9fe167
    """
    REPORT_TEMPLATE = """
Celery worker has reported the following error when processing *{queue}* queue:

{{code}}
{error}
{{code}}

h3. Details

{{code}}
{details}
{{code}}

*Flower link*: {flower_link}
    """

    LIMIT = 1500

    REPORT_LABEL = 'CeleryWorkersError'

    ELASTICSEARCH_INDEX_PREFIX = 'logstash-celery'

    def _get_entries(self, query):
        """ Return entries matching given query """
        return self._kibana.query_by_string(
            query='event: "Task failed" AND  kubernetes.namespace_name: "prod"',
            limit=self.LIMIT
        )

    def _filter(self, entry):
        return True

    def _get_kibana_url(self, entry):
        return self.format_kibana_url(
            query='@context.task_id: "{taskid}"'.format(
                taskid=entry.get('task_id')
            ),
            columns=['@timestamp', '@message'],
            index='logstash-mediawiki'
        )

    def _normalize(self, entry):
        """
        Normalize given entry
        """
        exception = entry.get('exception')

        # improve normalization of SQL queries
        if 'database error has occurred' in exception:
            exception = 'RemoteExecuteError(u"A database error has occurred.")'

        return 'Celery-{}-{}'.format(
            entry.get('kubernetes').get('container_name'),
            exception,
        )

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        exception = entry.get('exception')
        queue = entry.get('kubernetes').get('container_name')
        task_id = entry.get('task_id')

        description = self.REPORT_TEMPLATE.format(
            queue=queue,
            error=entry.get('exception'),
            details=json.dumps(entry, indent=True),
            flower_link='http://celery-flower.{dc}.k8s.wikia.net/task/{task_id}'.format(
                dc=entry.get('datacenter').lower(), task_id=task_id)
        ).strip()

        report = Report(
            summary='Celery worker {} reported: {}'.format(queue, exception),
            description=description,
            label=self.REPORT_LABEL
        )

        report.add_label(queue)

        return report
