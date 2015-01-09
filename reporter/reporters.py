import logging

from jira.client import JIRA

from reporter.config import JIRA_CONFIG


class Jira(object):
    """ Send reports to Jira """
    def __init__(self):
        self._logger = logging.getLogger('Jira')
        self._jira = JIRA(server=JIRA_CONFIG['url'], basic_auth=[JIRA_CONFIG['user'], JIRA_CONFIG['password']])
        self._project = JIRA_CONFIG['project']

        self._logger.info("Using {} project on <{}>".format(self._project, self._jira.client_info()))

    def report(self, report):
        self._logger.info('Reporting "{}"'.format(report.get_summary()))
        self._logger.info('Checking {} hash...'.format(report.get_unique_id()))

