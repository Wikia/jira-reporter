"""
Set of unit tests for helper functions
"""
import unittest

from ..helpers import is_main_dc_host, generalize_sql


class UtilsTestClass(unittest.TestCase):
    @staticmethod
    def test_is_main_dc_host():
        assert is_main_dc_host('ap-s32')
        assert is_main_dc_host('task-s2')
        assert is_main_dc_host('cron-s5')
        assert is_main_dc_host('staging-s3')

        assert is_main_dc_host('ap-r32') is False
        assert is_main_dc_host('dev-foo') is False

    def test_generalize_sql(self):
        assert generalize_sql(None) is None

        assert generalize_sql("UPDATE  `category` SET cat_pages = cat_pages + 1,cat_files = cat_files + 1 WHERE cat_title = 'foo'") ==\
            "UPDATE `category` SET cat_pages = cat_pages + N,cat_files = cat_files + N WHERE cat_title = X"

        assert generalize_sql("SELECT  entity_key  FROM `wall_notification_queue`  WHERE (wiki_id = ) AND (event_date > '20150105141012')") ==\
            "SELECT entity_key FROM `wall_notification_queue` WHERE (wiki_id = ) AND (event_date > X)"

        assert generalize_sql("UPDATE  `user` SET user_touched = '20150112143631' WHERE user_id = '25239755'") ==\
            "UPDATE `user` SET user_touched = X"

        assert generalize_sql("SELECT /* CategoryDataService::getMostVisited 207.46.13.56 */  page_id,cl_to  FROM `page` INNER JOIN `categorylinks` ON ((cl_from = page_id))  WHERE cl_to = 'Characters' AND (page_namespace NOT IN(500,6,14))  ORDER BY page_title") ==\
            "SELECT page_id,cl_to FROM `page` INNER JOIN `categorylinks` ON ((cl_from = page_id)) WHERE cl_to = X AND (page_namespace NOT IN(N,N,N)) ORDER BY page_title"

        assert generalize_sql("delete /* DatabaseBase::sourceFile( /usr/wikia/slot1/3690/src/maintenance/cleanupStarter.sql ) CreateWiki scri... */ from text where old_id not in (select rev_text_id from revision)") ==\
            "delete from text where old_id not in (select rev_text_id from revision)"

        # multiline query
        sql = """
SELECT page_title
    FROM page
    WHERE page_namespace = '10'
    AND page_title COLLATE LATIN1_GENERAL_CI LIKE '%{{Cata%'
        """

        assert generalize_sql(sql) ==\
            "SELECT page_title FROM page WHERE page_namespace = X AND page_title COLLATE LATINN_GENERAL_CI LIKE X"
