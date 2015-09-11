"""
A report wrapper
"""


class Report(object):
    """ A report wrapper """

    def __init__(self, summary, description, label=False):
        """ Set up the report """
        self._summary = summary
        self._description = description

        self._labels = list()
        if label:
            self.add_label(label)

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
        # prevent jira.exceptions.JIRAError: HTTP 400: "The summary is invalid because it contains newline characters."
        return self._summary.replace("\n", '')

    def get_description(self):
        """ Get report detailed description """
        return self._description

    def add_label(self, label):
        """ Add given label to the report """
        self._labels.append(label)

    def get_labels(self):
        """ Get report labels """
        return self._labels

    def __repr__(self):
        """ Returns human readable representation of the object """
        return '<Report: {summary} [{labels}] ({unique_id})>\n{description}'.format(
            summary=self.get_summary(),
            labels=']['.join(self.get_labels()),
            unique_id=self.get_unique_id(),
            description=self.get_description()
        )
