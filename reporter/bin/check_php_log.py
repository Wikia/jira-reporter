#!/usr/bin/env python
"""
This script checks PHP log for fatals, warnings, DB queries errors
and reports issues to JIRA when given thresholds are reached
"""
import logging

from reporter.reporters import Jira
from reporter.sources import PHPErrorsSource, DBQueryErrorsSource

logging.basicConfig(level=logging.INFO)

# get reports from various sources
reports = []

# PHP warnings and errors
source = PHPErrorsSource()
reports += source.query("PHP Fatal Error", threshold=5)
reports += source.query("PHP Warning", threshold=50)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/DBQuery%20errors
source = DBQueryErrorsSource()
reports += source.query(threshold=5)


logging.info('Reporting {} issues...'.format(len(reports)))
reporter = Jira()

reported = 0
for report in reports:
    if reporter.report(report):
        reported += 1

logging.info('Reported {} tickets'.format(reported))
