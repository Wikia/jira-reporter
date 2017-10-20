import re

from reporter.reports import Report

from common import PandoraLogsSource


class PandoraErrorsSource(PandoraLogsSource):
    """ Get Pandora errors from elasticsearch """
    REPORT_LABEL = 'PandoraErrors'

    def _get_entries(self, query):
        """ Return matching entries by given prefix """
        return self._kibana.query_by_string(
            query='kubernetes.labels.type: "pandora" AND rawMessage: * AND -rawLevel:"INFO"'.format(query),
            limit=self.LIMIT
        )

    def _filter(self, entry):
        level = entry.get('rawLevel')
        message = entry.get('rawMessage')
        app_name = entry.get('appname')

        if message is None or app_name is None:
            return False

        # filter out all messages except warnings and errors
        if level != 'WARN' and level != 'ERROR':
            return False

        return True

    def _get_kibana_url(self, entry):
        """
        Get the link to Kibana dashboard showing the provided error log entry
        """
        message = entry.get('rawMessage')
        if not message:
            return None

        return self.format_kibana_url(
            query='appname: * AND "{message}"'.format(
                message=message.encode('utf8')
            ),
            columns=['@timestamp', 'rawLevel', 'logger_name', 'rawMessage', 'thread_name']
        )

    def _normalize(self, entry):
        """
        Normalize given entry
        """
        message = entry.get('rawMessage').encode('utf8')
        logger_name = entry.get('logger_name')

        # normalize hashes
        message = re.sub(r'[a-f0-9-]{4,}', 'HASH', message)

        # normalize numeric values
        message = re.sub(r'\d+', 'N', message)

        # normalize URLs
        # Exception purging https://services.wikia.com/user-attribute/user/5430694
        message = re.sub(r'https?://[^\s]+', '<URL>', message)

        # remove JSON
        # error while sending: {"args":{"prevRevision":false
        message = re.sub(r'{.*}$', '{json here}', message)

        return 'Pandora-{}-{}'.format(message, logger_name)

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        message = entry.get('rawMessage').encode('utf8')
        app_name = entry.get('appname')

        description = self.REPORT_TEMPLATE.format(
            app_name=app_name,
            logger_name=entry.get('logger_name', 'n/a'),
            thread_name=entry.get('thread_name', 'n/a'),
            stack_trace=entry.get('stack_trace', 'n/a'),
            full_message='{}: {}'.format(entry.get('rawLevel'), message),
            url=self._get_url_from_entry(entry) or 'n/a'
        ).strip()

        # eg. [discussion] Unable to get the user information for userId: 23912489, Returning the default.
        summary = '[{}] {}'.format(entry.get('appname'), message)

        report = Report(
            summary=summary,
            description=description,
            label=self.REPORT_LABEL
        )

        # eg. service_discussion
        report.add_label('service_{}'.format(app_name))

        return report
