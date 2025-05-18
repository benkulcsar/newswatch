"""
Transform raw headlines into structured word frequency records.
"""

import os
import re
import sys
from collections import Counter
from datetime import datetime

import nltk
from textblob import Word

from newswatch.common.models import Headline, WordFrequency
from newswatch.common.utils import (
    build_s3_key,
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

logger = get_logger()

is_local = os.environ.get("AWS_EXECUTION_ENV") is None
is_pytest = "pytest" in sys.modules

WRITABLE_PATH = "/tmp"


def get_wordnet_corpus(bucket: str) -> None:
    """Download or update the WordNet corpus from S3 if outdated."""

    wordnet_file_path = f"{WRITABLE_PATH}/corpora/wordnet.zip"
    wordnet_s3_key = "nltk/corpora/wordnet.zip"

    wordnet_age_days: int | None = get_s3_object_age_days(bucket=bucket, key=wordnet_s3_key)
    max_wordnet_age_days = 7

    if wordnet_age_days is None or wordnet_age_days > max_wordnet_age_days:
        nltk.download("wordnet", download_dir=WRITABLE_PATH)
        upload_to_s3(bucket=bucket, key=wordnet_s3_key, filename=f"{wordnet_file_path}")
    else:
        download_from_s3(bucket=bucket, key=wordnet_s3_key, filename=wordnet_file_path)

    nltk.data.path.append(WRITABLE_PATH)


def count_words_in_text(text: str) -> dict[str, int]:
    """Count lemmatised words in a given text."""

    def _clean_text(text: str) -> str:
        """Convert text to lowercase and replace non-word characters with spaces."""
        return re.sub(r"\W+", " ", text.lower())

    headline_words = _clean_text(text).split()
    lemmatised_headline_words = [Word(headline_word).lemmatize() for headline_word in headline_words]

    return dict(Counter(lemmatised_headline_words))


def group_headlines_by_site(headlines: list[Headline]) -> dict[str, list[Headline]]:
    """Group headlines by site name."""

    grouped_headlines: dict[str, list[Headline]] = {}
    for headline in headlines:
        grouped_headlines.setdefault(headline.site_name, []).append(headline)
    return grouped_headlines


def calculate_word_frequencies(text: str) -> dict[str, float]:
    """
    Calculate word frequencies in the given text.
    Note: multiplied by 100,000 for backward compatibility.
    """

    compatibility_multiplier = 100_000
    word_counts = count_words_in_text(text)
    total_count = sum(word_counts.values())
    return {word: count * compatibility_multiplier / total_count for word, count in word_counts.items()}


def calculate_word_frequencies_by_site(
    headlines_grouped_by_site,
    timestamp: datetime,
) -> dict[str, list[WordFrequency]]:
    """Compute word frequencies for each site."""

    word_frequencies_by_site: dict[str, list[WordFrequency]] = {}

    for name, headlines in headlines_grouped_by_site.items():
        combined_text = " ".join([headline.headline for headline in headlines])
        word_frequencies = calculate_word_frequencies(combined_text)
        word_frequencies_by_site[name] = []

        for word, freq in word_frequencies.items():
            word_frequencies_by_site[name].append(
                WordFrequency(
                    word=word,
                    frequency=int(freq),
                    timestamp=timestamp,
                ),
            )
    return word_frequencies_by_site


def filter_sites(
    site_word_frequencies: dict[str, list[WordFrequency]],
    word_count_threshold: int,
) -> dict[str, list[WordFrequency]]:
    """Return sites that have more than word_count_threshold words."""

    return {site: freqs for site, freqs in site_word_frequencies.items() if len(freqs) >= word_count_threshold}


def sum_frequencies(sites: dict[str, list[WordFrequency]]) -> Counter:
    """Aggregate word frequencies across all sites."""

    total_counter: Counter = Counter()
    for freqs in sites.values():
        total_counter.update({wf.word: wf.frequency for wf in freqs})
    return total_counter


def merge_site_word_frequencies(
    site_word_frequencies: dict[str, list[WordFrequency]],
    word_count_threshold: int = 0,
) -> list[WordFrequency]:
    """Merge word frequencies across sites and get the average of each word frequency."""

    filtered_sites = filter_sites(site_word_frequencies, word_count_threshold)
    site_count = len(filtered_sites)
    if site_count == 0:
        raise ValueError("No sites matched the filter criteria, cannot merge frequencies.")
    first_site_freqs = next(iter(filtered_sites.values()))
    timestamp = first_site_freqs[0].timestamp
    total_frequencies = sum_frequencies(filtered_sites)

    merged_frequencies = [
        WordFrequency(word=word, frequency=total / site_count, timestamp=timestamp)
        for word, total in total_frequencies.items()
    ]

    return sorted(merged_frequencies, key=lambda wf: wf.frequency, reverse=True)


def transform(bucket: str, site_headline_list_s3_key: str) -> None:
    """
    Transforms headline data into aggregated word frequency data.

    This process consists of:
    1. Calculating word frequencies for each site separately.
    2. Averaging the word frequencies across all sites to prevent sites with longer front pages
    from disproportionately influencing the results.

    The final transformed data is stored in S3 as a Parquet file.
    """
    get_wordnet_corpus(bucket)
    logger.info(f"Transforming headlines from {bucket}/{site_headline_list_s3_key}")
    headline_parquet_bytes: bytes = get_from_s3(bucket_name=bucket, key=site_headline_list_s3_key)
    headlines: list[Headline] = convert_parquet_bytes_to_objects(
        parquet_bytes=headline_parquet_bytes,
        cls=Headline,
    )

    headlines_grouped_by_site = group_headlines_by_site(headlines)

    # Each record must include a timestamp due to the flat data structure.
    # This redundancy is acceptable since the dataset is small enough to fit in memory
    # and is efficiently stored in Parquet format in S3.
    extraction_timestamp = get_datetime_from_s3_key(site_headline_list_s3_key)
    word_frequencies_by_site = calculate_word_frequencies_by_site(
        headlines_grouped_by_site=headlines_grouped_by_site,
        timestamp=extraction_timestamp,
    )

    word_count_threshold = int(os.environ.get("TRANSFORM_WORD_COUNT_THRESHOLD", "0"))
    word_frequencies = merge_site_word_frequencies(word_frequencies_by_site, word_count_threshold)
    data_bytes = convert_objects_to_parquet_bytes(word_frequencies)

    if (not is_local) or is_pytest:
        transform_s3_prefix = os.environ.get("TRANSFORM_S3_PREFIX", "")
        object_key = build_s3_key(
            prefix=transform_s3_prefix,
            timestamp=get_datetime_from_s3_key(site_headline_list_s3_key),
            extension="parquet",
        )
    else:
        bucket = os.environ.get("TEST_S3_BUCKET_NAME", bucket)
        object_key = os.environ.get("TEST_S3_TRANSFORM_KEY", "")

    s3_response = put_to_s3(
        bucket_name=bucket,
        key=object_key,
        data=data_bytes,
    )

    if s3_response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
        logger.info(f"Uploaded word counts to S3: {bucket}/{object_key}")


# Lambda handler


def lambda_handler(event, context):
    bucket, key = extract_s3_bucket_and_key_from_event(event)
    transform(bucket, key)


if is_local and not is_pytest and __name__ == "__main__":
    transform(os.environ.get("TEST_S3_BUCKET_NAME", ""), os.environ.get("TEST_S3_EXTRACT_KEY", ""))
