import json
import re

from reporter.helpers import generalize_sql, is_production_host
from reporter.reports import Report

from common import PHPLogsSource


class DBQueryErrorsSource(PHPLogsSource):
    """ Get DB errors triggered by PHP application from elasticsearch """
    REPORT_LABEL = 'DBQueryErrors'

    FULL_MESSAGE_TEMPLATE = """
*Query*: {{noformat}}{query}{{noformat}}
*Function*: {function}
*DB server*: {server}
*Error*: {error}

h5. Backtrace
* {backtrace}
"""

    # MySQL error codes
    # @see https://dev.mysql.com/doc/refman/5.5/en/error-messages-server.html
    ER_LOCK_WAIT_TIMEOUT = 1205
    ER_LOCK_DEADLOCK = 1213

    def _get_entries(self, query):
        """ Return matching exception logs """
        return self._kibana.get_rows(match={"@exception.class": 'DBQueryError'}, limit=self.LIMIT)

    def _filter(self, entry):
        """ Remove log entries that are not coming from main DC """
        host = entry.get('@source_host', '')

        # filter out by host
        # "@source_host": "ap-s10",
        if not is_production_host(host):
            return False

        # skip deadlocks (PLATFORM-1110)
        context = entry.get('@context', {})
        if context.get('errno') in [self.ER_LOCK_DEADLOCK, self.ER_LOCK_WAIT_TIMEOUT]:
            return False

        return True

    def _normalize(self, entry):
        """
        Normalize given SQL error using normalized query and error code
        """
        context = self._get_context_from_entry(entry)

        if context is not None:
            query = context.get('query')

            if query is not None:
                entry.get('@context', {}).update(context)
                return '{}-{}'.format(generalize_sql(query), context.get('errno'))

        return None

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        context = entry.get('@context')

        query = context.get('query')
        normalized = generalize_sql(query)

        # remove server IP from error message
        error_no_ip = context.get('error').\
            replace('({})'.format(context.get('server')), '').\
            strip()

        # format the report
        full_message = self.FULL_MESSAGE_TEMPLATE.format(
            query=query,
            error=error_no_ip,
            function=context.get('function'),
            server=context.get('server'),
            backtrace=self._normalize_backtrace(entry.get('@exception', {}).get('trace'))
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
            summary='[DB error {err}] {function} - {query}'.format(
                err=error_no_ip, function=context.get('function'), query=normalized),
            description=description,
            label=self.REPORT_LABEL
        )

    @staticmethod
    def _get_context_from_entry(entry):
        """ Parse message coming from MediaWiki and extract key information """
        exception = entry.get('@exception', {})
        context = entry.get('@context', {})
        message = exception.get('message')

        if message is None:
            return None

        message = message.strip()

        """
        A database error has occurred.  Did you forget to run maintenance/update.php after upgrading?  See: https://www.mediawiki.org/wiki/Manual:Upgrading#Run_the_update_script
        Query: SELECT  DISTINCT `page`.page_namespace AS page_namespace,`page`.page_title AS page_title,`page`.page_id AS page_id, `page`.page_title  as sortkey FROM `page` WHERE 1=1  AND `page`.page_namespace IN ('6') AND `page`.page_is_redirect=0 AND 'Hal Homsar Solo' = (SELECT rev_user_text FROM `revision` WHERE `revision`.rev_page=page_id ORDER BY `revision`.rev_timestamp ASC LIMIT 1) ORDER BY page_title ASC LIMIT 0, 500
        Function: DPLMain:dynamicPageList
        Error: 1317 Query execution was interrupted (10.8.38.37)
        """

        # parse multiline message
        parsed = dict()

        for line in message.split("\n")[1:]:
            if ':' in line:
                [key, value] = line.split(":", 1)
                parsed[key] = value.strip()

        # normalize "DatabaseBase::sourceFile( /usr/wikia/slot1/3690/src/maintenance/cleanupStarter.sql )"
        function = parsed.get('Function', '')
        function = re.sub(r'/usr/wikia/slot1/\d+/src', '', function)

        context = {
            'query': parsed.get('Query'),
            'function': function,
            'error': '{} {}'.format(context.get('errno'), context.get('err')),
        }

        return context


class DBQueryNoLimitSource(PHPLogsSource):
    """ Get DB queries that return excessive number of rows """
    REPORT_LABEL = 'DBQueryNoLimit'

    ROWS_THRESHOLD = 2000

    FULL_MESSAGE_TEMPLATE = """
The database query below returned far too many rows. Please use a proper LIMIT statement.

*Query*: {{noformat}}{query}{{noformat}}
*Function*: {function}
*Rows returned*: {num_rows}

h5. Backtrace
* {backtrace}
"""

    def _get_entries(self, query):
        """ Return matching exception logs """
        # @see http://www.solrtutorial.com/solr-query-syntax.html
        return self._kibana.query_by_string(
            query='@context.num_rows: [{} TO *]'.format(self.ROWS_THRESHOLD),
            limit=self.LIMIT
        )

    def _filter(self, entry):
        """ Remove log entries that are not coming from main DC """
        if not entry.get('@message', '').startswith('SQL '):
            return False

        # filter out by host
        # "@source_host": "ap-s10",
        host = entry.get('@source_host', '')
        if not is_production_host(host):
            return False

        # remove those that do not return enough rows
        context = entry.get('@context', dict())
        if context.get('num_rows', 0) < self.ROWS_THRESHOLD:
            return False

        return True

    def _normalize(self, entry):
        """ Normalize the entry using the query and the method that made it """
        message = entry.get('@message')
        context = entry.get('@context', dict())

        return '{}-{}-no-limit'.format(generalize_sql(message), context.get('method'))

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        context = entry.get('@context')

        query = entry.get('@message')
        query = re.sub(r'^SQL', '', query).strip()  # remove "SQL" message prefix

        # format the report
        full_message = self.FULL_MESSAGE_TEMPLATE.format(
            query=query,
            function=context.get('method'),
            num_rows=context.get('num_rows'),
            backtrace=self._normalize_backtrace(entry.get('@exception', {}).get('trace'))
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
            summary='[{method}] The database query returns {rows}k+ rows'.format(
                method=context.get('method'), rows=context.get('num_rows') / 1000),
            description=description,
            label=self.REPORT_LABEL
        )