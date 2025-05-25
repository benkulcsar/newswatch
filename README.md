# 🗞️Newswatch🗞️
[![python](https://img.shields.io/badge/python-3.12-blue?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![coverage](assets/img/coverage.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[newswatch.live](http://newswatch.live "newswatch.live")** - real-time word frequency visualisation for 🇬🇧 and 🇺🇸 news

# Summary

Newswatch collects data from leading UK and US news websites' front pages and creates visualisations to track word frequency changes over time, providing insights into current news trends and topics.

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

High-level architecture overview:

!["Architecture"](assets/img/architecture.png?v=4&s=200 "Architecture")

## Optimisation and Smoothing

To enhance dashboard performance, the data tables are partitioned by date, and Google's [BI Engine](https://cloud.google.com/bigquery/docs/bi-engine-intro) is used for faster query processing.

To reduce noise in the charts and present smoother trends, a moving average of word frequencies is calculated over the last 24 hours. This calculation runs hourly through a scheduled [query](terraform/bigquery_moving_avg.sql).

# Runbook

## Manually executing AWS lambda functions for backfilling

This requires AWS credentials.

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

## Execute and debug stages locally

Local execution requires AWS credentials and certain environment variables.

Each variable is required for specific stages of execution as noted below:

- TEST_S3_BUCKET_NAME: all
- SITES_YAML_PATH: extract
- TEST_S3_EXTRACT_KEY: extract, transform
- TEST_S3_TRANSFORM_KEY: transform, load
- MIN_WORD_LENGTH: load
- MIN_FREQUENCY: load
- EXCLUDED_WORDS_TXT_PATH: load

Specific stages can be executed by the following commands:

```shell
uv run ./src/newswatch/extract.py
uv run ./src/newswatch/transform.py
uv run ./src/newswatch/load.py
```

Note: When run locally, `load.py` does not connect to BigQuery.
