import logging
import re
import yaml

from reporter.sources import PandoraErrorsSource, MercurySource, HeliosSource, ChatLogsSource, \
    PHPExecutionTimeoutSource, BackendSource


class ClassifierConfig(object):
    """
    Wraps access to YAML files in config directory
    """
    CLASSIFIER_CONFIG_DIR = 'reporter/classifier/config/'

    def __init__(self):
        self._config = {}

        for section in ['components', 'paths']:
            with open('{}{}.yaml'.format(self.CLASSIFIER_CONFIG_DIR, section), mode='r') as fp:
                self._config[section] = yaml.load(fp)[section]

    def __getitem__(self, item):
        """
        :type item str
        :rtype: dict
        """
        return self._config.get(item)


class Classifier(object):
    """
    Pick a correct JIRA project and component based on report type and content
    """
    PROJECT_MAIN = 'MAIN'
    PROJECT_SER = 'SER'
    PROJECT_COMMUNITY_TECHNICAL = 'CT'
    PROJECT_ERROR_REPORTER = 'ER'

    def __init__(self, config=ClassifierConfig()):
        self._logger = logging.getLogger(self.__class__.__name__)

        self._components = config['components']
        self._paths = config['paths']

    def get_component_id(self, component_name):
        """
        :type component_name str
        :rtype: int
        """
        return int(self._components.get(component_name, 0)) or None

    def classify(self, report):
        """
        :type report reporter.reports.Report
        :rtype: list
        """
        # classify using labels added by the report
        labels = report.get_labels()

        if HeliosSource.REPORT_LABEL in labels:
            return self.PROJECT_MAIN, self.get_component_id('Helios')

        if MercurySource.REPORT_LABEL in labels:
            return self.PROJECT_MAIN, self.get_component_id('Mercury')

        # we want Pandora services-related issues to be reported to ER project
        # and let Jira move it to an appropriate project based on label
        if PandoraErrorsSource.REPORT_LABEL in labels:
            return self.PROJECT_ERROR_REPORTER, None

        if ChatLogsSource.REPORT_LABEL in labels:
            return self.PROJECT_MAIN, self.get_component_id('Chat')

        if BackendSource.REPORT_LABEL in labels:
            return self.PROJECT_MAIN, self.get_component_id('Backend Scripts')

        if PHPExecutionTimeoutSource.REPORT_LABEL in labels:
            # no component specified for this project
            return self.PROJECT_COMMUNITY_TECHNICAL, None

        # classify using the report content and the paths inside it (always report to MAIN)
        description = report.get_description()

        # get the backtrace entries
        backtrace_entries = re.findall(r'^\*\s?([^:]+):\d+', description, flags=re.MULTILINE)

        # use the ticket description as a fallback when there's no backtrace
        if not backtrace_entries:
            backtrace_entries = [description]

        # scan them from top
        for backtrace_entry in backtrace_entries:
            for path, component_name in self._paths.iteritems():
                if path in backtrace_entry:
                    self._logger.info('Found "{}" in ticket\'s description, setting "{}" component'.
                                      format(path, component_name))
                    return self.PROJECT_MAIN, self.get_component_id(component_name)

        return None
