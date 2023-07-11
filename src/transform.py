import logging
import os
import re
from collections import Counter

import nltk
from textblob import Word

from common.models import SiteHeadlines, SiteWordFrequencies, WordFrequencies
from common.utils import (
    build_s3_key,
    convert_json_string_to_objects,
    convert_objects_to_json_string,
    download_data_from_s3,
    extract_s3_bucket_and_key_from_event,
    get_datetime_from_s3_key,
    merge_dictionaries_summing_values,
    sort_dict_by_value,
    upload_data_to_s3,
)


def count_words_in_text(text: str) -> dict:
    title_words = re.sub(r"\W+", " ", text.lower())
    title_words_lemmatised = [Word(title_word).lemmatize() for title_word in title_words.split()]

    return dict(Counter(title_words_lemmatised))


def get_site_word_frequencies_from_site_headlines(site_headlines: SiteHeadlines) -> SiteWordFrequencies:
    site_word_counts: dict[str, int] = count_words_in_text(" ".join(site_headlines.headlines))
    total_word_count: int = sum(site_word_counts.values())
    return SiteWordFrequencies(
        name=site_headlines.name,
        frequencies={word: count * 100_000 / total_word_count for word, count in site_word_counts.items()},
    )


def merge_site_word_frequencies(site_word_frequencies: list[SiteWordFrequencies]) -> WordFrequencies:
    site_count = len(site_word_frequencies)
    summed_frequencies = merge_dictionaries_summing_values(*[site.frequencies for site in site_word_frequencies])
    return WordFrequencies(
        frequencies=sort_dict_by_value({word: count / site_count for word, count in summed_frequencies.items()}),
    )


def transform(bucket: str, site_headline_list_key: str):
    logger.info(f"Transforming headlines from {bucket}/{site_headline_list_key}")

    json_data: str = download_data_from_s3(bucket_name=bucket, key=site_headline_list_key)
    site_headlines_list: list[SiteHeadlines] = convert_json_string_to_objects(json_string=json_data, cls=SiteHeadlines)
    site_word_frequencies: list[SiteWordFrequencies] = [
        get_site_word_frequencies_from_site_headlines(site_headlines) for site_headlines in site_headlines_list
    ]
    word_frequencies = merge_site_word_frequencies(site_word_frequencies)

    object_key = build_s3_key(
        prefix=transform_s3_prefix,
        timestamp=get_datetime_from_s3_key(site_headline_list_key),
        extension="json",
    )

    s3_response = upload_data_to_s3(
        bucket_name=bucket,
        key=object_key,
        data=convert_objects_to_json_string([word_frequencies]),
    )

    if s3_response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        logger.info(f"Uploaded word counts to S3: {bucket}/{object_key}")


# Lambda cold start


if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()

s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "")
transform_s3_prefix = os.environ.get("TRANSFORM_S3_PREFIX", "")

nltk.data.path.append("/tmp")
nltk.download("wordnet", download_dir="/tmp")


# Lambda handler


def lambda_handler(event, context):
    bucket, key = extract_s3_bucket_and_key_from_event(event)
    transform(bucket, key)
