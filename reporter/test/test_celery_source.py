"""
Set of unit tests for CeleryLogsSource
"""
import unittest

from ..sources import CeleryLogsSource


class CeleryLogsSourceTestClass(unittest.TestCase):
    ENTRY = {
        "syslog_timestamp": "2018-10-04 13:17:56,211",
        "event": "Task failed",
        "datacenter": "SJC",
        "exception_type": "RemoteExecuteError",
        "es_index": "celery",
        "@timestamp": "2018-10-04T13:17:56.211Z",
        "tags": [
            "json"
        ],
        "kubernetes": {
            "pod_name": "celery-mediawiki-main-58754999c5-rcp5g",
            "master_url": "https://10.220.0.1:443/api",
            "namespace_id": "29f07d84-1eb7-11e7-95d6-525400146bee",
            "labels": {
                "app": "celery-mediawiki-main",
                "pod-template-hash": "1431055571"
            },
            "namespace_name": "prod",
            "container_name": "mediawiki-main",
            "cluster_name": "kube-sjc-prod",
            "pod_id": "156b5bd8-c7a5-11e8-8105-525400702077",
            "namespace_annotations": {
                "kubectl_kubernetes_io/last-applied-configuration": "{\"apiVersion\":\"v1\",\"kind\":\"Namespace\",\"metadata\":{\"annotations\":{},\"name\":\"prod\",\"namespace\":\"\"},\"spec\":{\"finalizers\":[\"kubernetes\"]}}\n"
            },
            "host": "k8s-worker-s21"
        },
        "exception": "RemoteExecuteError(u'Wikia\\\\SwiftSync\\\\ImageSyncTask::synchronize',)",
        "stream": "stderr",
        "docker": {
            "container_id": "c9334973842ce82ce13bd2604a33e61c788e4e3ea35f3b3f24a590cfe043f452"
        },
        "@version": "1",
        "task_id": "mw-F9D9236F-73CA-4608-9E98-BAFE2A7A9359"
    }

    """
    Unit tests for CeleryLogsSource class
    """
    def setUp(self):
        self._source = CeleryLogsSource()

    def test_normalize(self):
        assert self._source._normalize(self.ENTRY) == "Celery-mediawiki-main-RemoteExecuteError(u'Wikia\\\\SwiftSync\\\\ImageSyncTask::synchronize',)"
        assert self._source._normalize({
            "kubernetes": {
                "container_name": "mediawiki-main",
            },
            "exception": "RemoteExecuteError(u\"A database error has occurred.  Did you forget to run maintenance/update.php after upgrading?  See: https://www.mediawiki.org/wiki/Manual:Upgrading#Run_the_update_script\nQuery: UPDATE  `city_list` SET city_last_timestamp = '20181008181837' WHERE city_id = '658996'\nFunction: UpdateCityListTask::updateLastTimestamp\nError: 1205 Lock wait timeout exceeded; try restarting transaction (geo-db-sharedb-master.query.consul)\n\",)"
        }) == 'Celery-mediawiki-main-RemoteExecuteError(u"A database error has occurred.")'

    def test_report(self):
        report = self._source._get_report(self.ENTRY)

        desc = report.get_description()

        print(desc)

        assert 'Celery worker has reported the following error when processing *mediawiki-main* queue:' in desc
        assert '*Flower link*: http://celery-flower.sjc.k8s.wikia.net/task/mw-F9D9236F-73CA-4608-9E98-BAFE2A7A935' in desc

        assert "Celery worker mediawiki-main reported: RemoteExecuteError(u'Wikia\\\\SwiftSync\\\\ImageSyncTask::synchronize',)" == report.get_summary()
        assert ['CeleryWorkersError', 'mediawiki-main'] == report.get_labels()
