#!/usr/bin/env python
import logging

from reporter.reporters import Jira
from reporter.sources import PHPErrorsSource

logging.basicConfig(level=logging.INFO)

# source = PHPErrorsSource(period=3600)
source = PHPErrorsSource(period=3600)
# source.LIMIT = 25000

# res = source.query("PHP Warning", threshold=50)
res = source.query("PHP Fatal Error", threshold=5)
# res = source.query("DBError", threshold=5)

reporter = Jira()

for report in res:
    reporter.report(report)
