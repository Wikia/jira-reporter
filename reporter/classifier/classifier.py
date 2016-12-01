import logging
import yaml

from reporter.sources import PandoraErrorsSource, PhalanxSource, MercurySource, HeliosSource, ChatLogsSource


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
            return self.PROJECT_SER, self.get_component_id('Helios')

        if MercurySource.REPORT_LABEL in labels:
            return self.PROJECT_MAIN, self.get_component_id('Mercury')

        if PandoraErrorsSource.REPORT_LABEL in labels:
            return self.PROJECT_SER, self.get_component_id('Pandora')

        if PhalanxSource.REPORT_LABEL in labels:
            return self.PROJECT_MAIN, self.get_component_id('Phalanx')

        if ChatLogsSource.REPORT_LABEL in labels:
            return self.PROJECT_MAIN, self.get_component_id('Chat')

        # classify using the report content and the paths inside it (always report to MAIN)
        description = report.get_description()

        for path, component_name in self._paths.iteritems():
            if path in description:
                self._logger.info('Found "{}" in ticket\'s description, setting "{}" component'.
                                  format(path, component_name))
                return self.PROJECT_MAIN, self.get_component_id(component_name)

        return None
