"""
Set of unit tests for IndexDigestSource
"""
import unittest

from ..sources import IndexDigestSource


class IndexDigestSourceTestClass(unittest.TestCase):
    """
    Unit tests for IndexDigestSource class
    """
    def setUp(self):
        self._source = IndexDigestSource()

    def test_normalize(self):
        assert self._source._normalize({
            'report': {
                'message': '"user_id" index can be removed as redundant (covered by "user_wiki_preference")',
                'table': 'local_preference',
                'type': 'redundant_indices',
            },
            'meta': {
                'database_name': 'user_preferences',
            }
        }) == 'index-digest-user_preferences-redundant_indices-local_preference-"user_id" ' \
              'index can be removed as redundant (covered by "user_wiki_preference")'

        assert self._source._normalize({
            'report': {
                'message': '"cu_log" has rows added 3726 days ago, consider changing retention policy',
                'table': 'local_preference',
                'type': 'redundant_indices',
            },
            'meta': {
                'database_name': 'user_preferences',
            }
        }) == 'index-digest-user_preferences-redundant_indices-local_preference-"cu_log" has rows added ' \
              'N days ago, consider changing retention policy'
