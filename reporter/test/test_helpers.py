"""
Set of unit tests for helper functions
"""
import unittest

from ..helpers import is_main_dc_host


class UtilsTestClass(unittest.TestCase):
    @staticmethod
    def test_is_main_dc_host():
        assert is_main_dc_host('ap-s32')
        assert is_main_dc_host('task-s2')
        assert is_main_dc_host('cron-s5')
        assert is_main_dc_host('staging-s3')

        assert is_main_dc_host('ap-r32') is False
        assert is_main_dc_host('dev-foo') is False
