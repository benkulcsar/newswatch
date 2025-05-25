from collections import Counter
from unittest.mock import ANY, patch

import pytest

from newswatch.common.models import Headline, WordFrequency
from newswatch.transform import (
    calculate_word_frequencies,
    calculate_word_frequencies_by_site,
    count_words_in_text,
    filter_sites,
    get_wordnet_corpus,
    group_headlines_by_site,
    merge_site_word_frequencies,
    sum_frequencies,
)


@patch("newswatch.transform.get_s3_object_age_days")
@patch("newswatch.transform.download_from_s3", return_value="downloaded from S3")
@patch("newswatch.transform.upload_to_s3", return_value="uploaded to S3")
@patch("nltk.download", return_value="downloaded from NLTK")
@patch("nltk.data.path")
def test_get_wordnet_corpus(mock_nltk_path, mock_download_nltk, mock_upload_s3, mock_download_s3, mock_age_days):
    test_bucket = "test_bucket"

    # Wordnet corpus is less than 7 days old, cached version from S3 should be used
    mock_age_days.return_value = 5
    get_wordnet_corpus(bucket=test_bucket)

    mock_age_days.assert_called_with(bucket=test_bucket, key=ANY)
    mock_download_s3.assert_called_with(bucket=test_bucket, key=ANY, filename=ANY)
    mock_upload_s3.assert_not_called()
    mock_download_nltk.assert_not_called()

    # Wordnet corpus is more than 7 days old, it should be downloaded from NLTK and cached in S3
    mock_age_days.return_value = 9
    get_wordnet_corpus(bucket=test_bucket)

    mock_upload_s3.assert_called_with(bucket=test_bucket, key=ANY, filename=ANY)
    mock_download_nltk.assert_called()


@pytest.mark.parametrize(
    "text,expected_word_counts",
    [
        (
            "This is a very very simple simple simple simple sentence.",
            {"this": 1, "is": 1, "a": 1, "very": 2, "simple": 4, "sentence": 1},
        ),
        (
            "\n Counter, counter, COUNTER,     counters, counters,    counters!",
            {"counter": 6},
        ),
        (
            "Me, Myself and I!!!",
            {"me": 1, "myself": 1, "and": 1, "i": 1},
        ),
        (
            "Go, go, go, go,... GO!",
            {"go": 5},
        ),
        (
            "2013 is gonna be super",
            {"2013": 1, "is": 1, "gonna": 1, "be": 1, "super": 1},
        ),
    ],
)
def test_count_words_in_text(text: str, expected_word_counts: dict) -> None:
    assert count_words_in_text(text) == expected_word_counts, f"Counting words failed for text: {text}"


def test_group_headlines_by_site(test_site_headlines_collection):
    grouped = group_headlines_by_site(test_site_headlines_collection)
    assert set(grouped.keys()) == {"abc", "def"}
    assert len(grouped["abc"]) == 3
    assert len(grouped["def"]) == 3


@pytest.mark.parametrize(
    "text, expected",
    [
        ("apple apple orange", {"apple": 100000 * 2 / 3, "orange": 100000 * 1 / 3}),
        ("banana banana banana", {"banana": 100000.0}),
    ],
)
def test_calculate_word_frequencies(text, expected):
    freqs = calculate_word_frequencies(text)
    for word, freq in expected.items():
        assert freqs[word] == pytest.approx(freq)


def test_calculate_word_frequencies_by_site(test_timestamp):
    headline1 = Headline(
        site_name="site1",
        timestamp=test_timestamp,
        headline="apple apple orange",
    )
    headline2 = Headline(
        site_name="site2",
        timestamp=test_timestamp,
        headline="banana banana",
    )
    grouped = {
        "site1": [headline1],
        "site2": [headline2],
    }

    result = calculate_word_frequencies_by_site(grouped, test_timestamp)

    site1_freqs = {wf.word: wf.frequency for wf in result["site1"]}
    site2_freqs = {wf.word: wf.frequency for wf in result["site2"]}

    assert site1_freqs.get("apple") == int(100000 * 2 / 3)
    assert site1_freqs.get("orange") == int(100000 * 1 / 3)
    assert site2_freqs.get("banana") == 100000
    for site_freqs in result.values():
        for wf in site_freqs:
            assert wf.timestamp == test_timestamp


def test_filter_sites(test_timestamp):
    wf_site1 = [
        WordFrequency(word="apple", frequency=100, timestamp=test_timestamp),
        WordFrequency(word="orange", frequency=50, timestamp=test_timestamp),
    ]
    wf_site2 = [
        WordFrequency(word="banana", frequency=200, timestamp=test_timestamp),
    ]
    site_word_freqs = {"site1": wf_site1, "site2": wf_site2}
    filtered = filter_sites(site_word_freqs, word_count_threshold=2)
    assert "site1" in filtered
    assert "site2" not in filtered


def test_sum_frequencies(test_timestamp):
    wf_site1 = [
        WordFrequency(word="apple", frequency=100, timestamp=test_timestamp),
        WordFrequency(word="orange", frequency=50, timestamp=test_timestamp),
    ]
    wf_site2 = [
        WordFrequency(word="apple", frequency=200, timestamp=test_timestamp),
    ]
    site_word_freqs = {"site1": wf_site1, "site2": wf_site2}
    total = sum_frequencies(site_word_freqs)
    expected = Counter({"apple": 300, "orange": 50})
    assert total == expected


def test_merge_site_word_frequencies(test_timestamp):
    site_word_freqs = {
        "site1": [
            WordFrequency(word="apple", frequency=100, timestamp=test_timestamp),
            WordFrequency(word="orange", frequency=50, timestamp=test_timestamp),
        ],
        "site2": [
            WordFrequency(word="apple", frequency=200, timestamp=test_timestamp),
            WordFrequency(word="orange", frequency=100, timestamp=test_timestamp),
        ],
        "site3": [
            WordFrequency(word="banana", frequency=300, timestamp=test_timestamp),
        ],
    }

    merged_thresh = merge_site_word_frequencies(site_word_freqs, word_count_threshold=2)
    merged_thresh_dict = {wf.word: wf.frequency for wf in merged_thresh}
    assert merged_thresh_dict["apple"] == 150
    assert merged_thresh_dict["orange"] == 75
    assert "banana" not in merged_thresh_dict
