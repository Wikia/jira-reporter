"""
Set of unit tests for helper functions
"""
import unittest

from ..helpers import is_production_host, generalize_sql, get_method_from_query


class UtilsTestClass(unittest.TestCase):
    @staticmethod
    def test_is_main_dc_host():
        assert is_production_host('ap-s32')
        assert is_production_host('task-s2')
        assert is_production_host('cron-s5')
        assert is_production_host('staging-s3')

        assert is_production_host('ap-r32')
        assert is_production_host('dev-foo') is False

    def test_generalize_sql(self):
        assert generalize_sql(None) is None

        assert generalize_sql("UPDATE  `category` SET cat_pages = cat_pages + 1,cat_files = cat_files + 1 WHERE cat_title = 'foo'") ==\
            "UPDATE `category` SET cat_pages = cat_pages + N,cat_files = cat_files + N WHERE cat_title = X"

        assert generalize_sql("SELECT  entity_key  FROM `wall_notification_queue`  WHERE (wiki_id = ) AND (event_date > '20150105141012')") ==\
            "SELECT entity_key FROM `wall_notification_queue` WHERE (wiki_id = ) AND (event_date > X)"

        assert generalize_sql("UPDATE  `user` SET user_touched = '20150112143631' WHERE user_id = '25239755'") ==\
            "UPDATE `user` SET user_touched = X WHERE user_id = X"

        assert generalize_sql("SELECT /* CategoryDataService::getMostVisited 207.46.13.56 */  page_id,cl_to  FROM `page` INNER JOIN `categorylinks` ON ((cl_from = page_id))  WHERE cl_to = 'Characters' AND (page_namespace NOT IN(500,6,14))  ORDER BY page_title") ==\
            "SELECT page_id,cl_to FROM `page` INNER JOIN `categorylinks` ON ((cl_from = page_id)) WHERE cl_to = X AND (page_namespace NOT IN (XYZ)) ORDER BY page_title"

        assert generalize_sql("SELECT /* ArticleCommentList::getCommentList Dancin'NoViolen... */  page_id,page_title  FROM `page`  WHERE (page_title LIKE 'Dreams\_Come\_True/@comment-%' ) AND page_namespace = '1'  ORDER BY page_id DESC") ==\
            "SELECT page_id,page_title FROM `page` WHERE (page_title LIKE X ) AND page_namespace = X ORDER BY page_id DESC"

        assert generalize_sql("delete /* DatabaseBase::sourceFile( /usr/wikia/slot1/3690/src/maintenance/cleanupStarter.sql ) CreateWiki scri... */ from text where old_id not in (select rev_text_id from revision)") ==\
            "delete from text where old_id not in (select rev_text_id from revision)"

        assert generalize_sql("SELECT /* WallNotifications::getBackupData Craftindiedo */  id,is_read,is_reply,unique_id,entity_key,author_id,notifyeveryone  FROM `wall_notification`  WHERE user_id = '24944488' AND wiki_id = '1030786' AND unique_id IN ('880987','882618','708228','522330','662055','837815','792393','341504','600103','612640','667267','482428','600389','213400','620177','164442','659210','621286','609757','575865','567668','398132','549770','495396','344814','421448','400650','411028','341771','379461','332587','314176','284499','250207','231714')  AND is_hidden = '0'  ORDER BY id") ==\
            "SELECT id,is_read,is_reply,unique_id,entity_key,author_id,notifyeveryone FROM `wall_notification` WHERE user_id = X AND wiki_id = X AND unique_id IN (XYZ) AND is_hidden = X ORDER BY id"

        # comments with * inside
        assert generalize_sql("SELECT /* ArticleCommentList::getCommentList *Crashie* */  page_id,page_title  FROM `page`  WHERE (page_title LIKE 'Dainava/@comment-%' ) AND page_namespace = '1201'  ORDER BY page_id DESC") ==\
            "SELECT page_id,page_title FROM `page` WHERE (page_title LIKE X ) AND page_namespace = X ORDER BY page_id DESC"

        # multiline query
        sql = """
SELECT page_title
    FROM page
    WHERE page_namespace = '10'
    AND page_title COLLATE LATIN1_GENERAL_CI LIKE '%{{Cata%'
        """

        assert generalize_sql(sql) ==\
            "SELECT page_title FROM page WHERE page_namespace = X AND page_title COLLATE LATINN_GENERAL_CI LIKE X"

    def test_get_method_from_query(self):
        assert get_method_from_query("SELECT column from table where foo = 1") is None

        assert get_method_from_query("SELECT /*   Foo::Bar   */ column from table where foo = 1") == "Foo::Bar"
        assert get_method_from_query("SELECT /*Foo::Bar*/ column from table where foo = 1") == "Foo::Bar"
        assert get_method_from_query("SELECT /* Foo::Bar 157.55.39.174 */ column from table where foo = 1") == "Foo::Bar"

        assert get_method_from_query("SELECT /* WikiaApiQueryLastEditors::getEventsInfo  */  wiki_id,page_id,rev_id,log_id,user_id,user_is_bot,page_ns,is_content,is_redirect,ip,rev_timestamp,image_links,video_links,total_words,rev_size,wiki_lang_id,wiki_cat_id,event_type,event_date,media_type  FROM `events`  WHERE wiki_id = '5687' AND user_is_bot = 'N' AND is_content = 'Y' AND (user_id > 0)  ORDER BY rev_timestamp DESC LIMIT 25") == \
            "WikiaApiQueryLastEditors::getEventsInfo"
