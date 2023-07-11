# 🗞️Newswatch🗞️
[![python](https://img.shields.io/badge/Python-3.10-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Visualising words frequencies in British newspaper headlines over time.

**[Link to the dashboard](http://newswatch.live "Looker Studio")**

# History

This repository serves as a more cost-effective replacement for the discontinued hobby project, [Firedruid](http://www.firedruid.com).

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
