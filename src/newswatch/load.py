"""
Load processed word frequency records into a BigQuery table.
"""

import os
import sys

from newswatch.common.models import WordFrequency
from newswatch.common.utils import (
    DeleteFailedError,
    convert_parquet_bytes_to_objects,
    delete_timestamp_from_bigquery,
    extract_s3_bucket_and_key_from_event,
    get_datetime_from_s3_key,
    get_from_s3,
    get_logger,
    insert_data_into_bigquery_table,
)


logger = get_logger()

DEFAULT_MIN_WORD_LENGTH = 3
DEFAULT_MIN_FREQUENCY = 500  # 0.5% multiplied by 10,000 for backwards compatibility


excluded_words_txt_path = os.environ.get("EXCLUDED_WORDS_TXT_PATH", "./resources/excluded-words.txt")

is_local = os.environ.get("AWS_EXECUTION_ENV") is None
is_pytest = "pytest" in sys.modules


def load_excluded_words(txt_path: str) -> set[str]:
    """Load excluded words that shouldn't be inserted to BigQuery."""
    with open(txt_path, "r") as file:
        return {line.strip() for line in file}


def filter_word_frequencies(
    flat_word_frequencies: list[WordFrequency],
    excluded_words: set[str],
) -> list[WordFrequency]:
    """
    Filter out words that are too short, in the exclusion list or below a frequency threshold.
    """

    min_word_length = int(os.environ.get("MIN_WORD_LENGTH", DEFAULT_MIN_WORD_LENGTH))
    min_frequency = int(os.environ.get("MIN_FREQUENCY", DEFAULT_MIN_FREQUENCY))

    def _keep_word_frequency(word: str, frequency: int) -> bool:
        """Return True if the word meets the length and frequency criteria."""
        if len(word) < min_word_length or word in excluded_words or frequency < min_frequency:
            return False
        return True

    return [fwf for fwf in flat_word_frequencies if _keep_word_frequency(fwf.word, fwf.frequency)]


def convert_filtered_word_frequencies_to_dict(word_frequencies: list[WordFrequency]) -> list[dict[str, int | str]]:
    """Convert a list of WordFrequency objects into a dictionary format with timestamps as strings."""

    return [
        {
            "word": wf.word,
            "frequency": wf.frequency,
            "timestamp": wf.timestamp.strftime("%Y-%m-%d %H:%M"),
        }
        for wf in word_frequencies
    ]


def load(bucket: str, word_frequencies_key: str) -> None:
    """Load word frequencies from S3 and insert them into BigQuery after applying filters."""

    logger.info(f"Loading word frequencies from {bucket}/{word_frequencies_key}")
    timestamp = get_datetime_from_s3_key(word_frequencies_key)
    word_frequency_bytes: bytes = get_from_s3(bucket_name=bucket, key=word_frequencies_key)
    word_frequencies: list[WordFrequency] = convert_parquet_bytes_to_objects(
        parquet_bytes=word_frequency_bytes,
        cls=WordFrequency,
    )
    excluded_words = load_excluded_words(excluded_words_txt_path) if excluded_words_txt_path else set()
    filtered_word_frequencies = filter_word_frequencies(word_frequencies, excluded_words)

    records_to_load_dicts = convert_filtered_word_frequencies_to_dict(filtered_word_frequencies)

    if is_local and not is_pytest:
        logger.warning("Local testing. Logging a sample of the records that would be loaded, but not loading them.")
        logger.warning(records_to_load_dicts[:5])
        return

    bigquery_table_id = os.environ.get("BIGQUERY_TABLE_ID", "")
    bigquery_delete_before_write = os.environ.get("BIGQUERY_DELETE_BEFORE_WRITE", "false").lower()

    if bigquery_delete_before_write == "true":
        logger.info(f"Attempting to delete: {timestamp} from {bigquery_table_id}")
        try:
            delete_timestamp_from_bigquery(table_id=bigquery_table_id, timestamp=timestamp)
        except DeleteFailedError as e:
            logger.error(f"Failed to delete {timestamp} from {bigquery_table_id}. Insert may not be idempotent.")
            logger.error(f"Reason: {e.errors}")
    else:
        logger.info(f"Skipping delete of {timestamp} from {bigquery_table_id}")

    insert_data_into_bigquery_table(table_id=bigquery_table_id, data=records_to_load_dicts)


# Lambda handler


def lambda_handler(event, context):
    bucket, key = extract_s3_bucket_and_key_from_event(event)
    load(bucket, key)


if is_local and not is_pytest and __name__ == "__main__":
    load(os.environ.get("TEST_S3_BUCKET_NAME", ""), os.environ.get("TEST_S3_TRANSFORM_KEY", ""))
