import logging
from jira import client, config


class Report(object):
    """
    issue_dict = {
        'project': {'key': 'PROJ'},
        'summary': 'New issue from jira-python',
        'description': 'Look into this one',
        'issuetype': {'name': 'Bug'},
    }

    @see http://jira-python.readthedocs.org/en/latest/
    """
    def __init__(self, summary, description):
        self._summary = summary
        self._description = description

        self._unique_id = False
        self._counter = False

    def set_unique_id(self, unique_id):
        self._unique_id = unique_id

    def get_unique_id(self):
        return self._unique_id

    def set_counter(self, counter):
        self._counter = counter

    def get_counter(self):
        return self._counter

    def get_summary(self):
        return self._summary

    def get_description(self):
        return self._description
