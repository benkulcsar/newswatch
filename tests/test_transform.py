import pytest

from transform import count_words_in_text


@pytest.mark.parametrize(
    "text,expected_word_count",
    [
        (
            "This is a simple sentence.",
            {"this": 1, "is": 1, "a": 1, "simple": 1, "sentence": 1},
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
def test_count_words_in_text(text: str, expected_word_count: dict):
    assert count_words_in_text(text) == expected_word_count
