import nltk
import os
import re
import json
import logging

from textblob import Word
from collections import Counter

from common.models import SiteHeadlineList

from common.utils import (
    get_datetime_from_s3_key,
    download_data_from_s3,
    convert_json_string_to_objects,
    sort_dict_by_value,
    build_s3_key,
    upload_data_to_s3,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def count_words_in_text(text: str) -> dict:
    title_words = re.sub(r"\W+", " ", text.lower())
    title_words_lemmatised = [Word(title_word).lemmatize() for title_word in title_words.split()]

    return dict(Counter(title_words_lemmatised))


def transform(bucket: str, site_headline_list_key: str):
    logger.info(f"Transforming headlines from {site_headline_list_key}")

    data = download_data_from_s3(bucket_name=bucket, key=site_headline_list_key)

    site_headline_lists = convert_json_string_to_objects(json_string=data, cls=SiteHeadlineList)
    all_headlines = [site_headline_list.headlines for site_headline_list in site_headline_lists]
    all_headlines_str = " ".join([item for s in all_headlines for item in s])

    word_counts = sort_dict_by_value(count_words_in_text(text=all_headlines_str))

    object_key = build_s3_key(
        prefix=transform_s3_prefix,
        timestamp=get_datetime_from_s3_key(site_headline_list_key),
        extension="json",
    )

    s3_response = upload_data_to_s3(
        bucket_name=bucket,
        key=object_key,
        data=json.dumps(word_counts),
    )

    if s3_response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        logger.info(f"Uploaded word counts to S3: {object_key}")


# Lambda cold start

s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "")
transform_s3_prefix = os.environ.get("TRANSFORM_S3_PREFIX", "")
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger(__name__)
logging.basicConfig(level=log_level)

nltk.data.path.append("/tmp")
nltk.download("wordnet", download_dir="/tmp")

# Lambda handler


def lambda_handler(event, context):
    bucket = event["detail"]["bucket"]["name"]
    key = event["detail"]["object"]["key"]
    if bucket != s3_bucket_name:
        logger.warning(f"Bucket name {bucket} does not match expected bucket name {s3_bucket_name}")
    transform(bucket, key)
