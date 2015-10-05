"""
Set of unit tests for PHPLogsSource
"""
import unittest

from ..sources.php.common import PHPLogsSource


class PHPLogsSourceTestClass(unittest.TestCase):
    """
    Unit tests for PHPLogsSource class
    """
    def test_get_backtrace_from_exception(self):
        assert PHPLogsSource._get_backtrace_from_exception(None) == 'n/a'
        assert PHPLogsSource._get_backtrace_from_exception({'trace': None}) == 'n/a'
        assert PHPLogsSource._get_backtrace_from_exception({'trace': ['/foo', '/bar']}) == '* /foo\n* /bar'
        assert PHPLogsSource._get_backtrace_from_exception({'file': '/test', 'trace': ['/foo', '/bar']}) == '* /test\n* /foo\n* /bar'
        assert PHPLogsSource._get_backtrace_from_exception({'trace': ['/usr/wikia/slot1/6875/src/includes/Hooks.php:216']}) == '* /includes/Hooks.php:216'

        assert PHPLogsSource._get_backtrace_from_exception({'file': '/test', 'trace': ['/foo', '/bar']}, offset=0) == '* /test\n* /foo\n* /bar'
        assert PHPLogsSource._get_backtrace_from_exception({'file': '/test', 'trace': ['/foo', '/bar']}, offset=1) == '* /foo\n* /bar'
        assert PHPLogsSource._get_backtrace_from_exception({'file': '/test', 'trace': ['/foo', '/bar']}, offset=2) == '* /bar'

        assert PHPLogsSource._get_backtrace_from_exception({
            'file': '/usr/wikia/slot1/7211/src/extensions/wikia/UserProfilePageV3/UserProfilePageController.class.php:334',
            'trace': ['/usr/wikia/slot1/6875/src/includes/Hooks.php:216']
        }) == '* /extensions/wikia/UserProfilePageV3/UserProfilePageController.class.php:334\n* /includes/Hooks.php:216'

    def test_get_wikia_caller_from_exception(self):
        assert PHPLogsSource._get_wikia_caller_from_exception(None) is None
        assert PHPLogsSource._get_wikia_caller_from_exception({'trace': None}) is None

        assert PHPLogsSource._get_wikia_caller_from_exception({'trace': [
            "/usr/wikia/slot1/7550/src/extensions/wikia/Security/classes/CSRFDetector.class.php:59",
            "{\"function\":\"foo\",\"class\":\"Wikia\\\\Security\\\\CSRFDetector\",\"type\":\"::\"}",
            "/usr/wikia/slot1/7550/src/includes/Hooks.php:216",
            "/usr/wikia/slot1/7550/src/includes/GlobalFunctions.php:4045",
            "/usr/wikia/slot1/7550/src/includes/upload/UploadFromUrl.php:164",
            "/usr/wikia/slot1/7550/src/includes/upload/UploadFromUrl.php:110",
            "/usr/wikia/slot1/7550/src/extensions/wikia/VideoHandlers/VideoFileUploader.class.php:332",
            "/usr/wikia/slot1/7550/src/extensions/wikia/VideoHandlers/VideoFileUploader.class.php:282",
            "/usr/wikia/slot1/7550/src/extensions/wikia/VideoHandlers/VideoFileUploader.class.php:93",
            "/usr/wikia/slot1/7550/src/extensions/wikia/VideoHandlers/VideoFileUploader.class.php:548",
            "/usr/wikia/slot1/7550/src/includes/wikia/services/VideoService.class.php:94",
            "/usr/wikia/slot1/7550/src/includes/wikia/services/VideoService.class.php:58",
            "/usr/wikia/slot1/7550/src/extensions/wikia/VideoHandlers/VideosController.class.php:29",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaDispatcher.class.php:205",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaApp.class.php:638",
            "/usr/wikia/slot1/7550/src/wikia.php:48"
        ]}) == '/extensions/wikia/VideoHandlers/VideoFileUploader.class.php:332'

        assert PHPLogsSource._get_wikia_caller_from_exception({'trace': [
            "/usr/wikia/slot1/7550/src/extensions/wikia/Security/classes/CSRFDetector.class.php:81",
            "{\"function\":\"onUserSaveSettings\",\"class\":\"Wikia\\\\Security\\\\CSRFDetector\",\"type\":\"::\"}",
            "/usr/wikia/slot1/7550/src/includes/Hooks.php:216",
            "/usr/wikia/slot1/7550/src/includes/GlobalFunctions.php:4045",
            "/usr/wikia/slot1/7550/src/includes/User.php:3567",
            "/usr/wikia/slot1/7550/src/includes/wikia/services/UserService.class.php:71",
            "/usr/wikia/slot1/7550/src/extensions/wikia/FacebookClient/FacebookClientController.class.php:156",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaDispatcher.class.php:205",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaApp.class.php:638",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaDispatchableObject.class.php:95",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaDispatchableObject.class.php:109",
            "/usr/wikia/slot1/7550/src/extensions/wikia/FacebookClient/FacebookClientController.class.php:101",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaDispatcher.class.php:205",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaApp.class.php:638",
            "/usr/wikia/slot1/7550/src/wikia.php:48"
        ]}) == '/extensions/wikia/FacebookClient/FacebookClientController.class.php:156'

        assert PHPLogsSource._get_wikia_caller_from_exception({'trace': [
            "/usr/wikia/slot1/7550/src/extensions/wikia/Security/classes/CSRFDetector.class.php:47",
            "{\"function\":\"foo\",\"class\":\"Wikia\\\\Security\\\\CSRFDetector\",\"type\":\"::\"}",
            "/usr/wikia/slot1/7550/src/includes/Hooks.php:216",
            "/usr/wikia/slot1/7550/src/includes/GlobalFunctions.php:4045",
            "/usr/wikia/slot1/7550/src/includes/Revision.php:1063",
            "/usr/wikia/slot1/7550/src/includes/WikiPage.php:1464",
            "/usr/wikia/slot1/7550/src/includes/filerepo/file/LocalFile.php:1149",
            "/usr/wikia/slot1/7550/src/includes/filerepo/file/LocalFile.php:950",
            "/usr/wikia/slot1/7550/src/extensions/VisualEditor/wikia/ApiAddMediaPermanent.php:40",
            "/usr/wikia/slot1/7550/src/extensions/VisualEditor/wikia/ApiAddMediaPermanent.php:14",
            "/usr/wikia/slot1/7550/src/includes/api/ApiMain.php:725",
            "/usr/wikia/slot1/7550/src/includes/api/ApiMain.php:362",
            "/usr/wikia/slot1/7550/src/includes/api/ApiMain.php:346",
            "/usr/wikia/slot1/7550/src/api.php:129"
        ]}) == '/extensions/VisualEditor/wikia/ApiAddMediaPermanent.php:40'

        assert PHPLogsSource._get_wikia_caller_from_exception({'trace': [
            "/usr/wikia/slot1/7550/src/extensions/wikia/Security/classes/CSRFDetector.class.php:69",
            "{\"function\":\"onUploadComplete\",\"class\":\"Wikia\\\\Security\\\\CSRFDetector\",\"type\":\"::\"}",
            "/usr/wikia/slot1/7550/src/includes/Hooks.php:216",
            "/usr/wikia/slot1/7550/src/includes/GlobalFunctions.php:4045",
            "/usr/wikia/slot1/7550/src/includes/upload/UploadBase.php:624",
            "/usr/wikia/slot1/7550/src/skins/oasis/modules/UploadPhotosController.class.php:76",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaDispatcher.class.php:205",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaApp.class.php:638",
            "/usr/wikia/slot1/7550/src/wikia.php:48"
        ]}) == '/skins/oasis/modules/UploadPhotosController.class.php:76'

        assert PHPLogsSource._get_wikia_caller_from_exception({'trace': [
            "/usr/wikia/slot1/7550/src/extensions/wikia/Security/classes/CSRFDetector.class.php:81",
            "{\"function\":\"onUserSaveSettings\",\"class\":\"Wikia\\\\Security\\\\CSRFDetector\",\"type\":\"::\"}",
            "/usr/wikia/slot1/7550/src/includes/Hooks.php:216",
            "/usr/wikia/slot1/7550/src/includes/GlobalFunctions.php:4045",
            "/usr/wikia/slot1/7550/src/includes/User.php:3567",
            "/usr/wikia/slot1/7550/src/includes/wikia/api/SendGridPostBackApiController.class.php:77",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaDispatcher.class.php:205",
            "/usr/wikia/slot1/7550/src/includes/wikia/nirvana/WikiaApp.class.php:638",
            "/usr/wikia/slot1/7550/src/wikia.php:48"
        ]}) == '/includes/wikia/api/SendGridPostBackApiController.class.php:77'
