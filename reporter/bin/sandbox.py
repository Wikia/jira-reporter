#!/usr/bin/env python
"""
This script is a sandbox for testing new sources
"""
import logging
from reporter.sources import KilledDatabaseQueriesSource, PHPErrorsSource, \
    DBQueryNoLimitSource, DBQueryErrorsSource, PHPAssertionsSource, PHPExceptionsSource, \
    PandoraErrorsSource

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-25s %(levelname)-8s %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)

reports = list()

"""
source = KilledDatabaseQueriesSource()
reports += source.query(threshold=0)

source = PHPErrorsSource()
reports += source.query("PHP Fatal Error", threshold=5)

source = DBQueryNoLimitSource()
reports += source.query(threshold=50)
"""

source = DBQueryErrorsSource()
reports += source.query(threshold=10)

"""
source = PHPAssertionsSource()
reports += source.query(threshold=5)

reports += PandoraErrorsSource().query(threshold=5)
"""

#reports += PHPExceptionsSource().query(threshold=50)

for report in reports:
    print report
