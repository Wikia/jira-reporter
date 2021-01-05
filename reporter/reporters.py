# -*- coding: utf-8 -*-
"""
Contains handling of different services that reports can be sent to
"""
import json
import logging
import time
import datetime

from dateutil.parser import parse
from dateutil.tz import tzutc

from jira.client import JIRA

from .config import JIRA_CONFIG
from reporter.classifier import Classifier


class Jira(object):
    """
    Send reports to Jira

    @see http://jira-python.readthedocs.org/en/latest/
    """

    JQL = "description ~ '{hash_value}' AND project = 'ER'"

    REOPEN_AFTER_DAYS = 14  # reopen still valid tickets when they were closed X days ago
    REOPEN_TRANSITION_COMMENT = '[~{assignee}], I reopened this ticket - logs say it is still valid'

    STATUS_CLOSED = "Closed"
    RESOLUTION_WONT_FIX = "Won't Fix"
    RESOLUTION_DUPLICATE = "Duplicate"

    def __init__(self):
        self._logger = logging.getLogger('Jira')
        self._jira = JIRA(
            server=JIRA_CONFIG['url'],
            basic_auth=(JIRA_CONFIG['user'], JIRA_CONFIG['password'])
        )

        self._fields = JIRA_CONFIG.get('fields')
        self._last_seen_field = self._fields['custom']['last_seen']

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

        :type unique_id str
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

                # PLATFORM-2441: set "ER Date" to indicate when was the last time this ticket was still valid
                try:
                    # SUS-1168: do not update ER date for tickets closed as "Won't Fix" or "Duplicate"
                    if str(fields.resolution) != self.RESOLUTION_WONT_FIX and \
                            str(fields.resolution) != self.RESOLUTION_DUPLICATE:
                        self._logger.info('Updating ER date')
                        ticket.update(fields={
                            self._last_seen_field: self.get_today_timestamp()
                        })
                except Exception:
                    self._logger.error('Failed to update "ER Date" field ({})'.
                                       format(self._last_seen_field), exc_info=True)

                # SUS-1134: the ticket was closed (but not as "Won't Fix" or "Duplicate") over X days ago,
                # but it's still valid -> reopen it
                if str(fields.status) == self.STATUS_CLOSED and \
                        str(fields.resolution) != self.RESOLUTION_WONT_FIX and \
                        str(fields.resolution) != self.RESOLUTION_DUPLICATE:
                    if self._ticket_is_older_than(ticket, days=self.REOPEN_AFTER_DAYS):
                        self._logger.info('Going to reopen {id} - it is still valid'.format(id=ticket.key))

                        # get transition ID for Open status, it varies between projects
                        transitions = {}

                        for transition in self.get_api_client().transitions(issue=ticket):
                            transitions[transition['name']] = transition['id']

                        # reopen and comment the ticket
                        try:
                            self.get_api_client().transition_issue(
                                issue=ticket,
                                transitionId=transitions['Open']
                            )

                            self.get_api_client().add_comment(
                                issue=ticket,
                                body=self.REOPEN_TRANSITION_COMMENT.format(
                                    assignee=fields.assignee.name if fields.assignee else 'Unassigned'
                                )
                            )
                        except Exception:
                            self._logger.error('Failed to reopen {}'.format(ticket), exc_info=True)

            return True
        else:
            return False

    @staticmethod
    def get_today_timestamp():
        """
        Get today's timestamp for Jira's date picker custom field

        :rtype: str
        """
        return time.strftime('%Y-%m-%d')  # e.g. 2016-09-27

    def _ticket_is_older_than(self, ticket, days):
        """
        :type ticket jira.resources.Issue
        :type days int
        :rtype: bool
        """
        resolution_threshold = datetime.datetime.now(tz=tzutc()) - datetime.timedelta(days=days)
        try:
            resolution_date = parse(ticket.raw['fields'].get('resolutiondate'))
        except:
            self._logger.error('Failed to get the resolution date for {}'.format(ticket), exc_info=True)
            resolution_date = None

        return resolution_date is not None and resolution_date < resolution_threshold

    def report(self, report):
        """
        Send given report to JIRA

        It checks if it hasn't been reported already

        :type report reporter.reports.Report
        """
        self._logger.info('Reporting "{}"'.format(report.get_summary()))

        priority = report.get_priority()
        if priority:
            self._fields['default']['priority'] = priority

        # let's first check if the report is already in JIRA
        # use "hash" added to a ticket description
        try:
            if self.ticket_exists(report.get_unique_id()):
                return False
        except Exception:
            self._logger.error('Failed to look up ticket duplicates', exc_info=True)
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

        # set default fields as defined in the config.py
        ticket_dict.update(self._fields['default'])

        # PLATFORM-2405: classify the report: set a proper project and component
        (project, component_id) = None, None

        classification = self._classifier.classify(report)

        if classification:
            (project, component_id) = classification

        # we do not want to file tickets in MAIN project anymore
        if project == self._classifier.PROJECT_MAIN:
            self._logger.info('MAIN tickets are now skipped')
            return False

        if project:
            ticket_dict['project']['key'] = project
            # overwrite default fields with project specific ones
            ticket_dict.update(self._fields.get(project, {}))

        if component_id:
            ticket_dict['components'] = [{'id': str(component_id)}]  # "expected 'id' property to be a string"

        # PLATFORM-2441: set "ER Date" to indicate when was the last time this ticket was still valid
        ticket_dict[self._last_seen_field] = self.get_today_timestamp()

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
