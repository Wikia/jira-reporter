import logging
import requests

from  urllib import urlencode

from requests.exceptions import RequestException


class AnemometerClient(object):
    """
    Fetch and parse JSON from Anemometer instance
    """

    # default set of fields to be returned
    FIELDS = [
        'checksum',
        'snippet',
        'index_ratio',
        'query_time_avg',
        'rows_sent_avg',
        'ts_cnt',
        'Query_time_sum',
        'Lock_time_sum',
        'Rows_sent_sum',
        'Rows_examined_sum',
        'Rows_examined_median',
        'Query_time_median',
        'Query_time_median',
        'dimension.sample',
        'hostname_max',
        'db_max',
        'Fingerprint',
    ]

    def __init__(self, root_url):
        self._http = None
        self._logger = logging.getLogger(self.__class__.__name__)
        self._root_url = root_url

    @property
    def http(self):
        if self._http is None:
            self._http = requests.session()

        return self._http

    def _get_full_url(self, params):
        encoded_params = urlencode(params, doseq=True)

        return '{}/index.php?{}'.format(self._root_url, encoded_params)

    def get_queries(self, fields=None, order=None, limit=None, group=None):
        # apply default values
        fields = fields or self.FIELDS
        order = order or 'Query_time_sum DESC'
        limit = limit or 50
        group = group or 'checksum'

        # format the URL
        url = self._get_full_url(params={
            'action': 'api',
            'output': 'json',
            'datasource': 'localhost',
            'fact-group': group,
            'fact-order': order,
            'fact-limit': limit,
            'table_fields[]': fields
        })

        self._logger.info('Fetching <{}>'.format(url))

        try:
            resp = self.http.get(url).json()
            queries = resp.get('result', [])

            self._logger.info('Got {} queries'.format(len(queries)))
            return queries
        except RequestException as e:
            self._logger.error('HTTP request failed', exc_info=True)
            raise e
