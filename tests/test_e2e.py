import io
from datetime import datetime
from unittest.mock import patch
from typing import Any

import boto3
import moto
import pyarrow.parquet as pq
from pydantic import HttpUrl
from pydantic.tools import parse_obj_as
from requests.models import Response

from src.common.models import Filter, Site
from src.extract import lambda_handler as extract_lambda_handler
from src.load import lambda_handler as load_lambda_handler
from src.transform import lambda_handler as transform_lambda_handler

# Global variables normally set by environment variables at lambda cold start
s3_bucket_name = "test-bucket"
extract_s3_prefix = "extracted-headlines"
transform_s3_prefix = "word-frequencies"
transform_writable_path = "./tmp"
transform_word_count_threshold = 0
bigquery_table = "nwproject.nwdataset.nwtable"
bigquery_delete_before_write = "true"
min_word_length = 3
min_frequency = 10000
excluded_words = ["and", "the", "bobby"]

# Fixed timestamp for testing
timestamp = datetime(2023, 6, 13, 21, 0, 0)
timestamp_str = "2023-06-13 21:00"
timestamp_partitions = "year=2023/month=06/day=13/hour=21"

# Object keys
expected_s3_object_key_after_extract = f"{extract_s3_prefix}/{timestamp_partitions}.parquet"
expected_s3_object_key_after_transform = f"{transform_s3_prefix}/{timestamp_partitions}.parquet"

# Object data
expected_s3_object_after_extract = [
    {
        "site_name": "site",
        "timestamp": timestamp,
        "headline": "Alice and Bob, Alice and Eve, Bob and Eve and Carol. The end.",
    },
    {
        "site_name": "site",
        "timestamp": timestamp,
        "headline": "Go sports, go sports, go sports... SPORTS!!!",
    },
]

expected_s3_object_after_transform = [
    {"word": "alice", "frequency": 10000, "timestamp": timestamp},
    {"word": "and", "frequency": 20000, "timestamp": timestamp},
    {"word": "bob", "frequency": 10000, "timestamp": timestamp},
    {"word": "carol", "frequency": 5000, "timestamp": timestamp},
    {"word": "end", "frequency": 5000, "timestamp": timestamp},
    {"word": "eve", "frequency": 10000, "timestamp": timestamp},
    {"word": "go", "frequency": 15000, "timestamp": timestamp},
    {"word": "sport", "frequency": 20000, "timestamp": timestamp},
    {"word": "the", "frequency": 5000, "timestamp": timestamp},
]

expected_bigquery_dataset_after_load = [
    {"timestamp": timestamp_str, "word": "sport", "frequency": 20000},
    {"timestamp": timestamp_str, "word": "alice", "frequency": 10000},
    {"timestamp": timestamp_str, "word": "bob", "frequency": 10000},
    {"timestamp": timestamp_str, "word": "eve", "frequency": 10000},
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
    <div>Ignore this one too<div>
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
@patch("src.extract.load_sites_from_yaml", return_value=[site_from_yaml])
@patch("src.extract.s3_bucket_name", s3_bucket_name)
@patch("src.extract.extract_s3_prefix", extract_s3_prefix)
@patch("src.extract.get_current_timestamp", return_value=timestamp)
@patch("src.transform.transform_s3_prefix", transform_s3_prefix)
@patch("src.transform.writable_path", transform_writable_path)
@patch("src.transform.word_count_threshold", transform_word_count_threshold)
@patch("src.load.bigquery_table_id", bigquery_table)
@patch("src.load.bigquery_delete_before_write", bigquery_delete_before_write)
@patch("src.load.min_word_length", min_word_length)
@patch("src.load.min_frequency", min_frequency)
@patch("src.load.excluded_words", excluded_words)
@patch("common.utils._get_bq_client", return_value=mock_bigquery_client)
def test_newswatch_e2e(*__args):
    # Setup
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket=s3_bucket_name)

    # Extract
    extract_lambda_handler(event=None, context=None)
    s3_response = s3_client.get_object(Bucket=s3_bucket_name, Key=expected_s3_object_key_after_extract)
    parquet_bytes = s3_response["Body"].read()
    table = pq.read_table(io.BytesIO(parquet_bytes))
    object_after_extract = table.to_pylist()
    assert object_after_extract == expected_s3_object_after_extract

    # Transform (now flat format)
    transform_lambda_handler(event=trasform_trigger_event, context=None)
    s3_response = s3_client.get_object(Bucket=s3_bucket_name, Key=expected_s3_object_key_after_transform)
    parquet_bytes = s3_response["Body"].read()
    table = pq.read_table(io.BytesIO(parquet_bytes))
    object_after_transform: list[dict[str, Any]] = table.to_pylist()
    assert sorted(object_after_transform, key=lambda x: str(x["word"])) == sorted(
        expected_s3_object_after_transform,
        key=lambda x: str(x["word"]),
    )

    # Load
    load_lambda_handler(event=load_trigger_event, context=None)
    assert sorted(mock_bigquery_client.inserted_rows, key=lambda x: str(x["word"])) == sorted(
        expected_bigquery_dataset_after_load,
        key=lambda x: str(x["word"]),
    )
    assert expected_bigquery_delete_query in mock_bigquery_client.queries_executed
