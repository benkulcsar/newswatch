import datetime

import pytest
from pydantic import HttpUrl, TypeAdapter

from newswatch.common.models import Filter, Headline, Site, WordFrequency

url_adapter = TypeAdapter(HttpUrl)


@pytest.fixture
def test_sites() -> list[Site]:
    return [
        Site(
            name="site1",
            url=url_adapter.validate_python("https://www.site1.com"),
            filters=[Filter(tag="a", attrs={"href": "hey"})],
        ),
        Site(
            name="site2",
            url=url_adapter.validate_python("https://site2.com"),
            filters=[Filter(tag="x", attrs={"keyonly": None})],
        ),
        Site(
            name="site3",
            url=url_adapter.validate_python("https://site3.co.uk"),
            filters=[Filter(tag="p", attrs=None)],
        ),
        Site(
            name="site4",
            url=url_adapter.validate_python("https://site4.news"),
            filters=[
                Filter(tag="h2", attrs=None),
                Filter(tag="h3", attrs=None),
                Filter(tag="h4", attrs=None),
            ],
        ),
        Site(
            name="site5",
            url=url_adapter.validate_python("https://site5.co"),
            filters=[Filter(tag=None, attrs={"aaa": "AAA"}), Filter(tag=None, attrs={"bbb": "BBB"})],
        ),
        Site(
            name="site6",
            url=url_adapter.validate_python("https://www.site6.com"),
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
def test_site_headlines_collection() -> list[Headline]:
    headlines = ["abc", "xyz", "123"]
    return [
        Headline(
            site_name="abc",
            timestamp=datetime.datetime(2021, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            headline=headline,
        )
        for headline in headlines
    ] + [
        Headline(
            site_name="def",
            timestamp=datetime.datetime(2022, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            headline=headline,
        )
        for headline in headlines
    ]


@pytest.fixture
def test_timestamp() -> datetime.datetime:
    return datetime.datetime(2023, 6, 13, 21, 0, 0)


@pytest.fixture
def test_timestamp_str() -> str:
    return "2023-06-10 10:00:00+00:00"


@pytest.fixture
def test_load_records(test_timestamp) -> list[WordFrequency]:
    return [
        WordFrequency(
            timestamp=test_timestamp,
            word="abc",
            frequency=16666,
        ),
        WordFrequency(
            timestamp=test_timestamp,
            word="xyz",
            frequency=33333,
        ),
        WordFrequency(
            timestamp=test_timestamp,
            word="123",
            frequency=16666,
        ),
        WordFrequency(
            timestamp=test_timestamp,
            word="def",
            frequency=16666,
        ),
        WordFrequency(
            timestamp=test_timestamp,
            word="456",
            frequency=16666,
        ),
    ]
