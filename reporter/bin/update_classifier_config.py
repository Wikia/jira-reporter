"""
This maintenace script is used to update Component name to Component ID mapping for tickets classifier

It uses https://fandom.atlassian.net/rest/api/2/project/MAIN/components API call

Run it via "make update_classifier_config" from the base directory of this repository
"""
import csv
import logging
import yaml

from reporter.classifier import ClassifierConfig
from reporter.reporters import Jira

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-35s %(levelname)-8s %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)

CLASSIFIER_CONFIG_DIR = 'reporter/classifier/config/'
YAML_HEADER = '# This file was auto-generated by "make update_classifier_config"\n'

logger = logging.getLogger(__name__)


def _write_to_yaml(name, data):
    """
    :type name str
    :type data dict
    """
    with open('{}{}.yaml'.format(ClassifierConfig.CLASSIFIER_CONFIG_DIR, name), mode='w') as fp:
        fp.write(YAML_HEADER)

        yaml.dump({name: data}, fp, default_flow_style=False)
        logger.info('{} generated (with {} items)'.format(fp.name, len(data.keys())))


def update_components_mapping():
    """
    Generate reporter/classifier/components.yaml with components mapping for MAIN project
    """
    jira_api = Jira().get_api_client()

    components = {}

    for component in jira_api.project_components('MAIN') + jira_api.project_components('SER'):
        components[str(component.name.strip())] = int(component.id)

    _write_to_yaml('components', components)

    return components


def update_paths_mapping(components):
    """
    Generate reporter/classifier/paths.yaml with extensions / source code paths to component names mapping
    """
    paths = {}

    files = {
        'core.csv': '/',
        'extensions.csv': '/extensions/wikia/',
    }

    for csv_file, path_prefix in files.items():
        with open(CLASSIFIER_CONFIG_DIR + csv_file, mode='r') as fp:
            reader = csv.reader(fp)

            # skip the CSV header
            next(reader)

            for line in reader:
                (extension_name, component_name) = line

                if component_name != '':
                    if component_name not in components:
                        raise Exception("'{}' component is not defined in Jira, please update your CSV file:\n{}".format(component_name, line))

                    paths['{}{}'.format(path_prefix, extension_name)] = component_name

    _write_to_yaml('paths', paths)


if __name__ == '__main__':
    components = update_components_mapping()
    update_paths_mapping(components)
