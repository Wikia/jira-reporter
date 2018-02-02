from reporter.sources.common import KibanaSource
from reporter.reports import Report


class ReportsPipeSource(KibanaSource):
    """
    Get issues pushed to 'jira-reporter-pipe' es index

    @see https://github.com/Wikia/sus-dynks/tree/master/linters

    "report": {
      "title": "/extensions/wikia/Discussions/maintenance/enableDiscussionsWithNoForums.php script is not used",
      "message": "*{{/extensions/wikia/Discussions/maintenance/enableDiscussionsWithNoForums.php}}* is not used by app nor referenced in Chef\n\nDouble check app and chef repositories and consider removing this script.\n\nh3. First commit of this script in git\n\n{code}\ncommit 139c3dee14f4fbda971412a407ece37bc780430c\nAuthor: Garth Webb <garth@wikia-inc.com>\nDate:   Fri Dec 2 11:14:58 2016 -0800\n\n    Additional error condition for migration\n{code}\n\nhttps://github.com/Wikia/app/blob/dev/extensions/wikia/Discussions/maintenance/enableDiscussionsWithNoForums.php",
      "hash": "not-used-maintenance-scripts-/extensions/wikia/Discussions/maintenance/enableDiscussionsWithNoForums.php",
      "tags": [
        "not-used-maintenance-scripts"
      ]
    }

    """
    ELASTICSEARCH_INDEX_PREFIX = 'logstash-jira-reporter-pipe'

    # @see https://wikia-inc.atlassian.net/browse/SUS-3566
    # https://github.com/macbre/index-digest#syslog
    ELASTICSEARCH_QUERY = 'report.hash: *'

    def _get_entries(self, query):
        return self._kibana.query_by_string(query=self.ELASTICSEARCH_QUERY, limit=self.LIMIT)

    def _filter(self, entry):
        """
        Skip these reports for now
        """
        return True

    def _normalize(self, entry):
        """
        Normalize given entry
        """
        report = entry.get('report')
        return report.get('hash')

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        report = entry.get('report')

        _report = Report(
            summary=report.get('title'),
            description=report.get('message')
        )

        for label in report.get('tags', []):
            _report.add_label(label)

        return _report
