"""
Base source for Kubernetes stuff
"""
import re
import urllib

from reporter.sources.common import KibanaSource


class KubernetesSource(KibanaSource):
    """
    An abstract class for sources querying logstash-k8s-event-logger index
    """
    REPORT_TEMPLATE = """
{message}:

h3. Details

{{code:json}}
{details}
{{code}}

*Kubernetes dashboard link*: {dashboard_link}
    """

    REPORT_LABEL = 'k8s'

    ELASTICSEARCH_INDEX_PREFIX = 'logstash-k8s-event-logger'

    EVENT_MESSAGE = False

    def _get_entries(self, query):
        """ Return entries matching given query """
        assert self.EVENT_MESSAGE is not False, 'You need to specif EVENT_MESSAGE in your class'

        return self._kibana.query_by_string(
            query='eventMessage: "{}" AND  kubernetes.namespace_name: "prod"'.format(self.EVENT_MESSAGE),
            limit=self.LIMIT
        )

    def _filter(self, entry):
        return True

    def _normalize(self, entry):
        assert self.EVENT_MESSAGE is not False, 'You need to specif EVENT_MESSAGE in your class'

        # normalize using "involvedObject.name" field, e.g. sla-report-comdev-1542331800
        involved_object_name = entry.get('involvedObject', {}).get('name', '')
        involved_object_name = re.sub(r'-\d+', '', involved_object_name)

        return 'k8s-{}-{}'.format(
            str(self.EVENT_MESSAGE).replace(' ', '-').lower(),
            involved_object_name,
        )

    def _get_report(self, entry):
        raise NotImplementedError("_get_report() method needs to be overwritten in your class!")

    @staticmethod
    def get_dashboard_link(query):
        return 'https://dashboard.sjc.k8s.wikia.net:30080/#!/search?namespace=prod&q={}'.\
            format(urllib.quote(query))
