import json
import re

from reporter.sources.kubernetes.common import KubernetesSource
from reporter.reports import Report


class KubernetesBackoffSource(KubernetesSource):
    """
    Report jobs that got "Job has reached the specified backoff limit"

    @see SUS-6261
    """
    REPORT_LABEL = 'k8s-backoff-limit'

    # eventMessage to query for
    EVENT_MESSAGE = 'Job has reached the specified backoff limit'

    def _get_report(self, entry):
        """
        Format the report to be sent to JIRA

        :type entry dict
        :rtype: dict
        """
        involved_object_name = entry.get('involvedObject', {}).get('name', '')
        involved_object_name = re.sub(r'-\d+', '', involved_object_name)

        description = self.REPORT_TEMPLATE.format(
            message='"{}" has been reported for {}'.format(self.EVENT_MESSAGE, involved_object_name),
            details=json.dumps(entry, indent=True),
            dashboard_link=self.get_dashboard_link(query=involved_object_name)
        ).strip()

        report = Report(
            summary='Job {} has reached the specified backoff limit'.format(involved_object_name),
            description=description,
            label=self.REPORT_LABEL
        )

        report.add_label(KubernetesSource.REPORT_LABEL)

        return report
