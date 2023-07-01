import json
from datetime import datetime, timezone
from unittest.mock import patch
from requests.models import Response

import moto
import boto3

from pydantic import HttpUrl
from pydantic.tools import parse_obj_as

from extract import lambda_handler as extract_lambda_handler
from transform import lambda_handler as transform_lambda_handler
from load import lambda_handler as load_lambda_handler

from common.models import Site, Filter


# Global variables normally set by environment variables at lambda cold start

log_level = "INFO"
s3_bucket_name = "test-bucket"
extract_s3_prefix = "extracted-headlines"
transform_s3_prefix = "word-frequencies"
bigquery_table = "nwproject.nwdataset.nwtable"
min_word_length = 3
min_frequency = 10_000
excluded_words = ["and", "the", "bobby"]


# Fixed timestamp for testing

timestamp = datetime(2023, 6, 13, 21, 0, 0, tzinfo=timezone.utc)
timestamp_str = "2023-06-13 21:00"
timestamp_partitions = "year=2023/month=06/day=13/hour=21"


# Object keys

expected_s3_object_key_after_extract = f"{extract_s3_prefix}/{timestamp_partitions}.json"
expected_s3_object_key_after_transform = f"{transform_s3_prefix}/{timestamp_partitions}.json"


# Object data

expected_s3_object_after_extract = [
    {
        "name": "site",
        "timestamp": "2023-06-13 21:00:00+00:00",
        "headlines": sorted(
            [
                "Go sports, go sports, go sports... SPORTS!!!",
                "Alice and Bob, Alice and Eve, Bob and Eve and Carol. The end.",
            ],
        ),
    },
]
expected_s3_object_after_transform = [
    {
        "frequencies": {
            "and": 20_000,
            "sport": 20_000,
            "go": 15_000,
            "alice": 10_000,
            "bob": 10_000,
            "eve": 10_000,
            "carol": 5_000,
            "the": 5_000,
            "end": 5_000,
        },
    },
]
expected_bigquery_dataset_after_load = [
    {"timestamp": timestamp_str, "word": "sport", "frequency": 20_000},
    {"timestamp": timestamp_str, "word": "alice", "frequency": 10_000},
    {"timestamp": timestamp_str, "word": "bob", "frequency": 10_000},
    {"timestamp": timestamp_str, "word": "eve", "frequency": 10_000},
]
expected_bigquery_delete_query = (
    f"DELETE FROM `{bigquery_table}` WHERE timestamp = '{timestamp.strftime('%Y-%m-%d %H:%M:%S')}'"
)


# Eventbridge triggers

trasform_trigger_event = {
    "detail-type": ["Object Created"],
    "source": ["aws.s3"],
    "detail": {"bucket": {"name": s3_bucket_name}, "object": {"key": expected_s3_object_key_after_extract}},
}
load_trigger_event = {
    "detail-type": ["Object Created"],
    "source": ["aws.s3"],
    "detail": {"bucket": {"name": s3_bucket_name}, "object": {"key": expected_s3_object_key_after_transform}},
}


# Extract mocks

site_from_yaml = Site(
    name="site",
    url=parse_obj_as(HttpUrl, "https://www.site.com"),
    filters=[Filter(tag="h2", attrs={"ping": "pong"})],
)
site_html = b"""
    <html><body>
    <h2 ping="pong">Alice and Bob, Alice and Eve, Bob and Eve and Carol. The end.</h2>
    <h2 ping="pong">Go sports, go sports, go sports... SPORTS!!!</h2>
    <h2 ping="notpong">Ignore this</h2>
    <div>Ignore thise one too<div>
    </body></html>
"""
requests_get_response = Response()
requests_get_response._content = site_html


# Load mocks


class _Result:
    def result(self):
        return None


class MockBigQueryClient:
    def __init__(self):
        self.inserted_rows = []
        self.queries_executed = []

    def insert_rows_json(self, table_id, data):
        self.inserted_rows += data

    def query(self, query):
        self.queries_executed.append(query)
        return _Result()


mock_bigquery_client = MockBigQueryClient()


# E2E test


@moto.mock_s3
@patch("requests.get", return_value=requests_get_response)
@patch("extract.load_sites_from_yaml", return_value=[site_from_yaml])
@patch("extract.s3_bucket_name", s3_bucket_name)
@patch("extract.extract_s3_prefix", extract_s3_prefix)
@patch("extract.get_current_timestamp", return_value=timestamp)
@patch("transform.transform_s3_prefix", transform_s3_prefix)
@patch("load.bigquery_table_id", bigquery_table)
@patch("load.min_word_length", min_word_length)
@patch("load.min_frequency", min_frequency)
@patch("load.excluded_words", excluded_words)
@patch("common.utils._get_get_bq_client", return_value=mock_bigquery_client)
def test_newswatch_e2e(*__args):
    # Setup

    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket=s3_bucket_name)

    # Extract

    extract_lambda_handler(event=None, context=None)
    object_after_extract = json.loads(
        s3_client.get_object(Bucket=s3_bucket_name, Key=expected_s3_object_key_after_extract)["Body"]
        .read()
        .decode("utf-8"),
    )
    assert object_after_extract == expected_s3_object_after_extract

    # Transform

    transform_lambda_handler(event=trasform_trigger_event, context=None)
    object_after_transform = json.loads(
        s3_client.get_object(Bucket=s3_bucket_name, Key=expected_s3_object_key_after_transform)["Body"]
        .read()
        .decode("utf-8"),
    )
    assert object_after_transform == expected_s3_object_after_transform

    # Load

    load_lambda_handler(event=load_trigger_event, context=None)
    assert mock_bigquery_client.inserted_rows == expected_bigquery_dataset_after_load
    assert expected_bigquery_delete_query in mock_bigquery_client.queries_executed
