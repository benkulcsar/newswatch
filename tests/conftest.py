import datetime

import pytest
from pydantic import HttpUrl
from pydantic.tools import parse_obj_as

from common.models import (
    Filter,
    LoadRecord,
    Site,
    SiteHeadlines,
    SiteWordFrequencies,
    WordFrequencies,
)


@pytest.fixture
def test_sites() -> list[Site]:
    return [
        Site(
            name="site1",
            url=parse_obj_as(HttpUrl, "https://www.site1.com"),
            filters=[Filter(tag="a", attrs={"href": "hey"})],
        ),
        Site(
            name="site2",
            url=parse_obj_as(HttpUrl, "https://site2.com"),
            filters=[Filter(tag="x", attrs={"keyonly": None})],
        ),
        Site(
            name="site3",
            url=parse_obj_as(HttpUrl, "https://site3.co.uk"),
            filters=[Filter(tag="p", attrs=None)],
        ),
        Site(
            name="site4",
            url=parse_obj_as(HttpUrl, "https://site4.news"),
            filters=[
                Filter(tag="h2", attrs=None),
                Filter(tag="h3", attrs=None),
                Filter(tag="h4", attrs=None),
            ],
        ),
        Site(
            name="site5",
            url=parse_obj_as(HttpUrl, "https://site5.co"),
            filters=[Filter(tag=None, attrs={"aaa": "AAA"}), Filter(tag=None, attrs={"bbb": "BBB"})],
        ),
        Site(
            name="site6",
            url=parse_obj_as(HttpUrl, "https://www.site6.com"),
            filters=[Filter(tag="A", attrs={"B": "C"}), Filter(tag="XX", attrs={"YY": "ZZ"})],
        ),
    ]


@pytest.fixture
def test_headlines() -> dict[str, list[str]]:
    return {
        "site1": sorted(["abc", "xyz", "123"]),
        "site3": sorted(["More p tags", "Hey ho, let's go!"]),
        "site4": sorted(["yes", "YES"]),
    }


@pytest.fixture
def test_site_headlines_collection() -> list[SiteHeadlines]:
    return [
        SiteHeadlines(
            name="abc",
            timestamp=datetime.datetime(2021, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            headlines=["abc", "xyz", "123"],
        ),
        SiteHeadlines(
            name="def",
            timestamp=datetime.datetime(2022, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            headlines=["def", "xyz", "456"],
        ),
    ]


@pytest.fixture
def test_site_word_frequencies_collection() -> list[SiteWordFrequencies]:
    return [
        SiteWordFrequencies(
            name="abc",
            frequencies={"abc": 33333, "xyz": 33333, "123": 33333},
        ),
        SiteWordFrequencies(
            name="def",
            frequencies={"def": 33333, "xyz": 33333, "456": 33333},
        ),
    ]


@pytest.fixture
def test_word_frequencies() -> WordFrequencies:
    return WordFrequencies(
        frequencies={
            "abc": 16666,
            "xyz": 33333,
            "123": 16666,
            "def": 16666,
            "456": 16666,
        },
    )


@pytest.fixture
def test_timestamp_str() -> str:
    return "2023-06-10 10:00:00+00:00"


@pytest.fixture
def test_load_records(test_timestamp_str) -> list[LoadRecord]:
    return [
        LoadRecord(
            timestamp=test_timestamp_str,
            word="abc",
            frequency=16666,
        ),
        LoadRecord(
            timestamp=test_timestamp_str,
            word="xyz",
            frequency=33333,
        ),
        LoadRecord(
            timestamp=test_timestamp_str,
            word="123",
            frequency=16666,
        ),
        LoadRecord(
            timestamp=test_timestamp_str,
            word="def",
            frequency=16666,
        ),
        LoadRecord(
            timestamp=test_timestamp_str,
            word="456",
            frequency=16666,
        ),
    ]
