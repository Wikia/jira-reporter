#!/usr/bin/env python
"""
This script is a sandbox for testing new sources
"""
import logging
import json

from reporter.reporters import Jira
from reporter.sources import KilledDatabaseQueriesSource, PHPErrorsSource, \
    DBQueryNoLimitSource, DBQueryErrorsSource, PHPAssertionsSource, PHPExceptionsSource, \
    PandoraErrorsSource, PHPSecuritySource, MercurySource, HeliosSource, AnemometerSource, \
    ChatLogsSource, BackendSource, PHPTriggeredSource, IndexDigestSource, ReportsPipeSource, \
    PHPTypeErrorsSource, CeleryLogsSource, KubernetesBackoffSource, UCPErrorsSource

from reporter.classifier import Classifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-35s %(levelname)-8s %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)

reports = list()
classifier = Classifier()

#source = PHPErrorsSource()
#reports += source.query("PHP Fatal Error", threshold=5)
#reports += source.query("PHP Notice", threshold=2000)

# reports += KilledDatabaseQueriesSource().query(threshold=0)

#source = DBQueryNoLimitSource()
#reports += source.query(threshold=50)

# reports += DBQueryErrorsSource().query(threshold=2)

#source = PHPAssertionsSource()
#reports += source.query(threshold=5)

#reports += PandoraErrorsSource().query(threshold=5)

#reports += PHPExceptionsSource().query(query='error', threshold=50)
#reports += PHPExceptionsSource().query(query='critical', threshold=0)

#reports += PHPSecuritySource().query(threshold=0)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-2055
#reports += MercurySource().query('fatal', threshold=0)
#reports += MercurySource().query('error', threshold=50)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/Helios%20errors
#reports += HeliosSource().query(threshold=0)

# @see https://fandom.atlassian.net/browse/PLATFORM-2180
#reports += AnemometerSource().query(threshold=0)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/Chat%20Server%20errors
#reports += ChatLogsSource().query('uncaughtException', threshold=5)
#reports += ChatLogsSource().query('SyntaxError', threshold=5)

#reports += BackendSource().query(threshold=1)

#reports += PHPTriggeredSource().query(threshold=1)

#reports += IndexDigestSource().query(threshold=1)

#reports += ReportsPipeSource().query(threshold=1)

#reports += DBReadQueryOnMaster().query(threshold=1)

#reports += PHPTypeErrorsSource().query(threshold=5)

#reports += CeleryLogsSource().query(threshold=2)

#reports += KubernetesBackoffSource().query(threshold=2)

reports += UCPErrorsSource(period=60).query(threshold=5)

for report in reports:
    print(report)

    if report.get_priority():
        print("priority:" + json.dumps(report.get_priority()))

    print(classifier.classify(report))
