# 🗞️Newswatch🗞️
[![python](https://img.shields.io/badge/Python-3.10-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[newswatch.live](http://newswatch.live "newswatch.live")** - real-time word frequency visualisation for 🇬🇧 and 🇺🇸 news

# Summary

Newswatch collects data from leading UK and US news websites' front pages and creates visualisations to track word frequency changes over time, offering insights into current news trends and topics.

## Line Chart

!["Line chart"](img/line_chart_historical.png?v=4&s=200 "Line chart")

## Treemap
!["Treemap"](img/treemap_oct_2023.png?v=4&s=200 "Treemap")

## Historical data

Data is available from:
* `2020-06-05` in the UK 🇬🇧 and
* `2023-09-01` in the US 🇺🇸

# Architecture

High-level architecture diagram:

!["Architecture"](img/architecture.png?v=4&s=200 "Architecture")

## Bigquery and BI Engine

In order to make the dashboard faster, Google's [BI Engine](https://cloud.google.com/bigquery/docs/bi-engine-intro) is used. This requires some of the business logic to live in scheduled queries within Bigquery.

The following query is scheduled to run every hour to calculate the moving average of word frequencies and load the data into a new table with fewer partitions to enable BI Engine to work:
```sql
MERGE `xyz.word-frequencies-ma-live` ma
USING (
  SELECT
    timestamp,
    word,
    CAST(
        AVG(frequency)
        OVER (
            PARTITION BY word
            ORDER BY timestamp
            ROWS BETWEEN 24 PRECEDING AND CURRENT ROW
        ) AS INT
    ) AS frequency
  FROM `xyz.word-frequencies-partitioned-live`
  WHERE
    timestamp >
    TIMESTAMP_ADD(
        TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY),
        INTERVAL -2 DAY
    )
) raw
ON na.timestamp = raw.timestamp
WHEN NOT MATCHED THEN
  INSERT(timestamp, word, frequency)
  VALUES(timestamp, word, frequency)
```

# Runbook

## Manually executing lambda functions for backfilling

```shell
./src/scripts/run_lambda.sh <start-date> <end-date> <region> <function-name> <s3-bucket> <s3-prefix>
```

Examples:

```shell
./src/scripts/run_lambda.sh \
    "2023-06-10" \
    "2023-06-20" \
    "eu-west-1" \
    "newswatch-load-live-uk" \
    "s3-example-newswatch-live" \
    "word-frequencies"

./src/scripts/run_lambda.sh \
    "2023-09-01" \
    "2023-09-02" \
    "us-east-1" \
    "newswatch-load-live-us" \
    "s3-example-newswatch-live-us" \
    "word-frequencies"
```

## Execute and debug extractions locally

Local execution with debugging is only implemented for extraction because this is the only stage that can't be "backfilled", so bugs have to be fixed as soon as possible.

```shell
export SITES_YAML_PATH="src/resources/sites-with-filters-uk.yaml"
# or
export SITES_YAML_PATH="src/resources/sites-with-filters-us.yaml

python ./src/extract.py
```
