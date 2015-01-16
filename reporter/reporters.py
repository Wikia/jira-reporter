"""
Contains handling of different services that reports can be sent to
"""
import json
import logging

from jira.client import JIRA

from reporter.config import JIRA_CONFIG


class Jira(object):
    """
    Send reports to Jira

    @see http://jira-python.readthedocs.org/en/latest/
    """

    JQL = "{hash_field} ~ '{hash_value}' or summary ~ 'Hash: {hash_value}'"

    def __init__(self):
        self._logger = logging.getLogger('Jira')
        self._jira = JIRA(server=JIRA_CONFIG['url'], basic_auth=[JIRA_CONFIG['user'], JIRA_CONFIG['password']])

        self._fields = JIRA_CONFIG.get('fields')
        self._project = JIRA_CONFIG.get('project')
        self._server = self._jira.client_info()

        self._logger.info("Using {} project on <{}>".format(self._project, self._server))

    def _get_issue_url(self, issue_id):
        return '{server}/browse/{issue_id}'.format(server=self._server, issue_id=issue_id)

    def ticket_exists(self, unique_id):
        """
        Checks if ticket with a given unique_id exists
        """
        self._logger.info('Checking {} unique ID...'.format(unique_id))
        tickets = self._jira.search_issues(
            self.JQL.format(project='ER', hash_field='report_hash', hash_value=unique_id)
        )

        if len(tickets) > 0:
            self._logger.info('Found {count} tickets: <{tickets}>'.format(
                count=len(tickets),
                tickets='>, <'.join([self._get_issue_url(ticket.key) for ticket in tickets])
            ))
            return True
        else:
            return False

    def report(self, report):
        """
        Send given report to JIRA

        It checks if it hasn't been reported already
        """
        self._logger.info('Reporting "{}"'.format(report.get_summary()))

        # let's first check if the report is already in JIRA
        # use "report_hash" custom field
        if self.ticket_exists(report.get_unique_id()):
            return False

        # add a hash and counter
        description = report.get_description().strip()

        description += '\n\n========================\nHash: {hash}\nOccurrences: {counter} in the last hour'.format(
            hash=report.get_unique_id(), counter=report.get_counter()
        )

        # it's not, create a ticket
        ticket_dict = {
            "project": {'key': self._project},
            "summary": report.get_summary()[:250],
            "description": description,
            "labels": [report.get_label()]
        }

        # set default fields as defined in the config.py
        ticket_dict.update(self._fields['default'])

        # set report_hash field
        ticket_dict[self._fields['custom']['unique_id']] = report.get_unique_id()

        # report the ticket
        self._logger.info('Reporting {}'.format(json.dumps(ticket_dict)))

        new_issue = self._jira.create_issue(fields=ticket_dict)
        issue_id = new_issue.key

        self._logger.info('Reported <{}>'.format(self._get_issue_url(issue_id)))
        return True
