"""
Various data providers

@see https://jira.atlassian.com/secure/WikiRendererHelpAction.jspa?section=all  JIRA text formatting
@see http://www.solrtutorial.com/solr-query-syntax.html                         Lucene query syntax
"""
import hashlib
import json
import logging
import re

from .helpers import is_main_dc_host, generalize_sql
from .reports import Report
from wikia.common.kibana import Kibana
from wikia.common.perfmonitoring import PerfMonitoring


class Source(object):
    """ An abstract class for data providers to inherit from """
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def query(self, query, threshold=50):
        """
        The Source class entry point

        - the provided query is passed to _get_entries method.
        - returned entries are than filtered using _filter method.
        - filtered entries are normalized using _normalize_entries method
        - reports are grouped (using the key returned by _normalize_entries)
        - each report is than formatted
        """

        self._logger.info("Query: '{}'".format(query))

        # filter the entries
        entries = [entry for entry in self._get_entries(query) if self._filter(entry)]
        self._logger.info("Got {} entries after filtering".format(len(entries)))

        # group them
        normalized = self._normalize_entries(entries)

        # generate reports
        reports = self._generate_reports(normalized, threshold)

        # log all reports
        self._logger.info("Returning {} reports (with threshold set to {} applied)".format(len(reports), threshold))

        for report in reports:
            self._logger.info("> {summary} ({counter} instances)".format(
                summary=report.get_summary(),
                counter=report.get_counter()
            ))

        self._send_stats(query, entries, reports)
        return reports

    def _normalize_entries(self, entries):
        """ Run all entries through _normalize method """
        normalized = dict()

        for entry in entries:
            try:
                key = self._normalize(entry)

                # extra normalization
                if key is not None:
                    key = key.lower().replace(' ', '')
            except UnicodeError:
                # ignore UTF parsing errors
                self._logger.error('Entry parsing error', exc_info=True)
                continue

            # all entries will be grouped
            # using the key return by _normalize method
            if key is not None:
                if key not in normalized:
                    normalized[key] = {
                        'cnt': 0,
                        'entry': entry
                    }

                normalized[key]['cnt'] += 1
            else:
                # self._logger.info('Entry not normalized: {}'.format(entry))
                pass

        return normalized

    def _generate_reports(self, items, threshold):
        """
        Turn grouped entries from the log into Report instances
        """
        reports = list()

        for key, item in items.iteritems():
            try:
                report = self._get_report(item['entry'])
            except Exception:
                self._logger.error('get_report raised an exception', exc_info=True)
                continue

            if item['cnt'] < threshold:
                self._logger.info('Skipped "{}" ({} occurrences)'.format(report.get_summary(), item['cnt']))
                continue

            # update the report with the "hash" generated previously via _normalize
            m = hashlib.md5()
            m.update(key)
            report.set_unique_id(m.hexdigest())

            report.set_counter(item['cnt'])
            reports.append(report)

        return reports

    def _get_entries(self, query):
        """ This method will query the source and return matching entries """
        raise Exception("This method needs to be overwritten in your class!")

    def _filter(self, entry):
        """ Callback used to filter entries """
        raise Exception("This method needs to be overwritten in your class!")

    def _normalize(self, entry):
        """
        Normalize given message by removing variables like server name
        to improve grouping of messages
        """
        raise Exception("This method needs to be overwritten in your class!")

    def _get_report(self, entry):
        """
        Return a report for a given entry
        """
        raise Exception("This method needs to be overwritten in your class!")

    def _send_stats(self, query, entries, reports):
        """
        Send metrics to InfluxDB

        They will be stored in 'jirareporter_reports' time series
        """
        metrics = PerfMonitoring(app_name='JIRAreporter', series_name='reports')

        metrics.set('type', self.__class__.__name__)
        metrics.set('query', query)
        metrics.set('entries', len(entries))
        metrics.set('reports', len(reports))
        metrics.push()


class KibanaSource(Source):
    """ elasticsearch-powered data provider """
    LIMIT = 100000

    ENV_PREVIEW = 'Preview'
    ENV_PRODUCTION = 'Production'

    PREVIEW_HOST = 'staging-s3'

    def __init__(self, period=3600):
        super(KibanaSource, self).__init__()
        self._kibana = Kibana(period=period)

    def _get_entries(self, query):
        """ Send the query to elasticsearch """
        return self._kibana.get_rows(query, limit=self.LIMIT)

    # helper methods
    def _get_url_from_entry(self, entry):
        """
        Get URL from given log entry
        :param entry: dict
        :return: bool|string
        """
        fields = entry.get('@fields', {})

        url = False
        try:
            if fields.get('server') and fields.get('url'):
                url = 'http://{}{}'.format(fields.get('server'), fields.get('url'))
        except UnicodeEncodeError:
            self._logger.error('URL parsing failed', exc_info=True)

        return url

    def _get_env_from_entry(self, entry):
        """
        Get environment for given log entry
        :param entry: dict
        :return: string
        """
        # preview -> staging-s3
        is_preview = entry.get('@source_host', '') == self.PREVIEW_HOST
        env = self.ENV_PREVIEW if is_preview is True else self.ENV_PRODUCTION

        return env


class PHPLogsSource(KibanaSource):
    """ Shared between PHP logs providers """
    REPORT_TEMPLATE = """
{{noformat}}{full_message}{{noformat}}

*URL*: {url}
*Env*: {env}

{{code}}
@source_host = {source_host}

@context = {context_formatted}

@fields = {fields_formatted}
{{code}}
    """


class PHPErrorsSource(PHPLogsSource):
    """ Get PHP errors from elasticsearch """
    REPORT_LABEL = 'PHPErrors'

    def _get_entries(self, query):
        """ Return matching entries by given prefix """
        return self._kibana.query_by_string(query='@message:"^{}"'.format(query), limit=self.LIMIT)

    def _filter(self, entry):
        """ Remove log entries that are not coming from main DC or lack key information """
        message = entry.get('@message', '')
        host = entry.get('@source_host', '')

        # filter out by host
        # "@source_host": "ap-s10",
        if not is_main_dc_host(host):
            return False

        # filter out errors without a clear context
        # on line 115
        if re.search(r'on line \d+', message) is None:
            return False

        return True

    def _normalize(self, entry):
        """
        Normalize given message by removing variables like server name
        to improve grouping of messages

        PHP Fatal Error: Call to a member function getText() on a non-object in /usr/wikia/slot1/3006/src/includes/api/ApiParse.php on line 20

        will become:

        Call to a member function getText() on a non-object in /includes/api/ApiParse.php on line 20
        """
        message = entry.get('@message')

        # remove exception prefix
        # Exception from line 141 of /includes/wikia/nirvana/WikiaView.class.php:
        message = re.sub(r'Exception from line \d+ of [^:]+:', 'Exception:', message)

        # remove HTTP adresses
        # Missing or invalid pubid from http://dragonball.wikia.com/__varnish_liftium/config in /var/www/liftium/delivery/config.php on line 17
        message = re.sub(r'https?://[^\s]+', '<URL>', message)

        # remove release-specific part
        # /usr/wikia/slot1/3006/src
        message = re.sub(r'/usr/wikia/slot1/\d+/src', '', message)

        # remove XML parsing errors details
        # Tag figure invalid in Entity, line: 286
        # Tag X invalid in Entity, line: N
        message = re.sub(r'Tag \w+ invalid in Entity, line: \d+', 'Tag X invalid in Entity, line: N', message)

        # remove popen() arguments
        message = re.sub(r'popen\([^\)]+\)', 'popen(X)', message)

        # remove exec arguments
        message = re.sub(r'Unable to fork \[[^\]]+\]', 'Unable to fork [X]', message)

        # normalize /tmp paths
        message = re.sub(r'/tmp/\w+', '/tmp/X', message)

        # update the entry
        entry['@message_normalized'] = message

        # production or preview?
        env = self._get_env_from_entry(entry)

        return 'PHP-{}-{}'.format(message, env)

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        description = self.REPORT_TEMPLATE.format(
            env=self._get_env_from_entry(entry),
            source_host=entry.get('@source_host', 'n/a'),
            context_formatted=json.dumps(entry.get('@context', {}), indent=True),
            fields_formatted=json.dumps(entry.get('@fields', {}), indent=True),
            full_message=entry.get('@message'),
            url=self._get_url_from_entry(entry) or 'n/a'
        ).strip()

        return Report(
            summary=entry.get('@message_normalized'),
            description=description,
            label=self.REPORT_LABEL
        )


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

    def _get_entries(self, query):
        """ Return matching exception logs """
        return self._kibana.get_rows(match={"@exception.class": query}, limit=self.LIMIT)

    def _filter(self, entry):
        """ Remove log entries that are not coming from main DC """
        host = entry.get('@source_host', '')

        # filter out by host
        # "@source_host": "ap-s10",
        if not is_main_dc_host(host):
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

        backtrace = entry.get('@exception', {}).get('trace', [])

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
            backtrace='\n* '.join(backtrace)
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

        context = {
            'query': parsed.get('Query'),
            'function': parsed.get('Function'),
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
        return self._kibana.query_by_string(query='@context.num_rows: [{} TO *]'.format(self.ROWS_THRESHOLD), limit=self.LIMIT)

    def _filter(self, entry):
        """ Remove log entries that are not coming from main DC """
        if not entry.get('@message', '').startswith('SQL '):
            return False

        # filter out by host
        # "@source_host": "ap-s10",
        host = entry.get('@source_host', '')
        if not is_main_dc_host(host):
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
        backtrace = entry.get('@exception', {}).get('trace', [])

        # format the report
        full_message = self.FULL_MESSAGE_TEMPLATE.format(
            query=query,
            function=context.get('method'),
            num_rows=context.get('num_rows'),
            backtrace='\n* '.join(backtrace)
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
