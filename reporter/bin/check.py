#!/usr/bin/env python
"""
This script checks PHP log for fatals, warnings, DB queries errors
and reports issues to JIRA when given thresholds are reached
"""
import logging

from time import sleep

from reporter.reporters import Jira
from reporter.sources import PHPErrorsSource, PHPExceptionsSource, DBQueryErrorsSource,\
    DBQueryNoLimitSource, NotCachedWikiaApiResponsesSource, KilledDatabaseQueriesSource, \
    PHPAssertionsSource, PandoraErrorsSource, PHPSecuritySource, \
    MercurySource, HeliosSource, VignetteThumbVerificationSource, AnemometerSource, \
    ChatLogsSource, PHPExecutionTimeoutSource, BackendSource, PHPTriggeredSource, \
    IndexDigestSource, ReportsPipeSource, PHPTypeErrorsSource, \
    CeleryLogsSource, KubernetesBackoffSource, UCPErrorsSource

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-35s %(levelname)-8s %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)

# get reports from various sources
reports = []

# PHP warnings and errors
source = PHPErrorsSource()

reports += source.query("PHP Fatal Error", threshold=5)
reports += source.query("PHP Catchable Fatal", threshold=5)
reports += source.query("PHP Warning", threshold=50)
reports += source.query("PHP Strict Standards", threshold=200)
reports += source.query("PHP Notice", threshold=1500)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/Severity%20error
reports += PHPExceptionsSource().query(query='error', threshold=50)
reports += PHPExceptionsSource().query(query='critical', threshold=0)  # PLATFORM-2271

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/DBQuery%20errors
reports += DBQueryErrorsSource().query(threshold=20)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-836
reports += DBQueryNoLimitSource().query(threshold=50)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/wikia.php%20caching%20disabled
reports += NotCachedWikiaApiResponsesSource().query(threshold=500)  # we serve 75k not cached responses an hour

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/drozdo.pt-kill
reports += KilledDatabaseQueriesSource().query(threshold=5)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/AssertionException
reports += PHPAssertionsSource().query(threshold=5)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-1420
reports += PandoraErrorsSource().query(threshold=50)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-1540
reports += PHPSecuritySource().query(threshold=0)  # security problems is always important

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-2055
reports += MercurySource().query('emergency', threshold=0)
reports += MercurySource().query('error', threshold=50)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/Helios%20errors
reports += HeliosSource().query(threshold=5)

# @see https://kibana.wikia-inc.com/index.html#/dashboard/elasticsearch/Vigniette%20Thumb%20Verifier
reports += VignetteThumbVerificationSource().query(threshold=5)

# @see https://wikia-inc.atlassian.net/browse/PLATFORM-2180
reports += AnemometerSource().query(threshold=0)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/Chat%20Server%20errors
reports += ChatLogsSource().query('uncaughtException', threshold=1)
reports += ChatLogsSource().query('SyntaxError', threshold=1)

reports += PHPExecutionTimeoutSource(period=21600).query(threshold=5)

reports += BackendSource().query(threshold=2)

reports += PHPTriggeredSource().query(threshold=1)

reports += IndexDigestSource().query(threshold=1)

reports += ReportsPipeSource().query(threshold=1)

reports += PHPTypeErrorsSource().query(threshold=5)

reports += CeleryLogsSource().query(threshold=5)

reports += KubernetesBackoffSource().query(threshold=1)

reports += UCPErrorsSource().query()

logging.info('Reporting {} issues...'.format(len(reports)))
reporter = Jira()

reported = 0
for report in reports:
    sleep(1)  # avoid hitting Jira with too many searches for ticket hash (we perform 150+ of them)

    if reporter.report(report):
        reported += 1

logging.info('Reported {} tickets'.format(reported))
