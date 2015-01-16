import json
import logging

from jira.client import JIRA

from reporter.config import JIRA_CONFIG


class Jira(object):
    JQL = "project = '{project}' AND {hash_field} ~ '{hash_value}'"

    """ Send reports to Jira """
    def __init__(self):
        self._logger = logging.getLogger('Jira')
        self._jira = JIRA(server=JIRA_CONFIG['url'], basic_auth=[JIRA_CONFIG['user'], JIRA_CONFIG['password']])
        self._fields = JIRA_CONFIG.get('fields')
        self._project = JIRA_CONFIG.get('project')

        self._logger.info("Using {} project on <{}>".format(self._project, self._jira.client_info()))

    def ticket_exists(self, unique_id):
        """
        Checks if ticket with a given unique_id exists
        """
        self._logger.info('Checking {} unique ID...'.format(unique_id))
        tickets = self._jira.search_issues(
            self.JQL.format(project='ER', hash_field='report_hash', hash_value=unique_id)
        )

        if len(tickets) > 0:
            self._logger.info('Found {count} tickets: {tickets}'.format(
                count=len(tickets),
                tickets=', '.join([ticket.key for ticket in tickets])
            ))
            return True
        else:
            return False

    def report(self, report):
        self._logger.info('Reporting "{}"'.format(report.get_summary()))

        # let's first check if the report is already in JIRA
        # use "report_hash" custom field
        if self.ticket_exists(report.get_unique_id()):
            return False

        # it's not, create a ticket
        ticket_dict = {
            "project": {'key': self._project},
            "summary": report.get_summary()[:250],
            "description": report.get_description(),
            "labels": [report.get_label()]
        }

        # set default fields as defined in the config.py
        ticket_dict.update(self._fields['default'])

        # set report_hash field
        ticket_dict[self._fields['custom']['unique_id']] = report.get_unique_id()

        self._logger.info('Reporting {}'.format(json.dumps(ticket_dict)))
        new_issue = self._jira.create_issue(fields=ticket_dict)

        self._logger.info('Reported {}'.format(new_issue.key))
        return True
