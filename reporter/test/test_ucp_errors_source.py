# -*- coding: utf-8 -*-
"""
Set of unit tests for PHPExceptionsSource
"""
import unittest

from ..sources import UCPErrorsSource, PHPTypeErrorsSource

class UCPErrorsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPTypeErrorsSource class
    """
    def setUp(self):
        self._source = UCPErrorsSource()

        self.message = 'PHP Notice: Undefined property: StubObject::$mOutput in ' \
                       '/extensions/fandom/Blogs/src/BlogTemplate.php on line 961 '

        self.stack_trace = 'PHP Notice: Undefined property: StubObject::$mOutput in ' \
                       '/extensions/fandom/Blogs/src/BlogTemplate.php on line ' \
                       '961\n\t#0 /extensions/fandom/Blogs/src/BlogTemplate.php(961): ' \
                       'MWExceptionHandler::handleError(integer, string, string, ' \
                       'integer, array)\n\t#1 ' \
                       '/extensions/fandom/Blogs/src/BlogTemplate.php(365): ' \
                       'Fandom\\Blogs\\BlogTemplate::__parse(array, array, StubObject, ' \
                       'boolean)\n\t#2 /extensions/fandom/Blogs/src/BlogArticle.php(' \
                       '179): Fandom\\Blogs\\BlogTemplate::parseTag(string, array, ' \
                       'StubObject)\n\t#3 ' \
                       '/extensions/fandom/Blogs/src/BlogArticle.php(39): ' \
                       'Fandom\\Blogs\\BlogArticle->showFeed(string)\n\t#4 ' \
                       '/includes/actions/ViewAction.php(68): ' \
                       'Fandom\\Blogs\\BlogArticle->view()\n\t#5 ' \
                       '/includes/MediaWiki.php(499): ViewAction->show()\n\t#6 ' \
                       '/includes/MediaWiki.php(294): MediaWiki->performAction(' \
                       'Fandom\\Blogs\\BlogArticle, Title)\n\t#7 ' \
                       '/includes/MediaWiki.php(865): MediaWiki->performRequest(' \
                       ')\n\t#8 /includes/MediaWiki.php(515): MediaWiki->main()\n\t#9 ' \
                       '/index.php(42): MediaWiki->run()\n\t#10 {main} '

        self.url = 'hearthstone.gamepedia.com'

        self.entry = {
            '@message': self.message,
            '@message_normalized': self.message,
            '@fields': {
                'http_url_domain': self.url,
                'http_url_path': '/Holy_Mackerel'
            },
            'stack_trace': self.stack_trace,
        }

    def default_assert(self, report):
        assert self.stack_trace in report.get_description()
        assert self.url in report.get_description()
        assert self.message in report.get_description()

        assert report.get_summary() == 'PHP Notice: Undefined property: StubObject::$mOutput in ' \
                                       '/extensions/fandom/Blogs/src/BlogTemplate.php on line 961 '


    def test_report_fatal(self):
        event_type = {'event': {'type': 'fatal'}}
        self.entry.update(event_type)
        report = self._source._get_report(self.entry)
        self.default_assert(report)

        assert report.get_priority() == {'id': '9'}

    def test_report_error(self):
        event_type = {'event': {'type': 'error'}}
        self.entry.update(event_type)
        report = self._source._get_report(self.entry)

        self.default_assert(report)
        assert report.get_priority() == {'id': '8'}

    def test_report_exception(self):
        event_type = {'event': {'type': 'exception'}}
        self.entry.update(event_type)
        report = self._source._get_report(self.entry)

        self.default_assert(report)
        assert report.get_priority() == {'id': '6'}

    def test_report_random(self):
        event_type = {'event': {'type': 'random'}}
        self.entry.update(event_type)
        report = self._source._get_report(self.entry)

        self.default_assert(report)
        assert report.get_priority() == False
