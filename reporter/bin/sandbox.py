#!/usr/bin/env python
"""
This script is a sandbox for testing new sources
"""
import logging
from reporter.sources import KilledDatabaseQueriesSource, PHPErrorsSource, \
    DBQueryNoLimitSource, DBQueryErrorsSource, PHPAssertionsSource, PHPExceptionsSource, \
    PandoraErrorsSource, PHPSecuritySource, PhalanxSource, MercurySource, HeliosSource,AnemometerSource

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-35s %(levelname)-8s %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)

reports = list()

#source = PHPErrorsSource()
#reports += source.query("PHP Fatal Error", threshold=5)
#reports += source.query("PHP Notice", threshold=2000)

#source = KilledDatabaseQueriesSource()
#reports += source.query(threshold=0)

#source = DBQueryNoLimitSource()
#reports += source.query(threshold=50)

#source = DBQueryErrorsSource()
#reports += source.query(threshold=2)

#source = PHPAssertionsSource()
#reports += source.query(threshold=5)

#reports += PandoraErrorsSource().query(threshold=5)

#reports += PHPExceptionsSource().query(query='error', threshold=50)
#reports += PHPExceptionsSource().query(query='critical', threshold=0)

#reports += PHPSecuritySource().query(threshold=0)

#reports += PhalanxSource().query(threshold=5)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-2055
#reports += MercurySource().query('fatal', threshold=0)
#reports += MercurySource().query('error', threshold=50)

# @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/Helios%20errors
#reports += HeliosSource().query(threshold=0)

# @see https://wikia-inc.atlassian.net/browse/PLATFORM-2180
reports += AnemometerSource().query(threshold=0)

for report in reports:
    print report
