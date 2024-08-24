import os
import json
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
import logging
from typing import Any, Callable, Optional, Protocol, Sequence, Union

import boto3
from google.api_core.exceptions import BadRequest as GcpBadRequest
from google.cloud import bigquery
from google.oauth2 import service_account


class HasDict(Protocol):
    __dict__: dict


class DeleteFailedError(Exception):
    def __init__(self, errors: str):
        self.errors = errors


def get_current_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def coalesce_dict_values(dct: Optional[dict], to: Any) -> Optional[dict]:
    return {k: v or to for k, v in dct.items()} if dct is not None else None


def merge_dictionaries_summing_values(*dicts: dict[Any, Union[int, float]]) -> dict:
    return dict(sum((Counter(d) for d in dicts), Counter()))


def convert_objects_to_json_string(object_collection: Iterable[HasDict]) -> str:
    return json.dumps([obj.__dict__ for obj in object_collection], default=str)


def convert_json_string_to_objects(json_string: str, cls: type[HasDict]) -> list[HasDict]:
    return [cls(**obj) for obj in json.loads(json_string)]


def build_s3_key(prefix: str, timestamp: datetime, extension: str) -> str:
    return f"{prefix}/{timestamp.strftime('year=%Y/month=%m/day=%d/hour=%H')}.{extension}"


def get_datetime_from_s3_key(s3_key: str) -> datetime:
    partitions_start = s3_key.find("year=")
    partitions_length = len("year=yyyy/month=mm/day=dd/hour=hh")
    partitions = s3_key[partitions_start : partitions_start + partitions_length]  # noqa
    return datetime.strptime(partitions, "year=%Y/month=%m/day=%d/hour=%H")


def sort_dict_by_value(dct: dict) -> dict:
    return dict(sorted(dct.items(), key=lambda item: item[1], reverse=True))


def extract_s3_bucket_and_key_from_event(event: dict) -> tuple[str, str]:
    return event["detail"]["bucket"]["name"], event["detail"]["object"]["key"]


def put_to_s3(bucket_name: str, key: str, data: str) -> dict:
    s3 = boto3.client("s3")
    return s3.put_object(Bucket=bucket_name, Key=key, Body=data)


def get_from_s3(bucket_name: str, key: str) -> str:
    s3 = boto3.client("s3")
    return s3.get_object(Bucket=bucket_name, Key=key)["Body"].read().decode("utf-8")


def get_s3_object_age_days(bucket: str, key: str) -> int:
    s3 = boto3.client("s3")
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
    except s3.exceptions.ClientError:
        return -1
    file_upload_time = response["LastModified"].replace(tzinfo=None)
    return (datetime.now() - file_upload_time).days


def download_from_s3(bucket: str, key: str, filename: str) -> None:
    s3 = boto3.client("s3")
    path = os.path.dirname(filename)
    if not os.path.exists(path):
        os.makedirs(path)
    s3.download_file(Bucket=bucket, Key=key, Filename=filename)


def upload_to_s3(bucket: str, key: str, filename: str) -> None:
    s3 = boto3.client("s3")
    s3.upload_file(Filename=filename, Bucket=bucket, Key=key)


def _get_bq_client() -> bigquery.Client:
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name="NewsWatchBigQueryCredentials", WithDecryption=True)
    credentials_info = json.loads(response["Parameter"]["Value"], strict=False)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    return bigquery.Client(credentials=credentials)


def delete_timestamp_from_bigquery(table_id: str, timestamp: datetime) -> bigquery.table.RowIterator:
    client = _get_bq_client()
    query_delete = f"DELETE FROM `{table_id}` WHERE timestamp = '{timestamp}'"
    try:
        return client.query(query_delete).result()
    except GcpBadRequest as e:
        raise DeleteFailedError(errors=e.errors)


def insert_data_into_bigquery_table(table_id: str, data: list[dict]) -> Sequence[dict]:
    client = _get_bq_client()
    return client.insert_rows_json(table_id, data)


def get_logger() -> logging.Logger:
    if logging.getLogger().hasHandlers():
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)

    return logging.getLogger()


def call_and_catch_error_with_logging(func: Callable, logger: logging.Logger, **kwargs) -> Any:
    try:
        return func(**kwargs)
    except Exception as e:
        error_msg = f"Error in {func.__name__}: {e}"
        logger.error(error_msg)
