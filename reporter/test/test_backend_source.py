"""
Set of unit tests for BackendSource
"""
import unittest

from ..sources import BackendSource


class BackendSourceTestClass(unittest.TestCase):
    """
    Unit tests for BackendSource class
    """
    def setUp(self):
        self._source = BackendSource()

    def test_extract_error_and_sql(self):
        assert self._source.extract_error_and_sql('foo') == ('foo', None)
        assert self._source.extract_error_and_sql("DBD::mysql::db do failed: Duplicate entry '1608358-28599913-' for key 'PRIMARY' [for Statement \"INSERT INTO events_local_users ( all_groups, single_group, last_revision, editdate, wiki_id, user_is_blocked, user_id, user_is_closed, cnt_groups, edits ) VALUES ( 'bureaucrat;sysop', 'sysop', '239', '2017-11-30 08:06:03', '1608358', '0', '28599913', '0', '2', '155' )\"]") == \
               ("Duplicate entry '1608358-28599913-' for key 'PRIMARY'", "INSERT INTO events_local_users ( all_groups, single_group, last_revision, editdate, wiki_id, user_is_blocked, user_id, user_is_closed, cnt_groups, edits ) VALUES ( 'bureaucrat;sysop', 'sysop', '239', '2017-11-30 08:06:03', '1608358', '0', '28599913', '0', '2', '155' )")
        assert self._source.extract_error_and_sql("DBD::mysql::db do failed: Lock wait timeout exceeded; try restarting transaction [for Statement \"update city_list set city_last_timestamp = '2017-11-30 08:45:03' where city_id = '1656550' \"]") == \
               ("Lock wait timeout exceeded; try restarting transaction", "update city_list set city_last_timestamp = '2017-11-30 08:45:03' where city_id = '1656550'")

    def test_normalize(self):
        assert self._source._normalize({
            '@message': 'foo',
        }) == 'Backend-foo-n/a-n/a'

        assert self._source._normalize({
            '@message': "LB::error",
            '@fields': {
                'script_name': 'foo.pl'
            },
            '@context': {
                'error': "DBD::mysql::db do failed: Duplicate entry '1599131-4962-5643-0-2017-11-30 07:42:36' for key 'PRIMARY' [for Statement \"insert into stats.events (is_content,wiki_id,ip_bin,wiki_lang_id,total_words,event_type,user_id,rev_size,image_links,rev_timestamp,user_is_bot,is_redirect,video_links,log_id,rev_id,page_ns,media_type,wiki_cat_id,page_id) values( 'N', '1599131', INET6_ATON('202.156.158.220'), '75', '2', '1', '32760087', '16', '0', '2017-11-30 07:42:36', 'N', 'N', '0', '0', '5643', '1201', '0', '3', '4962') \"]"
            }
        }) == "Backend-LB::error-foo.pl-DBD::mysql::db do failed: Duplicate entry X for key X [for Statement X]"
