"""
Various data providers
"""
import logging
from wikia.common.kibana import Kibana


class Source(object):
    """ An abstract class for data providers to inherit from """
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug('Init')

    def query(self, query):
        results = dict()

        # filter the entries
        entries = [entry for entry in self._get_entries(query) if self._filter(entry)]

        # and normalize them
        for entry in entries:
            normalized = self._normalize(entry)

            if normalized is not None:
                if normalized not in results:
                    results[normalized] = 0

                results[normalized] += 1
            else:
                # self._logger.info('Entry not normalized: {}'.format(entry))
                pass

        return results

    def _get_entries(self, query):
        raise Exception("This method needs to be overwritten in your class!")

    def _filter(self, entry):
        raise Exception("This method needs to be overwritten in your class!")

    def _normalize(self, entry):
        """
        Normalize given message by removing variables like server name
        to improve grouping of messages
        """
        raise Exception("This method needs to be overwritten in your class!")


class KibanaSource(Source):
    #LIMIT = 100000
    LIMIT = 7500

    """ Kibana/elasticsearch-powered data-provider"""
    def __init__(self, period):
        super(KibanaSource, self).__init__()
        self._kibana = Kibana(period=period)

    def _get_entries(self, query):
        return self._kibana.get_rows(query, limit=self.LIMIT)

    def _filter(self, entry):
        return True

    def _normalize(self, entry):
        """
        Normalize given message by removing variables like server name
        to improve grouping of messages
        """
        message = entry.get('@message')

        return message
