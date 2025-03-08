import io
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Protocol, Sequence

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from google.api_core.exceptions import BadRequest as GcpBadRequest
from google.cloud import bigquery
from google.oauth2 import service_account


class HasDict(Protocol):
    __dict__: dict


class DeleteFailedError(Exception):
    """Raised when a BigQuery delete operation fails."""

    def __init__(self, errors: str):
        self.errors = errors


def get_current_timestamp() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def coalesce_dict_values(dct: dict | None, to: Any) -> dict | None:
    """Replace None values in a dictionary with a given default."""
    return {k: v or to for k, v in dct.items()} if dct is not None else None


def convert_objects_to_parquet_bytes(object_collection: list) -> bytes:
    """Convert a list of objects to Parquet format and return as bytes."""

    data = [obj.dict() for obj in object_collection]
    table = pa.Table.from_pylist(data)
    sink = io.BytesIO()
    pq.write_table(table, sink, compression="gzip")
    return sink.getvalue()


def convert_parquet_bytes_to_objects(parquet_bytes: bytes, cls: type) -> list:
    """Convert Parquet bytes back into a list of objects of the given class."""

    sink = io.BytesIO(parquet_bytes)
    table = pq.read_table(sink)
    data = table.to_pylist()
    return [cls(**item) for item in data]


def build_s3_key(prefix: str, timestamp: datetime, extension: str) -> str:
    """
    Generate an S3 key using a timestamp-based folder structure.
    For example: sample_prefix/year=1999/month=01/day=05/hour=22.parquet
    """
    return f"{prefix}/{timestamp.strftime('year=%Y/month=%m/day=%d/hour=%H')}.{extension}"


def get_datetime_from_s3_key(s3_key: str) -> datetime:
    """Extract and parse a timestamp from an S3 key."""

    partitions_start = s3_key.find("year=")
    partitions_length = len("year=yyyy/month=mm/day=dd/hour=hh")
    partitions = s3_key[partitions_start : partitions_start + partitions_length]  # noqa
    return datetime.strptime(partitions, "year=%Y/month=%m/day=%d/hour=%H")


def extract_s3_bucket_and_key_from_event(event: dict) -> tuple[str, str]:
    """Extract the S3 bucket name and object key from an S3 notification event."""
    return event["detail"]["bucket"]["name"], event["detail"]["object"]["key"]


def put_to_s3(bucket_name: str, key: str, data: str) -> dict:
    """Upload data to an S3 bucket."""
    s3 = boto3.client("s3")
    return s3.put_object(Bucket=bucket_name, Key=key, Body=data)


def get_from_s3(bucket_name: str, key: str) -> bytes:
    """Retrieve data from an S3 object."""
    s3 = boto3.client("s3")
    return s3.get_object(Bucket=bucket_name, Key=key)["Body"].read()


def get_s3_object_age_days(bucket: str, key: str) -> int | None:
    """Return the age of an S3 object in days or None if it does not exist."""

    s3 = boto3.client("s3")
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
    except s3.exceptions.ClientError:
        return None
    file_upload_time = response["LastModified"].replace(tzinfo=None)
    return (datetime.now() - file_upload_time).days


def download_from_s3(bucket: str, key: str, filename: str) -> None:
    """Download a file from S3 and save it locally."""

    s3 = boto3.client("s3")
    path = os.path.dirname(filename)
    if not os.path.exists(path):
        os.makedirs(path)
    s3.download_file(Bucket=bucket, Key=key, Filename=filename)


def upload_to_s3(bucket: str, key: str, filename: str) -> None:
    """Upload a local file to S3."""

    s3 = boto3.client("s3")
    s3.upload_file(Filename=filename, Bucket=bucket, Key=key)


def _get_bq_client() -> bigquery.Client:
    """
    Return a BigQuery client using credentials stored in AWS SSM Paramter Store.
    Note: SSM is used instead of Secrets Manager to reduce the number of AWS services involved.
    """

    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name="NewsWatchBigQueryCredentials", WithDecryption=True)
    credentials_info = json.loads(response["Parameter"]["Value"], strict=False)
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    return bigquery.Client(credentials=credentials)


def delete_timestamp_from_bigquery(table_id: str, timestamp: datetime) -> bigquery.table.RowIterator:
    """Delete records from a BigQuery table with a given timestamp"""

    client = _get_bq_client()
    query_delete = f"DELETE FROM `{table_id}` WHERE timestamp = '{timestamp}'"
    try:
        return client.query(query_delete).result()
    except GcpBadRequest as e:
        raise DeleteFailedError(errors=e.errors)


def insert_data_into_bigquery_table(table_id: str, data: list[dict]) -> Sequence[dict]:
    """Insert multiple records into a BigQuery table."""

    client = _get_bq_client()
    return client.insert_rows_json(table_id, data)


def get_logger() -> logging.Logger:
    """Return a configured logger instance both locally and in AWS Lambda."""

    if logging.getLogger().hasHandlers():
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)
    return logging.getLogger()


def call_and_catch_error_with_logging(logger: logging.Logger):
    """
    Decorator that logs exceptions but allows execution to continue.
    This prevents a failure in one site's extraction from stopping the entire process.
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {func.__name__}: {e}"
                logger.error(error_msg)

        return wrapper

    return decorator
