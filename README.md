# 🗞️Newswatch🗞️
[![python](https://img.shields.io/badge/Python-3.10-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**[newswatch.live](http://newswatch.live "newswatch.live")** - real-time word frequency visualisation for 🇬🇧 and 🇺🇸 news

# Summary

Newswatch collects data from leading UK and US news websites' front pages and creates visualisations to track word frequency changes over time, offering insights into current news trends and topics.

## Line Chart

!["Line chart"](img/line_chart_september_2023.png?v=4&s=200 "Line chart")

## Treemap
!["Treemap"](img/treemap_september_2023.png?v=4&s=200 "Treemap")

## Historical data

Data is available from:
* `2020-06-05` in the UK 🇬🇧 and
* `2023-09-01` in the US 🇺🇸

### Line Chart - UK History
!["Historical"](img/line_chart_historical.png?v=4&s=200 "Historical")
# Architecture

High-level architecture diagram:

!["Architecture"](img/architecture.png?v=4&s=200 "Architecture")

# Runbook

## Manually running a lambda function

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
