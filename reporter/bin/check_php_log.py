#!/usr/bin/env python
"""
This script checks PHP log for fatals, warnings, DB queries errors
and reports issues to JIRA when given thresholds are reached
"""
import logging

from reporter.reporters import Jira
from reporter.sources import PHPErrorsSource, DBQueryErrorsSource, DBQueryNoLimitSource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
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

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/DBQuery%20errors
source = DBQueryErrorsSource()
reports += source.query('DBQueryError', threshold=20)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-836
source = DBQueryNoLimitSource()
reports += source.query()

logging.info('Reporting {} issues...'.format(len(reports)))
reporter = Jira()

reported = 0
for report in reports:
    if reporter.report(report):
        reported += 1

logging.info('Reported {} tickets'.format(reported))
