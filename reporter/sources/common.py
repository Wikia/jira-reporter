"""
Common classes allowing us to access logs from various sources
"""

import hashlib
import logging
import re
import urllib

from wikia.common.kibana import Kibana
from wikia.common.perfmonitoring import PerfMonitoring


class Source(object):
    """ An abstract class for data providers to inherit from """
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def query(self, query='', threshold=50):
        """
        The Source class entry point

        - the provided query is passed to _get_entries method.
        - returned entries are then filtered using _filter method.
        - filtered entries are normalized using _normalize_entries method
        - reports are grouped (using the key returned by _normalize_entries)
        - each report is than formatted
        """

        if query != '':
            self._logger.info("Query: '{}'".format(query))

        # filter the entries
        try:
            entries = [entry for entry in self._get_entries(query) if self._filter(entry)]
        except:
            self._logger.error('self._get_entries raised an exception', exc_info=True)
            return []

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
                has_all_required_fields = self._has_all_required_fields(entry)

                if key not in normalized:
                    normalized[key] = {
                        'cnt': 1,
                        'entry': entry,
                        'has_all_required_fields': has_all_required_fields
                    }
                else:
                    normalized[key]['cnt'] += 1

                    # update the normalized entry if we finally got the full context
                    # @see PLATFORM-1162
                    if has_all_required_fields and not normalized[key]['has_all_required_fields']:
                        normalized[key]['entry'] = entry
                        normalized[key]['has_all_required_fields'] = True

            else:
                self._logger.debug('Entry not normalized: {}'.format(entry))

        return normalized

    def _generate_reports(self, items, threshold):
        """
        Turn grouped entries from the log into Report instances
        """
        reports = list()

        for key, item in items.iteritems():
            try:
                report = self._get_report(item['entry'])

                # provide various sources a way to modify the report
                self._update_report(report, item['entry'])

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

    @staticmethod
    def _has_all_required_fields(entry):
        """
        This method is called to fill the normalized entries with all required fields
        in case the first match does not have them
        """
        return True

    def _get_entries(self, query):
        """ This method will query the source and return matching entries """
        raise NotImplementedError("_get_entries() method needs to be overwritten in your class!")

    def _filter(self, entry):
        """ Callback used to filter entries """
        raise NotImplementedError("_filter() method needs to be overwritten in your class!")

    def _normalize(self, entry):
        """
        Normalize given message by removing variables like server name
        to improve grouping of messages
        """
        raise NotImplementedError("_normalize() method needs to be overwritten in your class!")

    def _get_report(self, entry):
        """
        Return a report for a given entry

        :type entry object
        :rtype: reporter.reports.Report
        """
        raise NotImplementedError("_get_report() method needs to be overwritten in your class!")

    def _update_report(self, report, entry):
        """
        Allow various sources a way to modify the report
        """
        pass

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

        try:
            metrics.push()
        except:
            self._logger.error('Sending stats to InfluxDB failed', exc_info=True)


class KibanaSource(Source):
    """ elasticsearch-powered data provider """
    LIMIT = 100000  # limit how many rows can be fetched from elasticsearch

    # TODO: move to a separate class
    ENV_PREVIEW = 'Preview'
    ENV_MAIN_DC = 'Production'
    ENV_BACKUP_DC = 'Reston'
    ENV_STAGING = 'Staging'

    PREVIEW_HOST = 'staging-s1'

    KIBANA_URL = 'https://kibana.wikia-inc.com/index.html#/dashboard/script/logstash.js?query={query}&from=6h&fields={fields}'

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

        try:
            if fields.get('http_url'):
                return fields.get('http_url').encode('utf8')
        except UnicodeEncodeError:
            self._logger.error('URL parsing failed', exc_info=True)

        return False

    def _get_env_from_entry(self, entry):
        """
        Get environment for given log entry
        :type entry dict
        :rtype: str
        """
        host = entry.get('@source_host', '')
        env = entry.get('@fields', {}).get('environment')
        is_preview = host == self.PREVIEW_HOST

        # get env info from @fields.environment
        if env == 'staging':
            return self.ENV_STAGING

        if is_preview:
            # staging-s1
            env = self.ENV_PREVIEW
        else:
            # SJC or Reston?
            if re.search(r'\-r\d+$', host) is not None:
                # ap-r20
                env = self.ENV_BACKUP_DC
            else:
                # ap-s32
                env = self.ENV_MAIN_DC

        return env

    @staticmethod
    def format_kibana_url(query, columns=None):
        columns = columns or ['@timestamp', '@source_host', '@message']

        # do not split the query into Kibana subqueries
        query = query.replace(',', ' ')

        # encode backslashes
        query = query.replace('\\', '\\\\')

        return KibanaSource.KIBANA_URL.format(
            query=urllib.quote(query),
            fields=','.join(columns)
        )

    def _get_kibana_url(self, entry):
        """
        Get Kibana dashboard URL for a given entry

        It will be automatically added at the end of the report description
        """
        return None

    def _update_report(self, report, entry):
        """
        Add generic links to error specific Kibana dashboard and request trace (by request_id)
        """
        # call self._get_kibana_url and update the report description if there's a link to custom dashboard
        kibana_url = self._get_kibana_url(entry)

        if kibana_url is not None:
            report.append_to_description('\n\n*Still valid?* Check [Kibana dashboard|{url}]'.format(url=kibana_url))

        # add a link to request trace using @fields.trace_id (introduced by PLATFORM-1949)
        trace_id = entry.get('@fields', {}).get('trace_id')

        if trace_id:
            report.append_to_description('\n\n*[Request trace for {trace_id}|{url}]*'.format(
                trace_id=trace_id,
                url=self.format_kibana_url(
                    query='"{}"'.format(trace_id)
                )
            ))

        # set JIRA URL field
        report.set_url(self._get_url_from_entry(entry))
