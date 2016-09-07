# -*- coding: utf-8 -*-
"""
Contains handling of different services that reports can be sent to
"""
import json
import logging

from jira.client import JIRA

from .config import JIRA_CONFIG
from reporter.classifier import Classifier


class Jira(object):
    """
    Send reports to Jira

    @see http://jira-python.readthedocs.org/en/latest/
    """

    JQL = "description ~ '{hash_value}'"

    def __init__(self):
        self._logger = logging.getLogger('Jira')
        self._jira = JIRA(server=JIRA_CONFIG['url'], basic_auth=[JIRA_CONFIG['user'], JIRA_CONFIG['password']])

        self._fields = JIRA_CONFIG.get('fields')
        self._project = JIRA_CONFIG.get('project')
        self._server = self._jira.client_info()

        self._classifier = Classifier()

        self._logger.info("Using {} project on <{}>".format(self._project, self._server))

    def get_api_client(self):
        return self._jira

    def _get_issue_url(self, issue_id):
        return '{server}/browse/{issue_id}'.format(server=self._server, issue_id=issue_id)

    def ticket_exists(self, unique_id):
        """
        Checks if ticket with a given unique_id exists
        """
        self._logger.info('Checking {} unique ID...'.format(unique_id))
        tickets = self._jira.search_issues(
            self.JQL.format(hash_value=unique_id)
        )

        if len(tickets) > 0:
            self._logger.info('Found {} ticket(s)'.format(len(tickets)))

            for ticket in tickets:
                fields = ticket.fields

                self._logger.info('<{url}> {assignee} ({status})'.format(
                    id=ticket.key,
                    url=ticket.permalink(),
                    assignee=fields.assignee.displayName.encode('utf8') if fields.assignee else None,  # e.g. Jan Ęąwski
                    status=fields.resolution or fields.status  # Done / In Progress / Won't Fix / ...
                ))

            return True
        else:
            return False

    def report(self, report):
        """
        Send given report to JIRA

        It checks if it hasn't been reported already

        :type report reporter.reports.Report
        """
        self._logger.info('Reporting "{}"'.format(report.get_summary()))

        # let's first check if the report is already in JIRA
        # use "hash" added to a ticket description
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
            "labels": report.get_labels()
        }

        # PLATFORM-2405: classify the report: set a proper project and component
        classification = self._classifier.classify(report)

        if classification:
            (project, component_id) = classification

            ticket_dict['project']['key'] = project
            ticket_dict['components'] = [{'id': str(component_id)}]  # "expected 'id' property to be a string"

        # set default fields as defined in the config.py
        ticket_dict.update(self._fields['default'])

        # set custom fields
        if report.get_url() is not False:
            # "The entered text is too long. It exceeds the allowed limit of 255 characters."
            ticket_dict[self._fields['custom']['url']] = report.get_url()[:250]

        # report the ticket
        self._logger.info('Reporting {}'.format(json.dumps(ticket_dict)))

        try:
            new_issue = self._jira.create_issue(fields=ticket_dict)
            issue_id = new_issue.key

            self._logger.info('Reported <{}>'.format(self._get_issue_url(issue_id)))
        except Exception:
            self._logger.error('Failed to report a ticket', exc_info=True)
            return False

        return True
