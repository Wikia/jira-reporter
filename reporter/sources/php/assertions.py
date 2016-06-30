import json
import re

from reporter.helpers import is_production_host
from reporter.reports import Report

from common import PHPLogsSource


class PHPAssertionsSource(PHPLogsSource):
    """
    Report failed asserts reported by Wikia\Util\AssertionException
    """
    REPORT_LABEL = 'PHPAssertion'

    FULL_MESSAGE_TEMPLATE = """
h1. {assertion}

{message}

h5. Backtrace
{backtrace}
"""

    def _get_entries(self, query):
        """ Return failed assertions logs """
        # @see http://www.solrtutorial.com/solr-query-syntax.html
        return self._kibana.get_rows(match={"@exception.class": "Wikia\\Util\\AssertionException"}, limit=self.LIMIT)

    def _filter(self, entry):
        # filter out by host
        # "@source_host": "ap-s10",
        host = entry.get('@source_host', '')
        if not is_production_host(host):
            return False

        return True

    def _normalize(self, entry):
        """ Normalize using the assertion class and message """
        exception = entry.get('@exception', {})
        message = exception.get('message')

        # remove PHP-encoded data
        # a:26:{s:3:"url";...s:10:"local_port";i:0;}
        message = re.sub(r'a:\d+:{.*;}', '', message)

        # normalize services timeout errors
        message = re.sub(r'API call to /[^ ]+ timed out', 'API call to /X timed out', message)

        # {"title":"Attribute UserProfilePagesV3_birthday not found for user 26816594","status":404}
        message = re.sub(r'Attribute [^\s]+ not found for user \d+', 'Attribute X not found for user N', message)

        # [404] Error connecting to the API (10.8.74.17:31440/user/28883525/attr/UserProfilePagesV3_birthday)
        message = re.sub(r'\d+.\d+.\d+.\d+:\d+', 'N.N.N.N:N', message)  # normalize IP addresses
        message = re.sub(r'/\d+', '/N', message)  # normalize user ID

        message = message.strip(': ')

        return '{}-{}'.format(exception.get('class'), message)

    def _get_kibana_url(self, entry):
        """
        Get Kibana dashboard URL for a given entry

        It will be automatically added at the end of the report description
        """
        exception = entry.get('@exception', {})

        return self.format_kibana_url(
            query='@exception.class: "Wikia\Util\AssertionException" AND @exception.message:"{}"'.format(exception.get('message')),
            columns=['@timestamp', '@source_host', '@fields.http_url']
        )

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        exception = entry.get('@exception', {})

        # format the report
        full_message = self.FULL_MESSAGE_TEMPLATE.format(
            assertion=exception.get('message'),
            message=entry.get('@message'),
            backtrace=self._get_backtrace_from_exception(exception)
        ).strip()

        description = self.REPORT_TEMPLATE.format(
            env=self._get_env_from_entry(entry),
            source_host=entry.get('@source_host', 'n/a'),
            context_formatted=json.dumps(entry.get('@context', {}), indent=True),
            fields_formatted=json.dumps(entry.get('@fields', {}), indent=True),
            full_message=full_message,
            url=self._get_url_from_entry(entry) or 'n/a'
        ).strip()

        return Report(
            summary='[Assertion failed] {assertion}'.format(assertion=exception.get('message')),
            description=description,
            label=self.REPORT_LABEL
        )
