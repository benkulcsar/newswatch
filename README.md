# 🗞️Newswatch🗞️
[![python](https://img.shields.io/badge/Python-3.10-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Visualising words frequencies in 🇬🇧 and 🇺🇸 newspaper headlines over time.

**[Link to the dashboard](http://newswatch.live "Looker Studio")**

# Summary

Newswatch is a more cost-effective replacement for the discontinued hobby project, Firedruid.

## Line Chart

!["Line chart"](img/line_chart_september_2023.png?v=4&s=200 "Line chart")

## Treemap
!["Treemap"](img/treemap_september_2023.png?v=4&s=200 "Treemap")

## Historical data

Data is available:
* from `2020-06-05` in the UK 🇬🇧 and
* from `2023-09-01` in the US 🇺🇸

## Line Chart - UK History
!["Backfill"](img/line_chart_historical.png?v=4&s=200 "Backfill")
# Architecture

High-level architecture diagram:

!["Architecture"](img/architecture.png?v=4&s=200 "Architecture")

# Runbook

## Manually running a lambda function

`./src/scripts/run_lambda.sh <START DATE> <END DATE> <REGION> <FUNCTION NAME> <S3 BUCKET> <S3 SOURCE PREFIX>`

Examples:

```shell
./src/scripts/run_lambda.sh "2023-06-10" "2023-06-20" "eu-west-1" "newswatch-load-live-uk" "s3-example-newswatch-live" "word-frequencies"

./src/scripts/run_lambda.sh "2023-08-10" "2023-08-20" "us-east-1" "newswatch-load-live-us" "s3-example-newswatch-live-us" "word-frequencies"
```
