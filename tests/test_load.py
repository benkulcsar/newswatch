import os
import tempfile
from datetime import datetime, timezone

import pytest

from newswatch.common.models import WordFrequency
from newswatch.load import (
    convert_filtered_word_frequencies_to_dict,
    filter_word_frequencies,
    load_excluded_words,
)

dummy_timestamp = datetime(2023, 6, 13, 21, 0, tzinfo=timezone.utc)
dummy_timestamp_str = "2023-06-13 21:00"


def test_load_excluded_words():
    words = ["abc", "123", "def456"]
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp_file:
        txt_path = tmp_file.name
        tmp_file.write("\n".join(words) + "\n")
    result = load_excluded_words(txt_path)
    assert result == set(words)
    os.remove(txt_path)


@pytest.mark.parametrize(
    "word_frequencies, min_word_length, min_frequency, excluded_words, expected_filtered",
    [
        # All words pass filtering
        (
            [
                WordFrequency(word="a", frequency=1, timestamp=dummy_timestamp),
                WordFrequency(word="bb", frequency=2, timestamp=dummy_timestamp),
                WordFrequency(word="ccc", frequency=3, timestamp=dummy_timestamp),
                WordFrequency(word="dddd", frequency=4, timestamp=dummy_timestamp),
            ],
            1,
            1,
            set(),
            [
                WordFrequency(word="a", frequency=1, timestamp=dummy_timestamp),
                WordFrequency(word="bb", frequency=2, timestamp=dummy_timestamp),
                WordFrequency(word="ccc", frequency=3, timestamp=dummy_timestamp),
                WordFrequency(word="dddd", frequency=4, timestamp=dummy_timestamp),
            ],
        ),
        # Filter based on min_frequency
        (
            [
                WordFrequency(word="a", frequency=1, timestamp=dummy_timestamp),
                WordFrequency(word="bb", frequency=2, timestamp=dummy_timestamp),
                WordFrequency(word="ccc", frequency=3, timestamp=dummy_timestamp),
                WordFrequency(word="dddd", frequency=4, timestamp=dummy_timestamp),
            ],
            1,
            2,
            set(),
            [
                WordFrequency(word="bb", frequency=2, timestamp=dummy_timestamp),
                WordFrequency(word="ccc", frequency=3, timestamp=dummy_timestamp),
                WordFrequency(word="dddd", frequency=4, timestamp=dummy_timestamp),
            ],
        ),
        # Filter based on min_word_length
        (
            [
                WordFrequency(word="a", frequency=1, timestamp=dummy_timestamp),
                WordFrequency(word="bb", frequency=2, timestamp=dummy_timestamp),
                WordFrequency(word="ccc", frequency=3, timestamp=dummy_timestamp),
                WordFrequency(word="dddd", frequency=4, timestamp=dummy_timestamp),
            ],
            3,
            1,
            set(),
            [
                WordFrequency(word="ccc", frequency=3, timestamp=dummy_timestamp),
                WordFrequency(word="dddd", frequency=4, timestamp=dummy_timestamp),
            ],
        ),
        # Filter by both criteria and excluded words
        (
            [
                WordFrequency(word="a", frequency=1, timestamp=dummy_timestamp),
                WordFrequency(word="bb", frequency=2, timestamp=dummy_timestamp),
                WordFrequency(word="ccc", frequency=3, timestamp=dummy_timestamp),
                WordFrequency(word="dddd", frequency=4, timestamp=dummy_timestamp),
            ],
            1,
            2,
            {"ccc"},
            [
                WordFrequency(word="bb", frequency=2, timestamp=dummy_timestamp),
                WordFrequency(word="dddd", frequency=4, timestamp=dummy_timestamp),
            ],
        ),
    ],
)
def test_filter_word_frequencies(
    word_frequencies,
    min_word_length,
    min_frequency,
    excluded_words,
    expected_filtered,
):
    mp = pytest.MonkeyPatch()
    mp.setenv("MIN_WORD_LENGTH", str(min_word_length))
    mp.setenv("MIN_FREQUENCY", str(min_frequency))

    filtered = filter_word_frequencies(word_frequencies, excluded_words)
    assert filtered == expected_filtered


def test_convert_filtered_word_frequencies_to_dict():
    flat_list = [
        WordFrequency(word="alpha", frequency=100, timestamp=dummy_timestamp),
        WordFrequency(word="beta", frequency=200, timestamp=dummy_timestamp),
    ]

    records: list[dict[str, int | str]] = convert_filtered_word_frequencies_to_dict(flat_list)
    records_list = list(records)
    expected = [
        {"word": "alpha", "timestamp": dummy_timestamp_str, "frequency": 100},
        {"word": "beta", "timestamp": dummy_timestamp_str, "frequency": 200},
    ]
    assert records_list == expected
