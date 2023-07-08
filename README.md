# 🗞️Newswatch🗞️

Visualising the most frequent words in British newspaper headlines over time.

**[Link to the dashboard](https://lookerstudio.google.com/reporting/cace127d-4866-4fcf-ae4c-a3f861e52a92 "Looker Studio")**

# History

This is a replacement of an old hobby project called Firedruid that became too expensive to maintain.

## Newswatch (new)

!["Line chart"](img/newswatch_lines.png?v=4&s=200 "Line chart")
!["Treemap"](img/newswatch_treemap.png?v=4&s=200 "Treemap")

## Firedruid (old)

!["Firedruid"](img/firedruid.png?v=4&s=200 "Firedruid")

## Historical data

Firedruid stored the scraped data in a local SQLite database file. This has been reprocessed and backfilled in the new dashboard from `2020-06-05`.

!["Backfill"](img/newswatch_backfill.png?v=4&s=200 "Backfill")
# Architecture

High-level architecture diagram:

!["Architecture"](img/architecture.png?v=4&s=200 "Architecture")

# Runbook

## Manually running a lambda function

`./src/scripts/run_lambda.sh <START DATE> <END DATE> <FUNCTION NAME> <S3 BUCKET> <S3 SOURCE PREFIX>`

Example:

```shell
./src/scripts/run_lambda.sh "2023-06-10" "2023-06-20" "newswatch-load-live" "s3-example-newswatch-live" "word-frequencies"
```

## Backfilling from local SQLite file

`./src/scripts/backfill_sqlite.sh <START DATE> <END DATE> <SQLITE PATH> <S3 BUCKET> <S3 PREFIX>`

Example:

```shell
./src/scripts/backfill_sqlite.sh "2020-06-05" "2020-08-31" "~/raw_data.db" "s3-example-newswatch-live" "headlines"
```
