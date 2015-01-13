"""
Set of helper functions
"""
import re


def is_main_dc_host(host):
    """
    Return true if given host is from our main datacenter (i.e. SJC)
    """
    return re.search(r'^(ap|task|cron|liftium|staging)\-s', host) is not None
