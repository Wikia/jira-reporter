#!/usr/bin/env python
"""
This script is a sandbox for testing new sources
"""
import logging
from reporter.sources import KilledDatabaseQueriesSource

logging.basicConfig(level=logging.INFO)

reports = list()

source = KilledDatabaseQueriesSource()
reports += source.query(threshold=0)

for report in reports:
    print report
