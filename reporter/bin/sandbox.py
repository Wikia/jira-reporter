#!/usr/bin/env python
"""
This script is a sandbox for testing new sources
"""
import logging
from reporter.sources import NotCachedWikiaApiResponsesSource

logging.basicConfig(level=logging.INFO)

reports = list()

source = NotCachedWikiaApiResponsesSource()
reports += source.query(threshold=500)  # we serve 75k not cached responses an hour

for report in reports:
    print report
