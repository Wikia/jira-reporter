from setuptools import setup

from reporter import __version__

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='reporter',
    version=__version__,
    description='Automated JIRA reporting of various errors and issues found in logs',
    long_description=long_description,
    url='https://github.com/Wikia/jira-reporter',
    author='macbre',
    author_email='macbre@wikia-inc.com',
    install_requires=[
        'jira==2.0.0',
        'pytest==3.6.3',
        'requests-oauthlib==0.6.1',
        'wikia-common-kibana==2.2.6',
        'PyYAML==3.13',
    ],
    include_package_data=True,
)
