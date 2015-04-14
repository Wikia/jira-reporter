"""
Common classes allowing us to access logs from various sources
"""

import hashlib
import logging

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
