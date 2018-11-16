"""
Set of unit tests for k8s' KubernetesBackoffSource
"""
import unittest

from ..sources import KubernetesBackoffSource


class KubernetesBackoffSourceTestClass(unittest.TestCase):
    """
    Unit tests for KubernetesBackoffSource class
    """

    ENTRY = {
        "source": {
            "component": "job-controller"
        },
        "involvedObject": {
            "kind": "Job",
            "resourceVersion": "396944026",
            "name": "mw-cj-lyricwiki-crawler-1542189600",
            "uid": "12520cf1-e7f4-11e8-9529-525400c7a681",
            "namespace": "prod",
            "apiVersion": "batch/v1"
        },
        "datacenter": "SJC",
        "@timestamp": "2018-11-14T11:43:58.000Z",
        "apiVersion": "v1",
        "reportingComponent": "",
        "kubernetes": {
            "master_url": "https://10.220.0.1:443/api",
            "cluster_name": "kube-sjc-prod",
            "host": "k8s-worker-s15",
            "namespace_id": "0e6cd6ef-d657-11e6-8cc2-525400146bee",
            "labels": {
            "pod-template-hash": "1743839742",
            "app": "k8s-event-logger"
        },
        "container_name": "k8s-event-logger",
        "namespace_name": "ops",
        "pod_name": "k8s-event-logger-5c87d7fc86-6cszf",
        "pod_id": "f8d1ddf5-bffa-11e8-8436-525400c7a681",
        "namespace_annotations": {
            "kubectl_kubernetes_io/last-applied-configuration": "{\"apiVersion\":\"v1\",\"kind\":\"Namespace\",\"metadata\":{\"annotations\":{},\"name\":\"ops\",\"namespace\":\"\"},\"spec\":{\"finalizers\":[\"kubernetes\"]}}\n"
        }
        },
        "tags": [],
        "eventType": "Warning",
        "eventMessage": "Job has reached the specified backoff limit",
        "docker": {
            "container_id": "64511926f13d5b6dc3223d1eb115d658e729e09437c7b55fa451cd8f0c40f255"
        },
        "metadata": {
            "resourceVersion": "396969060",
            "name": "mw-cj-lyricwiki-crawler-1542189600.1566f79d91ad3392",
            "uid": "0d492cdf-e7fa-11e8-9529-525400c7a681",
            "creationTimestamp": "2018-11-14T10:42:58Z",
            "namespace": "prod",
            "selfLink": "/api/v1/namespaces/prod/events/mw-cj-lyricwiki-crawler-1542189600.1566f79d91ad3392"
        },
        "reason": "BackoffLimitExceeded",
        "lastTimestamp": "2018-11-14T10:42:58Z",
        "stream": "stdout",
        "reportingInstance": "",
        "firstTimestamp": "2018-11-14T10:42:58Z",
        "count": 1,
        "es_index": "k8s-event-logger",
        "kind": "Event",
        "@version": "1",
        "eventTime": None
    }

    def setUp(self):
        self._source = KubernetesBackoffSource()

    def test_normalize(self):
        assert self._source._normalize(self.ENTRY) == "k8s-job-has-reached-the-specified-backoff-limit-mw-cj-lyricwiki-crawler"
        assert self._source._normalize({
            "involvedObject": {
                "name": "foo-bar-12345",
            }
        }) == 'k8s-job-has-reached-the-specified-backoff-limit-foo-bar'

    def test_report(self):
        report = self._source._get_report(self.ENTRY)

        desc = report.get_description()

        print(desc)

        assert '"Job has reached the specified backoff limit" has been reported for mw-cj-lyricwiki-crawler:' in desc
        assert '*Kubernetes dashboard link*: https://dashboard.sjc.k8s.wikia.net:30080/#!/search?namespace=prod&q=mw-cj-lyricwiki-crawler' in desc

        assert "Job mw-cj-lyricwiki-crawler has reached the specified backoff limit" == report.get_summary()
        assert ['k8s-backoff-limit', 'k8s'] == report.get_labels()
