from datetime import datetime
import json
import boto3
from collections.abc import Iterable
from typing import Protocol, Any, Optional


class HasDict(Protocol):
    __dict__: dict


def coalesce_dict_values(dct: Optional[dict], to: Any) -> Optional[dict]:
    return {k: v or to for k, v in dct.items()} if dct is not None else None


def convert_objects_to_json_string(object_collection: Iterable[HasDict]) -> str:
    return json.dumps([obj.__dict__ for obj in object_collection], default=str)


def convert_json_string_to_objects(json_string: str, cls: type) -> list:
    return [cls(**obj) for obj in json.loads(json_string)]


def build_s3_key(prefix: str, timestamp: datetime, extension: str) -> str:
    return (
        f"{prefix}/year={timestamp.year}"
        f"/month={timestamp.month:02}"
        f"/day={timestamp.day:02}"
        f"/hour={timestamp.hour:02}.{extension}"
    )


def get_datetime_from_s3_key(s3_key: str) -> datetime:
    partitions_start = s3_key.find("year=")
    partitions_length = len("year=yyyy/month=mm/day=dd/hour=hh")
    partitions = s3_key[partitions_start : partitions_start + partitions_length]  # noqa
    print(partitions)
    return datetime.strptime(partitions, "year=%Y/month=%m/day=%d/hour=%H")


def sort_dict_by_value(dct: dict) -> dict:
    return dict(sorted(dct.items(), key=lambda item: item[1], reverse=True))


def upload_data_to_s3(bucket_name: str, key: str, data: str) -> dict:
    s3 = boto3.client("s3")
    return s3.put_object(Bucket=bucket_name, Key=key, Body=data)


def download_data_from_s3(bucket_name: str, key: str) -> str:
    s3 = boto3.client("s3")
    return s3.get_object(Bucket=bucket_name, Key=key)["Body"].read().decode("utf-8")
