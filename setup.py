from setuptools import setup

from reporter import __version__

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='reporter',
    version=__version__,
    description='Automated JIRA reporting of PHP fatal errors',
    long_description=long_description,
    url='https://github.com/Wikia/jira-reporter',
    author='macbre',
    author_email='macbre@wikia-inc.com',
    install_requires=[
        'jira==0.32',
        'pytest==2.6.4',
        'requests-oauthlib==0.4.2',
        'wikia.common.kibana==1.0.0'
    ],
    include_package_data=True,
)