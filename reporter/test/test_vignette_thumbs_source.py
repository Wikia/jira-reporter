import unittest

from ..sources import VignetteThumbVerificationSource

class VignetteThumbVerificationSourceTest(unittest.TestCase):


    EXPECTED_REPORT = """
h3. ERROR: foo

*App name*: {{vignette}}
*Source host*: {{localhost}}
*Thumb map*: {{thumb map}}
*Estimated*: {{estimated}}
*Actual*: {{actual}}
    """.strip()

    def setUp(self):
        self._source = VignetteThumbVerificationSource()

    def test_normalize(self):
        assert self._source._normalize({
            '@message': 'test',
            'logger_name': 'test_logger'
        }) == 'Vignette-test_logger-test'

    def test_report(self):
        report = self._source._get_report({
            '@message': 'foo',
            '@source_host': 'localhost',
            'appname': 'vignette',
            'level': 'ERROR',
            'thumb-map': 'thumb map',
            'estimated': 'estimated',
            'actual': 'actual'
        })

        assert report.get_description() == self.EXPECTED_REPORT
