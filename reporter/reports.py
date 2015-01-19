"""
A report wrapper
"""


class Report(object):
    """ A report wrapper """

    def __init__(self, summary, description, label=False):
        """ Set up the report """
        self._summary = summary
        self._description = description
        self._label = label

        self._unique_id = False
        self._counter = False

    def set_unique_id(self, unique_id):
        """ Set the hash used to avoid duplicates reported to JIRA """
        self._unique_id = unique_id

    def get_unique_id(self):
        """ Get the hash """
        return self._unique_id

    def set_counter(self, counter):
        """ Set occurrences counter """
        self._counter = counter

    def get_counter(self):
        """ Get occurrences counter """
        return self._counter

    def get_summary(self):
        """ Get report title / summary """
        return self._summary

    def get_description(self):
        """ Get report detailed description """
        return self._description

    def get_label(self):
        """ Get report label """
        return self._label

    def __repr__(self):
        """ Returns human readable representation of the object """
        return '<Report: {summary} [{label}] ({unique_id})>\n{description}'.format(
            summary=self.get_summary(),
            label=self.get_label(),
            unique_id=self.get_unique_id(),
            description=self.get_description()
        )
