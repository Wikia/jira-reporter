"""
Set of unit tests for PHPLogsSource
"""
import unittest

from ..sources.php.common import PHPLogsSource


class PHPLogsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPLogsSource class
    """
    def test_get_backtrace_from_exception(self):
        assert PHPLogsSource._get_backtrace_from_exception(None) == 'n/a'
        assert PHPLogsSource._get_backtrace_from_exception({'trace': None}) == 'n/a'
        assert PHPLogsSource._get_backtrace_from_exception({'trace': ['/foo', '/bar']}) == '* /foo\n* /bar'
        assert PHPLogsSource._get_backtrace_from_exception({'file': '/test', 'trace': ['/foo', '/bar']}) == '* /test\n* /foo\n* /bar'
        assert PHPLogsSource._get_backtrace_from_exception({'trace': ['/usr/wikia/slot1/6875/src/includes/Hooks.php:216']}) == '* /includes/Hooks.php:216'

        assert PHPLogsSource._get_backtrace_from_exception({
            'file': '/usr/wikia/slot1/7211/src/extensions/wikia/UserProfilePageV3/UserProfilePageController.class.php:334',
            'trace': ['/usr/wikia/slot1/6875/src/includes/Hooks.php:216']
        }) == '* /extensions/wikia/UserProfilePageV3/UserProfilePageController.class.php:334\n* /includes/Hooks.php:216'
