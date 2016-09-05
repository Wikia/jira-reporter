"""
This maintenace script is used to update Component name to Component ID mapping for tickets classifier

It uses https://wikia-inc.atlassian.net/rest/api/2/project/MAIN/components API call
"""
import logging
import yaml

from reporter.reporters import Jira

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-35s %(levelname)-8s %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)


def update_components_mapping():
    """
    Generate reporter/classifier/components.yaml with components mapping for MAIN project
    """
    logger = logging.getLogger('update_components_mapping')

    jira_api = Jira().get_api_client()

    components = {}

    for component in jira_api.project_components('MAIN'):
        components[str(component.name.strip())] = int(component.id)

    with open('reporter/classifier/components.yaml', mode='w') as fp:
        data = {
            'components': components
        }

        yaml.dump(data, fp, default_flow_style=False)
        logger.info('{} generated'.format(fp.name))


def update_extensions_mapping():
    """
    Generate reporter/classifier/extensions.yaml with extensions / source code path to component name mapping
    """
    pass


if __name__ == '__main__':
    update_components_mapping()
    update_extensions_mapping()
