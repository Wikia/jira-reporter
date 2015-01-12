"""
Various data providers
"""
import hashlib
import json
import logging
import re

from reporter.reports import Report
from wikia.common.kibana import Kibana


class Source(object):
    """ An abstract class for data providers to inherit from """
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def query(self, query, threshold=50):
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

        return reports

    def _normalize_entries(self, entries):
        """ Run all entries through _normalize method """
        normalized = dict()

        for entry in entries:
            key = self._normalize(entry)

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
        reports = list()

        for key, item in items.iteritems():
            report = self._get_report(item['entry'])

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
        raise Exception("This method needs to be overwritten in your class!")

    def _filter(self, entry):
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


class KibanaSource(Source):
    """ elasticsearch-powered data provider """
    LIMIT = 100000

    ENV_PREVIEW = 'Preview'
    ENV_PRODUCTION = 'Production'

    PREVIEW_HOST = 'staging-s3'

    """ Kibana/elasticsearch-powered data-provider"""
    def __init__(self, period):
        super(KibanaSource, self).__init__()
        self._kibana = Kibana(period=period)

    def _get_entries(self, query):
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


class PHPErrorsSource(KibanaSource):
    """ Get PHP errors from elasticsearch """
    REPORT_LABEL = 'PHPErrors'
    REPORT_TEMPLATE = """
{full_message}

URL: {url}
Env: {env}

{{code}}
@context = {context_formatted}

@fields = {fields_formatted}
{{code}}
    """

    _query = ''

    def query(self, query, threshold=50):
        self._query = query
        self._logger.info("Query: '{}'".format(query))

        """
        Search for messages starting with "query"
        """
        return super(PHPErrorsSource, self).query({"@message": "/^" + query + "/"}, threshold)

    def _filter(self, entry):
        message = entry.get('@message', '')
        host = entry.get('@source_host', '')

        if not message.startswith(self._query):
            return False

        # filter out by host
        # "@source_host": "ap-s10",
        if re.search(r'^(ap|task|cron|liftium|staging)\-s', host) is None:
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
        fields = entry.get('@fields', {})

        # remove the prefix
        # PHP Fatal error:
        message = re.sub(r'PHP (Fatal error|Warning):', '', message, flags=re.IGNORECASE).strip()

        # remove exception prefix
        # Exception from line 141 of /includes/wikia/nirvana/WikiaView.class.php:
        message = re.sub(r'Exception from line \d+ of [^:]+:', 'Exception:', message)

        # remove HTTP adresses
        # Missing or invalid pubid from http://dragonball.wikia.com/__varnish_liftium/config in /var/www/liftium/delivery/config.php on line 17
        message = re.sub(r'https?://[^\s]+', '<URL>', message)

        # remove release-specific part
        # /usr/wikia/slot1/3006/src
        message = re.sub(r'/usr/wikia/slot1/\d+/src', '', message)

        # update the entry
        entry['@message_normalized'] = message

        # production or preview?
        env = self._get_env_from_entry(entry)

        return 'PHP-{}-{}-{}'.format(self._query, message, env)

    def _get_report(self, entry):
        """
        Format the report to be reported to JIRA
        """
        description = self.REPORT_TEMPLATE.format(
            env=self._get_env_from_entry(entry),
            context_formatted=json.dumps(entry.get('@context', {}), indent=True),
            fields_formatted=json.dumps(entry.get('@fields', {}), indent=True),
            full_message=entry.get('@message'),
            url=self._get_url_from_entry(entry) or 'n/a'
        ).strip()

        return Report(
            summary='{}: {}'.format(self._query, entry.get('@message_normalized')),
            description=description,
            label=self.REPORT_LABEL
        )
