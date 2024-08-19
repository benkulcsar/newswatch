import datetime
import json
import logging

import boto3
import moto
import pytest
from pyfakefs.fake_filesystem_unittest import Patcher as FSPatcher


from common.utils import (
    build_s3_key,
    call_and_catch_error_with_logging,
    coalesce_dict_values,
    convert_objects_to_json_string,
    download_from_s3,
    extract_s3_bucket_and_key_from_event,
    get_datetime_from_s3_key,
    get_from_s3,
    get_logger,
    get_s3_object_age_days,
    merge_dictionaries_summing_values,
    sort_dict_by_value,
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


@pytest.mark.parametrize(
    "source_dicts, expected_dict",
    [
        ([{"a": 1, "b": 2, "c": 3}, {"b": 10, "d": 20}], {"a": 1, "b": 12, "c": 3, "d": 20}),
        ([{"a": 0.1, "b": 0.2}, {"b": 10, "c": 20}], {"a": 0.1, "b": 10.2, "c": 20}),
    ],
)
def test_merge_dictionaries_summing_values(source_dicts, expected_dict):
    assert merge_dictionaries_summing_values(*source_dicts) == expected_dict


class MockObject:
    def __init__(self, attr1, attr2):
        self.attr1 = attr1
        self.attr2 = attr2

    def dummy_method(self):
        return "dummy"


@pytest.mark.parametrize(
    "object_collection, expected_json_string",
    [
        (
            [],
            "[]",
        ),
        (
            [MockObject("a", "b"), MockObject("c", "d")],
            '[{"attr1": "a", "attr2": "b"}, {"attr1": "c", "attr2": "d"}]',
        ),
    ],
)
def test_convert_objects_to_json_string(object_collection, expected_json_string):
    assert expected_json_string == convert_objects_to_json_string(object_collection)


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


def test_sort_dict_by_value():
    assert tuple(sort_dict_by_value({"a": 1, "b": 2})) == tuple({"b": 2, "a": 1})


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
    def div(a, b):
        return a / b

    logger = logging.getLogger()

    with caplog.at_level(logging.ERROR):
        assert call_and_catch_error_with_logging(div, logger, a=6, b=2) == 3
        assert "ERROR" not in caplog.text.upper()

        assert call_and_catch_error_with_logging(div, logger, a=5, b=0) is None
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
    s3_client.put_object(Bucket=test_bucket, Key=test_key, Body=test_data)

    assert get_from_s3(bucket_name=test_bucket, key=test_key) == test_data


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
