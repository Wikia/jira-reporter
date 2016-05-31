Example response:

```json
{
    checksum: "3567184055139552756",
    snippet: "SELECT /* CategoryService::fetchTopArticlesInfo 10",
    index_ratio: "2.03",
    query_time_avg: "4.705532230234841",
    rows_sent_avg: "968110",
    ts_cnt: "1335",
    Query_time_sum: "6281.885527363513",
    Lock_time_sum: "0.07180099994002376",
    Rows_sent_sum: "1292426458",
    Rows_examined_sum: "2626120022",
    Query_time_median: "2.1164110083584653",
    sample: "SELECT /* CategoryService::fetchTopArticlesInfo 10.8.34.20 - 53e2e5fe-1fc5-4681-a34e-e1a545fde765 */ page_id,page_title,page_namespace FROM `page` INNER JOIN `categorylinks` ON ((cl_from = page_id)) WHERE cl_to = 'Dark_Monsters' AND page_namespace = '0'",
    hostname_max: "db-rg4",
    db_max: "yugioh",
    Fingerprint: "select page_id,page_title,page_namespace from `page` inner join `categorylinks` on ((cl_from = page_id)) where cl_to = ? and page_namespace = ?"
}
```