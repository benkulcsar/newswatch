import os
from typing import Iterator

from common.models import LoadRecord, WordFrequencies
from common.utils import (
    DeleteFailedError,
    convert_json_string_to_objects,
    delete_timestamp_from_bigquery,
    get_from_s3,
    get_logger,
    extract_s3_bucket_and_key_from_event,
    get_datetime_from_s3_key,
    insert_data_into_bigquery_table,
)


def load_excluded_words_from_txt(txt_path: str) -> set[str]:
    excluded_words = set()
    with open(txt_path, "r") as file:
        for line in file:
            excluded_words.add(line.strip())
    return excluded_words


def filter_word_frequencies(word_frequencies: WordFrequencies) -> WordFrequencies:
    def _keep_word_frequency(word: str, frequency: int) -> bool:
        if len(word) < min_word_length or word in excluded_words or frequency < min_frequency:
            return False
        return True

    return WordFrequencies(
        frequencies={
            word: frequency
            for word, frequency in word_frequencies.frequencies.items()
            if _keep_word_frequency(word, frequency)
        },
    )


def generate_load_records(word_frequencies: WordFrequencies, timestamp_str: str) -> Iterator[LoadRecord]:
    for word, frequency in word_frequencies.frequencies.items():
        yield LoadRecord(timestamp=timestamp_str, word=word, frequency=frequency)


def load(bucket: str, word_frequencies_key: str):
    logger.info(f"Loading word frequencies from {bucket}/{word_frequencies_key}")

    data: str = get_from_s3(bucket_name=bucket, key=word_frequencies_key)
    word_frequencies: WordFrequencies = convert_json_string_to_objects(json_string=f"{data}", cls=WordFrequencies)[0]
    filtered_word_frequencies: WordFrequencies = filter_word_frequencies(word_frequencies=word_frequencies)

    timestamp = get_datetime_from_s3_key(word_frequencies_key)
    records_to_load: list[LoadRecord] = list(
        generate_load_records(
            word_frequencies=filtered_word_frequencies,
            timestamp_str=timestamp.strftime("%Y-%m-%d %H:%M"),
        ),
    )

    records_to_load_dicts: list[dict] = [dict(lr) for lr in records_to_load]

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


# Lambda cold start


logger = get_logger()

bigquery_table_id = os.environ.get("BIGQUERY_TABLE_ID", "")
bigquery_delete_before_write = os.environ.get("BIGQUERY_DELETE_BEFORE_WRITE", "false").lower()
min_word_length = int(os.environ.get("MIN_WORD_LENGTH", "99"))
min_frequency = int(os.environ.get("MIN_FREQUENCY", "99999"))
excluded_words_txt_path = os.environ.get("EXCLUDED_WORDS_TXT_PATH", None)
excluded_words = load_excluded_words_from_txt(excluded_words_txt_path) if excluded_words_txt_path else set()


# Lambda handler


def lambda_handler(event, context):
    bucket, key = extract_s3_bucket_and_key_from_event(event)
    load(bucket, key)
