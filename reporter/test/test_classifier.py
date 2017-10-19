"""
Set of unit tests for Classifier
"""
import unittest

from reporter.classifier import Classifier
from reporter.reports import Report


class ClassifierTestClass(unittest.TestCase):
    def setUp(self):
        classifier_config = {
            'components': {
                'Helios': 1,
                'Mercury': 2,
                'Pandora': 3,
                'Phalanx': 4,
                'Chat': 5,
                'CreatePage': 6,
                'DPL': 7,
                'CreateNewWiki': 8,
                'Lua': 9,
                'Core MediaWiki': 10,
            },
            'paths': {
                '/extensions/wikia/Chat2': 'Chat',
                '/extensions/wikia/CreatePage': 'CreatePage',
                '/extensions/DynamicPageList': 'DPL',
                '/extensions/wikia/CreateNewWiki': 'CreateNewWiki',
                '/includes/parser/Parser.php': 'Core MediaWiki',
                '/extensions/Scribunto': 'Lua',
            }
        }
        self.classifier = Classifier(config=classifier_config)

    def test_classify_by_label(self):
        report = Report('foo', 'bar')
        assert self.classifier.classify(report) is None

        report = Report('foo', 'bar', label='MercuryErrors')
        assert self.classifier.classify(report) == (Classifier.PROJECT_MAIN, 2)

        report = Report('foo', 'bar', label='Helios')
        assert self.classifier.classify(report) == (Classifier.PROJECT_SER, 1)

        report = Report('foo', 'bar', label='PandoraErrors')
        assert self.classifier.classify(report) == (Classifier.PROJECT_ERROR_REPORTER, None)

    def test_classify_chat_error_report(self):
        # https://wikia-inc.atlassian.net/browse/SUS-977
        report = Report(
            summary='[Exception] HTTP request failed - ChatServerApiClient:makeRequest',
            description="""
h1. Exception

HTTP request failed - ChatServerApiClient:makeRequest

h5. Backtrace
* /includes/HttpFunctions.php:102
* /includes/HttpFunctions.php:140
* /extensions/wikia/Chat2/ChatServerApiClient.class.php:138
* /extensions/wikia/Chat2/ChatServerApiClient.class.php:31
* /extensions/wikia/Chat2/ChatAjax.class.php:84
* /extensions/wikia/Chat2/Chat_setup.php:185
* /includes/AjaxDispatcher.php:118
* /includes/Wiki.php:629
* /includes/Wiki.php:547
* /index.php:58
""".strip()
        )

        assert self.classifier.classify(report) == (Classifier.PROJECT_MAIN, 5)  # Chat

    def test_classify_CreatePage_error_report(self):
        # https://wikia-inc.atlassian.net/browse/MAIN-7876
        report = Report(
            summary='PHP Warning: Missing argument 1 for SpecialEditPage::execute(), called in /extensions/wikia/CreatePage/monobook/SpecialCreatePage.class.php on line 49 and defined in /extensions/wikia/CreatePage/monobook/SpecialEditPage.class.php on line 25',
            description="""
PHP Warning: Missing argument 1 for SpecialEditPage::execute(), called in /usr/wikia/slot1/13272/src/extensions/wikia/CreatePage/monobook/SpecialCreatePage.class.php on line 49 and defined in /usr/wikia/slot1/13272/src/extensions/wikia/CreatePage/monobook/SpecialEditPage.class.php on line 25

*URL*: http://desencyclopedie.wikia.com/wiki/Sp%C3%A9cial:CreatePage?wpPollId=xssnezwj%3E%3Chyqxl&wpVote=xss&wpPollRadioB0A402429314838F13DBDC9E0963D17B=xss&
*Env*: Production
""".strip()
        )

        assert self.classifier.classify(report) == (Classifier.PROJECT_MAIN, 6)  # CreatePage

    def test_classify_DPL_error_report(self):
        # https://wikia-inc.atlassian.net/browse/ER-14593
        report = Report(
            summary='[Wikia\Util\AssertionException] DatabaseMysqli::mysqlNumRows',
            description="""
h1. Wikia\Util\AssertionException

DatabaseMysqli::mysqlNumRows

h5. Backtrace
* /lib/Wikia/src/Util/Assert.php:25
* /includes/db/DatabaseMysqli.php:207
* /includes/db/DatabaseMysqlBase.php:241
* /extensions/DynamicPageList/DPLMain.php:2584
* /extensions/DynamicPageList/DPLSetup.php:1385
* /includes/parser/Parser.php:3516
* /includes/parser/Preprocessor_DOM.php:1189
* /includes/parser/Parser.php:3280
* /includes/parser/Parser.php:1205
* /includes/parser/Parser.php:371
* /includes/WikiPage.php:3178
* /includes/PoolCounter.php:192
* /includes/Article.php:634
* /includes/actions/ViewAction.php:40
* /includes/Wiki.php:528
* /includes/Wiki.php:307
* /includes/Wiki.php:667
* /includes/Wiki.php:547
* /index.php:58
""".strip()
        )

        assert self.classifier.classify(report) == (Classifier.PROJECT_MAIN, 7)  # DPL

    def test_classify_CreateNewWiki_error_report(self):
        # https://wikia-inc.atlassian.net/browse/SUS-974
        report = Report(
            summary='[Exception] Wikia\CreateNewWiki\Tasks\TaskRunner::run task Wikia\CreateNewWiki\Tasks\ImportStarterData failed',
            description="""
h1. Exception

Wikia\CreateNewWiki\Tasks\TaskRunner::run task Wikia\CreateNewWiki\Tasks\ImportStarterData failed

h5. Backtrace
* /lib/Wikia/src/Logger/WikiaLogger.php:163
* /lib/Wikia/src/Logger/WikiaLogger.php:145
* /lib/Wikia/src/Logger/Loggable.php:46
* /extensions/wikia/CreateNewWiki/tasks/TaskRunner.php:92
* /extensions/wikia/CreateNewWiki/CreateWiki.php:59
* /extensions/wikia/CreateNewWiki/CreateNewWikiController.class.php:297
* /includes/wikia/nirvana/WikiaDispatcher.class.php:214
* /includes/wikia/nirvana/WikiaApp.class.php:645
* /includes/wikia/nirvana/WikiaApp.class.php:661
* /wikia.php:48
""".strip()
        )

        assert self.classifier.classify(report) == (Classifier.PROJECT_MAIN, 8)  # CreateNewWiki

    def test_classify_LuaException_report(self):
        # https://wikia-inc.atlassian.net/browse/SUS-2029
        report = Report(
            summary='[ScribuntoException] MWExceptionHandler::report',
            description="""
h1. ScribuntoException

MWExceptionHandler::report

h5. Backtrace
* /extensions/Scribunto/common/Base.php:97
* /extensions/Scribunto/engines/LuaStandalone/LuaStandaloneEngine.php:448
* /extensions/Scribunto/engines/LuaStandalone/LuaStandaloneEngine.php:318
* /extensions/Scribunto/engines/LuaStandalone/LuaStandaloneEngine.php:281
* /extensions/Scribunto/engines/LuaStandalone/LuaStandaloneEngine.php:184
* /extensions/Scribunto/engines/LuaCommon/LuaCommon.php:205
* /extensions/Scribunto/engines/LuaCommon/LuaCommon.php:589
* /extensions/Scribunto/common/Hooks.php:96
* /includes/parser/Parser.php:3509
* /includes/parser/Preprocessor_DOM.php:1189
* /includes/parser/Parser.php:3698
* /includes/parser/Preprocessor_DOM.php:1189
* /includes/parser/Parser.php:3698
* /includes/parser/Preprocessor_DOM.php:1189
* /includes/parser/Parser.php:3363
* /includes/parser/Preprocessor_DOM.php:1189
* /includes/parser/Parser.php:3363
* /includes/parser/Preprocessor_DOM.php:1189
* /includes/parser/Preprocessor_DOM.php:1651
* /includes/parser/Preprocessor_DOM.php:1659
* /extensions/Scribunto/engines/LuaCommon/LuaCommon.php:421
* /extensions/Scribunto/engines/LuaStandalone/LuaStandaloneEngine.php:262
* /extensions/Scribunto/engines/LuaStandalone/LuaStandaloneEngine.php:240
* /extensions/Scribunto/engines/LuaStandalone/LuaStandaloneEngine.php:287
* /extensions/Scribunto/engines/LuaStandalone/LuaStandaloneEngine.php:184
* /extensions/Scribunto/engines/LuaCommon/LuaCommon.php:205
* /extensions/Scribunto/engines/LuaCommon/LuaCommon.php:589
* /extensions/Scribunto/common/Hooks.php:96
* /includes/parser/Parser.php:3509
* /includes/parser/Preprocessor_DOM.php:1189
* /includes/parser/Parser.php:3698
* /includes/parser/Preprocessor_DOM.php:1189
* /includes/parser/Parser.php:3273
* /includes/parser/Parser.php:1203
* /includes/parser/Parser.php:370
* /includes/WikiPage.php:3192
* /includes/PoolCounter.php:192
* /includes/Article.php:634
* /includes/actions/ViewAction.php:40
* /includes/Wiki.php:528
* /includes/Wiki.php:307
* /includes/Wiki.php:667
* /includes/Wiki.php:547
* /index.php:58
""".strip()
        )

        assert self.classifier.classify(report) == (Classifier.PROJECT_MAIN, 9)  # LUA
