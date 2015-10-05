import json

from reporter.helpers import is_production_host
from reporter.reports import Report

from common import PHPLogsSource


class PHPSecuritySource(PHPLogsSource):
    """
    Report failed asserts reported by Wikia\Security\Exception

    @see https://github.com/Wikia/app/tree/dev/extensions/wikia/Security
    @see https://kibana.wikia-inc.com/#/dashboard/elasticsearch/PLATFORM-1540
    """
    REPORT_LABEL = 'CSRFDetector'

    FULL_MESSAGE_TEMPLATE = """
h2. {message}

{details}

h5. Backtrace
{backtrace}
"""

    LIMIT = 500

    def _get_entries(self, query):
        """ Return failed security assertions logs """
        return self._kibana.get_rows(match={"@exception.class": "Wikia\\Security\\Exception"}, limit=self.LIMIT)

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
        source = exception.get('file')
        caller = self._get_wikia_caller_from_exception(exception)

        # @see PLATFORM-1540
        if 'CSRFDetector' in source:
            issue_type = 'CSRF'
            message = 'CSRF detected in {}'.format(caller)
        else:
            return None

        entry['issue_type'] = issue_type
        entry['caller'] = caller
        entry['@message'] = message

        return '{}-{}-{}'.format(issue_type, issue_type, caller)

    def _get_kibana_url(self, entry):
        """
        Get Kibana dashboard URL for a given entry

        It will be automatically added at the end of the report description
        """
        # exception = entry.get('@exception', {})

        return self.format_kibana_url(
            query='@exception.class: "Wikia\\Security\\Exception"',
            columns=['@timestamp', '@source_host', '@fields.url']
        )

    def _get_report(self, entry):
        """ Format the report to be sent to JIRA """
        context = entry.get('@context', {})
        exception = entry.get('@exception', {})

        issue_type = entry.get('issue_type')
        message = entry.get('@message')
        details = ''

        # labels to add a report
        labels = ['security']

        assert message is not None

        if issue_type == 'CSRF':
            # @see https://cwe.mitre.org/data/definitions/352.html
            labels.append('CWE-352')
            details = """
*A [Cross-site request forgery|https://cwe.mitre.org/data/definitions/352.html] attack is possible here*!
An attacker can make a request on behalf of a current Wikia user.

Please refer to [documentation on Wikia One|https://one.wikia-inc.com/wiki/User_blog:Daniel_Grunwell/Cross-Site_Request_Forgery_and_Nirvana_controllers] on how to protect your code.

*Action performed*: {{{{{action_performed}}}}}
*Token checked*: {token_checked}
*HTTP method checked*: {method_checked}
""".format(
                action_performed=context.get('caller'),
                token_checked='checked' if context.get('editTokenChecked') is True else '*not checked*',
                method_checked='checked' if context.get('httpMethodChecked') is True else '*not checked*',
            )

        # format the report
        full_message = self.FULL_MESSAGE_TEMPLATE.format(
            message=message,
            details=details.strip(),
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

        report = Report(
            summary=message,
            description=description,
            label=self.REPORT_LABEL
        )

        # add security issue specific labels
        [report.add_label(label) for label in labels]

        return report
