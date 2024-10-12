# 🗞️Newswatch🗞️
[![python](https://img.shields.io/badge/python-3.12-blue?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[newswatch.live](http://newswatch.live "newswatch.live")** - real-time word frequency visualisation for 🇬🇧 and 🇺🇸 news

# Summary

Newswatch collects data from leading UK and US news websites' front pages and creates visualisations to track word frequency changes over time, offering insights into current news trends and topics.

## Line Chart

!["Line chart"](assets/img/uk_time_series_selected_words_20200601_20241012.png?v=4&s=200 "Line chart")
[raw data in csv](assets/data/uk_time_series_selected_words_20200601_20241012.csv)

## Treemap

!["Treemap"](assets/img/treemap_all_words_20230601_20241012.png?v=4&s=200 "Treemap")
[raw data in csv](assets/data/treemap_all_words_20230601_20241012.csv)

## Historical data

Data is available from:
* `2020-06-05` in the UK 🇬🇧 and
* `2023-09-01` in the US 🇺🇸

# Architecture

High-level architecture diagram:

!["Architecture"](assets/img/architecture.png?v=4&s=200 "Architecture")

## Optimisation and Smoothing

To enhance dashboard performance, the data tables are partitioned by date, and Google's [BI Engine](https://cloud.google.com/bigquery/docs/bi-engine-intro) is used for faster query processing.

To reduce noise in the charts and present smoother trends, a moving average of word frequencies is calculated. This calculation runs hourly through a scheduled [query](terraform/bigquery_moving_avg.sql).

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
