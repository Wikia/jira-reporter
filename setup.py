from setuptools import setup, find_packages

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
    packages=find_packages(include=['reporter', 'reporter.*']),
    install_requires=[
        'jira==3.10.5',
        'pytest==9.2.0',
        'pylint==4.1.3',
        'requests-oauthlib==1.3.0',
        'wikia-common-kibana==2.2.7',
        'PyYAML==6.0.1',
    ],
    include_package_data=True,
)