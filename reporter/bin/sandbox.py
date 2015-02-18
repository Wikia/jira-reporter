#!/usr/bin/env python
"""
This script is a sandbox for testing new sources
"""
import logging
from reporter.sources import PHPErrorsSource, DBQueryErrorsSource, DBQueryNoLimitSource

logging.basicConfig(level=logging.INFO)

reports = list()

source = DBQueryNoLimitSource()
reports += source.query()

for report in reports:
    print report
