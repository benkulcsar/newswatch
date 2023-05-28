import datetime

import pytest
from common.models import Filter
from common.models import Site
from common.models import SiteHeadlineList
from pydantic import HttpUrl
from pydantic.tools import parse_obj_as


@pytest.fixture
def expected_sites():
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
def expected_headlines():
    return {
        "site1": set(["abc", "xyz", "123"]),
        "site3": set(["More p tags", "Hey ho, let's go!"]),
        "site4": set(["yes", "YES"]),
    }


@pytest.fixture
def site_headline_collections():
    return [
        SiteHeadlineList(
            name="abc",
            timestamp=datetime.datetime(2021, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            headlines=["abc", "xyz", "123"],
        ),
        SiteHeadlineList(
            name="def",
            timestamp=datetime.datetime(2022, 10, 10, 10, 10, 10, tzinfo=datetime.timezone.utc),
            headlines=["def", "zzz", "456"],
        ),
    ]


@pytest.fixture
def expected_json_string():
    return (
        """[{"name": "abc", "timestamp": "2021-10-10 10:10:10+00:00", "headlines": ["abc", "xyz", "123"]}, """
        """{"name": "def", "timestamp": "2022-10-10 10:10:10+00:00", "headlines": ["def", "zzz", "456"]}]"""
    )
