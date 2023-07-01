import pytest
from typing import Iterator

from load import (
    filter_word_frequencies,
    generate_load_records,
)

from common.models import WordFrequencies, LoadRecord


def test_load_excluded_words_from_txt():
    pass


@pytest.mark.parametrize(
    "word_frequencies,min_word_length,min_frequency,excluded_words,expected_filtered_word_frequencies",
    [
        (
            WordFrequencies(frequencies={"a": 1, "b": 2, "ccc": 3, "ddd": 4}),
            1,
            1,
            {},
            WordFrequencies(frequencies={"a": 1, "b": 2, "ccc": 3, "ddd": 4}),
        ),
        (
            WordFrequencies(frequencies={"a": 1, "b": 2, "ccc": 3, "ddd": 4}),
            1,
            2,
            {},
            WordFrequencies(frequencies={"b": 2, "ccc": 3, "ddd": 4}),
        ),
        (
            WordFrequencies(frequencies={"a": 1, "b": 2, "ccc": 3, "ddd": 4}),
            3,
            1,
            {},
            WordFrequencies(frequencies={"ccc": 3, "ddd": 4}),
        ),
        (
            WordFrequencies(frequencies={"a": 1, "b": 2, "ccc": 3, "ddd": 4}),
            3,
            4,
            {},
            WordFrequencies(frequencies={"ddd": 4}),
        ),
        (
            WordFrequencies(frequencies={"a": 1, "b": 2, "ccc": 3, "ddd": 4}),
            1,
            2,
            {"ccc"},
            WordFrequencies(frequencies={"b": 2, "ddd": 4}),
        ),
    ],
)
def test_filter_word_frequencies(
    word_frequencies,
    min_word_length,
    min_frequency,
    excluded_words,
    expected_filtered_word_frequencies,
):
    from unittest.mock import patch

    with patch("load.excluded_words", excluded_words), patch("load.min_word_length", min_word_length), patch(
        "load.min_frequency",
        min_frequency,
    ):
        assert filter_word_frequencies(word_frequencies) == expected_filtered_word_frequencies


def test_generate_load_records(
    test_word_frequencies: WordFrequencies,
    test_timestamp_str: str,
    test_load_records: LoadRecord,
) -> None:
    load_records: Iterator[LoadRecord] = generate_load_records(test_word_frequencies, test_timestamp_str)
    assert list(load_records) == test_load_records
