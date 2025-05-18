import datetime
import io
import json
import logging

import boto3
import moto
import pyarrow.parquet as pq
import pytest
from pyfakefs.fake_filesystem_unittest import Patcher as FSPatcher

from newswatch.common.utils import (
    build_s3_key,
    call_and_catch_error_with_logging,
    coalesce_dict_values,
    convert_objects_to_parquet_bytes,
    convert_parquet_bytes_to_objects,
    download_from_s3,
    extract_s3_bucket_and_key_from_event,
    get_datetime_from_s3_key,
    get_from_s3,
    get_logger,
    get_s3_object_age_days,
    put_to_s3,
    upload_to_s3,
)


@pytest.mark.parametrize(
    "source_dict, to, expected_dict",
    [
        (None, True, None),
        ({}, True, {}),
        ({"a": None}, True, {"a": True}),
        ({"a": None, "b": None}, True, {"a": True, "b": True}),
        ({"a": "A", "b": None}, False, {"a": "A", "b": False}),
    ],
)
def test_coalesce_dict_values(source_dict, to, expected_dict):
    assert coalesce_dict_values(source_dict, to) == expected_dict


class DummyObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def dict(self):
        return self.__dict__


@pytest.mark.parametrize(
    "data",
    [
        [],
        [{"attr1": "a", "attr2": "b"}, {"attr1": "c", "attr2": "d"}],
    ],
)
def test_convert_objects_to_parquet_bytes(data):
    objects = [DummyObject(**d) for d in data]
    parquet_bytes = convert_objects_to_parquet_bytes(objects)
    table = pq.read_table(io.BytesIO(parquet_bytes))
    result = table.to_pylist()
    assert result == data


@pytest.mark.parametrize(
    "data",
    [
        [],
        [{"attr1": "a", "attr2": "b"}, {"attr1": "c", "attr2": "d"}],
    ],
)
def test_convert_parquet_bytes_to_objects(data):
    objects = [DummyObject(**d) for d in data]
    parquet_bytes = convert_objects_to_parquet_bytes(objects)
    result_objects = convert_parquet_bytes_to_objects(parquet_bytes, DummyObject)
    assert [obj.__dict__ for obj in result_objects] == data


@pytest.mark.parametrize(
    "prefix, timestamp, extension, expected_object_key",
    [
        (
            "extracted-headlines",
            datetime.datetime(2021, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            "json",
            "extracted-headlines/year=2021/month=10/day=10/hour=10.json",
        ),
        (
            "nested/prefix/exotic-chars=+",
            datetime.datetime(2023, 3, 5, 7, 1, 2, tzinfo=datetime.timezone.utc),
            "tar.gz",
            "nested/prefix/exotic-chars=+/year=2023/month=03/day=05/hour=07.tar.gz",
        ),
    ],
)
def test_build_s3_key(prefix, timestamp, extension, expected_object_key):
    assert expected_object_key == build_s3_key(prefix, timestamp, extension)


def test_get_datetime_from_s3_key():
    s3_key = "s3://some-prefix/more-prefix/year=2023/month=06/day=09/hour=00.json"
    assert get_datetime_from_s3_key(s3_key) == datetime.datetime(2023, 6, 9, 0, 0)


def test_extract_s3_bucket_and_key_from_event():
    test_event = json.loads(
        """
        {
            "detail-type": ["Object Created"],
            "source": ["aws.s3"],
            "detail": {"bucket": {"name": "test-bucket"}, "object": {"key": "prefix/test-key"}}
        }
    """,
    )
    expected_bucket, expected_key = "test-bucket", "prefix/test-key"
    assert extract_s3_bucket_and_key_from_event(test_event) == (expected_bucket, expected_key)


def test_call_and_catch_error_with_logging(caplog):
    logger = logging.getLogger()

    @call_and_catch_error_with_logging(logger)
    def div(a, b):
        return a / b

    with caplog.at_level(logging.ERROR):
        assert div(a=6, b=2) == 3
        assert "ERROR" not in caplog.text.upper()

        assert div(a=5, b=0) is None
        assert "ERROR" in caplog.text.upper()


def test_get_logger(caplog):
    logger = get_logger()
    assert caplog.text == ""

    logger.info("hey")
    assert all(word in caplog.text for word in ["INFO", "hey"])


# Testing S3 functions


@pytest.fixture(scope="function")
def s3_setup():
    with moto.mock_s3():
        test_bucket = "test-bucket"
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=test_bucket)
        yield s3_client, test_bucket


@pytest.fixture
def test_key():
    return "test-object-key"


@pytest.fixture
def test_data():
    return '{"test": "test"}'


@pytest.fixture
def test_file():
    return "a/b/test.txt"


def test_put_to_s3(s3_setup, test_key, test_data):
    s3_client, test_bucket = s3_setup
    response = put_to_s3(bucket_name=test_bucket, key=test_key, data=test_data)

    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    assert s3_client.get_object(Bucket=test_bucket, Key=test_key)["Body"].read().decode("utf-8") == test_data


def test_get_from_s3(s3_setup, test_key, test_data):
    s3_client, test_bucket = s3_setup
    binary_data = test_data.encode("utf-8")
    s3_client.put_object(Bucket=test_bucket, Key=test_key, Body=binary_data)
    result = get_from_s3(bucket_name=test_bucket, key=test_key)
    assert result == binary_data


def test_get_s3_object_age_days(s3_setup, test_key, test_data):
    s3_client, test_bucket = s3_setup
    s3_client.put_object(Bucket=test_bucket, Key=test_key, Body=test_data)

    assert get_s3_object_age_days(bucket=test_bucket, key=test_key) == 0


def test_download_from_s3(s3_setup, test_key, test_data, test_file):
    s3_client, test_bucket = s3_setup
    s3_client.put_object(Bucket=test_bucket, Key=test_key, Body=test_data)

    with FSPatcher() as patcher:
        download_from_s3(bucket=test_bucket, key=test_key, filename=test_file)
        assert patcher.fs.get_object(test_file).contents == test_data


def test_upload_to_s3(s3_setup, test_key, test_data, test_file):
    s3_client, test_bucket = s3_setup

    with FSPatcher() as patcher:
        patcher.fs.create_file(test_file, contents=test_data)
        upload_to_s3(bucket="test-bucket", key=test_key, filename=test_file)

    response = s3_client.get_object(Bucket=test_bucket, Key=test_key)

    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    assert s3_client.get_object(Bucket=test_bucket, Key=test_key)["Body"].read().decode("utf-8") == test_data
