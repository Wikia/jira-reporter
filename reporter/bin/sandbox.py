#!/usr/bin/env python
"""
This script is a sandbox for testing new sources
"""
import logging
from reporter.sources import KilledDatabaseQueriesSource, PHPErrorsSource, DBQueryNoLimitSource, DBQueryErrorsSource

logging.basicConfig(level=logging.INFO)

reports = list()

source = KilledDatabaseQueriesSource()
reports += source.query(threshold=0)

source = PHPErrorsSource()
reports += source.query("PHP Fatal Error", threshold=5)

source = DBQueryNoLimitSource()
reports += source.query(threshold=50)

source = DBQueryErrorsSource()
reports += source.query(threshold=20)

for report in reports:
    print report
