#!/usr/bin/env python
"""
This script is a sandbox for testing new sources
"""
import logging
from reporter.sources import NotCachedWikiaApiResponsesSource

logging.basicConfig(level=logging.DEBUG)

reports = list()

source = NotCachedWikiaApiResponsesSource()
reports += source.query(threshold=1000)  # we serve 90k not cached responses

for report in reports:
    print report
