"""
Set of helper functions
"""
import re


def is_main_dc_host(host):
    """
    Return true if given host is from our main datacenter (i.e. SJC)
    """
    return re.search(r'^(ap|task|cron|liftium|staging)\-s', host) is not None


def generalize_sql(sql):
    """
    Removes most variables from an SQL query and replaces them with X or N for numbers.

    Based on Mediawiki's DatabaseBase::generalizeSQL
    """
    if sql is None:
        return None

    sql = re.sub(r"\\\\", '', sql)
    sql = re.sub(r"\\'", '', sql)
    sql = re.sub(r'\\"', '', sql)
    sql = re.sub(r"'.*'", 'X', sql)
    sql = re.sub(r'".*"', 'X', sql)

    # All newlines, tabs, etc replaced by single space
    sql = re.sub(r'\s+', ' ', sql)

    # All numbers => N
    sql = re.sub(r'-?[0-9]+', 'N', sql)

    # MW comments
    # e.g. /* CategoryDataService::getMostVisited N.N.N.N */
    sql = re.sub(r'\s?/\*[^\*]+\*/', '', sql)

    return sql.strip()
