import json

from reporter.helpers import is_from_production_host
from reporter.reports import Report

from .common import PHPLogsSource


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

    EXCEPTION_CLASS = 'Wikia\Security\Exception'

    def _get_entries(self, query):
        """ Return failed security assertions logs """
        return self._kibana.get_rows(match={"@exception.class": self.EXCEPTION_CLASS}, limit=self.LIMIT)

    def _filter(self, entry):
        return is_from_production_host(entry)

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
        context = entry.get('@context', {})

        transaction = context.get('transaction')
        hook_name = context.get('hookName')

        return self.format_kibana_url(
            query='@exception.class: "{}" AND @context.transaction: "{}" AND @context.hookName: "{}"'.
                  format(self.EXCEPTION_CLASS, transaction, hook_name),
            columns=['@timestamp', '@source_host', '@fields.http_url']
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

        assert message is not None, '@message should not be empty'

        if issue_type == 'CSRF':
            assert context.get('hookName') is not None, '@context.hookName should be defined'

            # @see https://cwe.mitre.org/data/definitions/352.html
            labels.append('CWE-352')
            details = """
*A [Cross-site request forgery|https://cwe.mitre.org/data/definitions/352.html] attack is possible here*!
An attacker can make a request on behalf of a current Wikia user.

Please refer to [documentation on Confluence|https://fandom.atlassian.net/wiki/display/SEC/Cross-Site+Request+Forgery] on how to protect your code.

*Transaction*: {{{{{transaction}}}}}
*Action performed*: {{{{{action_performed}}}}}
*Token checked*: {token_checked}
*HTTP method checked*: {method_checked}
""".format(
                transaction=context.get('transaction'),  # e.g. api/nirvana/CreateNewWiki
                action_performed=context.get('hookName'),  # e.g. WikiFactoryChanged
                token_checked='checked' if context.get('editTokenChecked') is True else '*not checked*',
                method_checked='checked' if context.get('httpMethodChecked') is True else '*not checked*',
            )

        # format the report
        full_message = self.FULL_MESSAGE_TEMPLATE.format(
            message=message,
            details=details.strip(),
            backtrace=self._get_backtrace_from_exception(exception, offset=5)  # skip backtrace to CSRFDetector
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
