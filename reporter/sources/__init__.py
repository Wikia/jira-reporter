"""
Various data providers

@see https://jira.atlassian.com/secure/WikiRendererHelpAction.jspa?section=all  JIRA text formatting
@see http://www.solrtutorial.com/solr-query-syntax.html                         Lucene query syntax
"""
from caching import NotCachedWikiaApiResponsesSource
from php import PHPErrorsSource, DBQueryErrorsSource, DBQueryNoLimitSource
from pt_kill import KilledDatabaseQueriesSource
