import pytest

from common.models import SiteHeadlines, SiteWordFrequencies, WordFrequencies
from transform import (
    count_words_in_text,
    get_site_word_frequencies_from_site_headlines,
    merge_site_word_frequencies,
)


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


# Indirectly testing count_words_in_text() too
def test_get_site_word_frequencies_from_site_headlines(
    test_site_headlines_collection: list[SiteHeadlines],
    test_site_word_frequencies_collection: list[SiteWordFrequencies],
) -> None:
    for site_headlines, site_word_frequencies in zip(
        test_site_headlines_collection,
        test_site_word_frequencies_collection,
    ):
        assert (
            get_site_word_frequencies_from_site_headlines(site_headlines) == site_word_frequencies
        ), f"Getting site word frequencies failed for site headlines: {site_headlines}"


def test_merge_site_word_frequencies(
    test_site_word_frequencies_collection: list[SiteWordFrequencies],
    test_word_frequencies: WordFrequencies,
) -> None:
    assert (
        merge_site_word_frequencies(test_site_word_frequencies_collection) == test_word_frequencies
    ), f"Merging site word frequencies failed for site word frequencies: {test_site_word_frequencies_collection}"
