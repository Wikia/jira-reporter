"""
Set of unit tests for PHPLogsSource
"""
import unittest

from ..sources.php.common import PHPLogsSource


class PHPLogsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPLogsSource class
    """
    def test_normalize_backtrace(self):
        assert PHPLogsSource._normalize_backtrace(None) == 'n/a'
        assert PHPLogsSource._normalize_backtrace(['/foo', '/bar']) == '* /foo\n* /bar'
        assert PHPLogsSource._normalize_backtrace(['/usr/wikia/slot1/6875/src/includes/Hooks.php:216"']) == '* /includes/Hooks.php:216"'
