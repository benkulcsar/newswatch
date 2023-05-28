from datetime import datetime
import json
import boto3
from collections.abc import Iterable
from typing import Protocol, Any, Optional


class HasDict(Protocol):
    __dict__: dict


def coalesce_dict_values(dct: Optional[dict], to: Any) -> Optional[dict]:
    return {k: v or to for k, v in dct.items()} if dct is not None else None


def convert_objects_to_json_string(
    object_collection: Iterable[HasDict],
) -> str:
    return json.dumps([obj.__dict__ for obj in object_collection], default=str)


def build_s3_key(prefix: str, timestamp: datetime, extension: str) -> str:
    return (
        f"{prefix}/year={timestamp.year}"
        f"/month={timestamp.month:02}"
        f"/day={timestamp.day:02}"
        f"/hour={timestamp.hour:02}.{extension}"
    )


def upload_data_to_s3(bucket_name: str, key: str, data: str) -> dict:
    s3 = boto3.client("s3")
    return s3.put_object(Bucket=bucket_name, Key=key, Body=data)
